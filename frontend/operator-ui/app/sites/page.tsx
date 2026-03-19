"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { useOperatorContext } from "../../components/useOperatorContext";
import { createAuditRun, createSite, fetchAuditRuns } from "../../lib/api/client";
import type { SEOAuditRun, SEOSite } from "../../lib/api/types";

interface DerivedSiteStatus {
  label: string;
  badgeClass: string;
}

function deriveSiteStatus(site: SEOSite, latestRun: SEOAuditRun | null): DerivedSiteStatus {
  if (!site.is_active) {
    return { label: "inactive", badgeClass: "badge badge-muted" };
  }
  if (!latestRun) {
    return { label: "not analyzed", badgeClass: "badge badge-muted" };
  }

  const status = latestRun.status.trim().toLowerCase();
  if (status === "queued" || status === "running") {
    return { label: "analysis in progress", badgeClass: "badge badge-warn" };
  }
  if (status === "completed") {
    return { label: "analysis complete", badgeClass: "badge badge-success" };
  }
  if (status === "failed") {
    return { label: "analysis failed", badgeClass: "badge badge-error" };
  }
  return { label: latestRun.status, badgeClass: "badge badge-muted" };
}

function parseBaseUrl(value: string): URL {
  let parsed: URL;
  try {
    parsed = new URL(value.trim());
  } catch {
    throw new Error("Base URL must be a valid absolute URL.");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("Base URL must start with http:// or https://.");
  }
  if (!parsed.hostname) {
    throw new Error("Base URL must include a valid domain.");
  }
  return parsed;
}

export default function SitesPage() {
  const context = useOperatorContext();
  const [displayName, setDisplayName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [latestRunsBySite, setLatestRunsBySite] = useState<Record<string, SEOAuditRun | null>>({});
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [triggeringSiteId, setTriggeringSiteId] = useState<string | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const loadLatestRuns = useCallback(
    async (sites: SEOSite[]): Promise<void> => {
      if (!context.token || !context.businessId) {
        return;
      }
      if (sites.length === 0) {
        setLatestRunsBySite({});
        setStatusError(null);
        return;
      }

      setStatusLoading(true);
      setStatusError(null);
      try {
        const entries = await Promise.all(
          sites.map(async (site) => {
            const response = await fetchAuditRuns(context.token, context.businessId, site.id);
            return [site.id, response.items[0] ?? null] as const;
          }),
        );
        setLatestRunsBySite(Object.fromEntries(entries));
      } catch (err) {
        setStatusError(err instanceof Error ? err.message : "Failed to load site status.");
      } finally {
        setStatusLoading(false);
      }
    },
    [context.businessId, context.token],
  );

  useEffect(() => {
    if (context.loading || context.error) {
      return;
    }
    void loadLatestRuns(context.sites);
  }, [context.error, context.loading, context.sites, loadLatestRuns]);

  const statuses = useMemo(() => {
    return context.sites.reduce<Record<string, DerivedSiteStatus>>((acc, site) => {
      acc[site.id] = deriveSiteStatus(site, latestRunsBySite[site.id] ?? null);
      return acc;
    }, {});
  }, [context.sites, latestRunsBySite]);

  const handleCreateSite = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitLoading(true);
    setSubmitError(null);
    setSubmitSuccess(null);
    setTriggerMessage(null);
    setTriggerError(null);

    try {
      const parsedBaseUrl = parseBaseUrl(baseUrl);
      const normalizedDisplayName = displayName.trim() || parsedBaseUrl.hostname;
      const created = await createSite(context.token, context.businessId, {
        display_name: normalizedDisplayName,
        base_url: parsedBaseUrl.toString(),
      });
      const updatedSites = await context.refreshSites();
      context.setSelectedSiteId(created.id);
      await loadLatestRuns(updatedSites);
      setDisplayName("");
      setBaseUrl("");
      setSubmitSuccess(`Created site ${created.display_name}.`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to create site.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleTriggerAudit = async (site: SEOSite) => {
    setTriggeringSiteId(site.id);
    setTriggerError(null);
    setTriggerMessage(null);
    setSubmitSuccess(null);

    try {
      const run = await createAuditRun(context.token, context.businessId, site.id, {
        max_pages: 25,
        max_depth: 2,
      });
      await loadLatestRuns(context.sites);
      setTriggerMessage(`Audit run ${run.id} finished with status ${run.status}.`);
    } catch (err) {
      setTriggerError(err instanceof Error ? err.message : "Failed to trigger site analysis.");
    } finally {
      setTriggeringSiteId(null);
    }
  };

  if (context.loading) {
    return <section className="panel">Loading sites...</section>;
  }
  if (context.error) {
    return <section className="panel">Error: {context.error}</section>;
  }

  return (
    <section className="panel stack">
      <h1>SEO Sites</h1>
      <p>Business: <code>{context.businessId}</code></p>

      <form onSubmit={(event) => void handleCreateSite(event)} className="stack">
        <h2>Add Site</h2>
        <label htmlFor="base-url">Base URL</label>
        <input
          id="base-url"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="https://example.com"
          required
        />
        <label htmlFor="display-name">Display Name (optional)</label>
        <input
          id="display-name"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Example Site"
        />
        <button className="primary" type="submit" disabled={submitLoading}>
          {submitLoading ? "Adding site..." : "Add Site"}
        </button>
      </form>

      {submitSuccess ? <p className="hint">{submitSuccess}</p> : null}
      {submitError ? <p className="hint error">{submitError}</p> : null}
      {statusLoading ? <p className="hint muted">Refreshing site status...</p> : null}
      {statusError ? <p className="hint warning">{statusError}</p> : null}
      {triggerMessage ? <p className="hint">{triggerMessage}</p> : null}
      {triggerError ? <p className="hint error">{triggerError}</p> : null}

      <table className="table">
        <thead>
          <tr>
            <th>Display Name</th>
            <th>Base URL</th>
            <th>Domain</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Primary</th>
            <th>Active</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {context.sites.map((site) => (
            <tr key={site.id}>
              <td>{site.display_name}</td>
              <td>{site.base_url}</td>
              <td>{site.normalized_domain}</td>
              <td>
                <span className={statuses[site.id]?.badgeClass || "badge badge-muted"}>
                  {statuses[site.id]?.label || "unknown"}
                </span>
              </td>
              <td>{latestRunsBySite[site.id]?.completed_at || latestRunsBySite[site.id]?.started_at || "none"}</td>
              <td>{site.is_primary ? "yes" : "no"}</td>
              <td>{site.is_active ? "yes" : "no"}</td>
              <td>
                <button
                  type="button"
                  disabled={
                    !!triggeringSiteId ||
                    !site.is_active ||
                    ["queued", "running"].includes((latestRunsBySite[site.id]?.status || "").toLowerCase())
                  }
                  onClick={() => {
                    void handleTriggerAudit(site);
                  }}
                >
                  {triggeringSiteId === site.id
                    ? "Running..."
                    : latestRunsBySite[site.id]
                      ? "Run Audit Again"
                      : "Run First Audit"}
                </button>
              </td>
            </tr>
          ))}
          {context.sites.length === 0 ? (
            <tr>
              <td colSpan={8}>No sites configured for this business.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}

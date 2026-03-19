"use client";

import { FormEvent, useMemo, useState } from "react";

import { useOperatorContext } from "../../components/useOperatorContext";
import { createAuditRun, createSite } from "../../lib/api/client";
import type { SEOSite } from "../../lib/api/types";

interface DerivedSiteStatus {
  label: string;
  badgeClass: string;
}

function deriveSiteStatus(site: SEOSite): DerivedSiteStatus {
  if (!site.is_active) {
    return { label: "inactive", badgeClass: "badge badge-muted" };
  }
  if (!site.last_audit_run_id) {
    return { label: "not analyzed", badgeClass: "badge badge-muted" };
  }

  const status = (site.last_audit_status || "").trim().toLowerCase();
  if (status === "completed") {
    return { label: "analysis complete", badgeClass: "badge badge-success" };
  }
  if (status === "failed") {
    return { label: "analysis failed", badgeClass: "badge badge-error" };
  }
  return { label: site.last_audit_status || "created", badgeClass: "badge badge-warn" };
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
  const [triggeringSiteId, setTriggeringSiteId] = useState<string | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const statuses = useMemo(() => {
    return context.sites.reduce<Record<string, DerivedSiteStatus>>((acc, site) => {
      acc[site.id] = deriveSiteStatus(site);
      return acc;
    }, {});
  }, [context.sites]);

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
      await context.refreshSites();
      context.setSelectedSiteId(created.id);
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
      await context.refreshSites();
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
      <p>
        Business: <code>{context.businessId}</code>
      </p>

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
      {triggerMessage ? <p className="hint">{triggerMessage}</p> : null}
      {triggerError ? <p className="hint error">{triggerError}</p> : null}

      <table className="table">
        <thead>
          <tr>
            <th>Display Name</th>
            <th>Base URL</th>
            <th>Domain</th>
            <th>Status</th>
            <th>Last Audit</th>
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
              <td>{site.last_audit_completed_at || "none"}</td>
              <td>{site.is_primary ? "yes" : "no"}</td>
              <td>{site.is_active ? "yes" : "no"}</td>
              <td>
                <button
                  type="button"
                  disabled={!!triggeringSiteId || !site.is_active}
                  onClick={() => {
                    void handleTriggerAudit(site);
                  }}
                >
                  {triggeringSiteId === site.id
                    ? "Running..."
                    : site.last_audit_run_id
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

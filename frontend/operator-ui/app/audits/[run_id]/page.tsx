"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useOperatorContext } from "../../../components/useOperatorContext";
import {
  ApiRequestError,
  fetchAuditRun,
  fetchAuditRunSummary,
  fetchRecommendations,
} from "../../../lib/api/client";
import type { Recommendation, SEOAuditRun, SEOAuditRunSummary } from "../../../lib/api/types";

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

function recommendationSource(item: Recommendation): string {
  if (item.audit_run_id && item.comparison_run_id) {
    return "mixed";
  }
  if (item.audit_run_id) {
    return "audit";
  }
  if (item.comparison_run_id) {
    return "comparison";
  }
  return "unknown";
}

function safeAuditDetailErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 401) {
      return "Session expired. Sign in again.";
    }
    if (error.status === 403) {
      return "You are not authorized to view this audit run.";
    }
    if (error.status === 404) {
      return "Audit run was not found in your tenant scope.";
    }
  }
  return "Unable to load audit run details right now. Please try again.";
}

export default function AuditRunDetailPage() {
  const params = useParams<{ run_id: string }>();
  const runId = (params?.run_id || "").trim();
  const context = useOperatorContext();

  const [run, setRun] = useState<SEOAuditRun | null>(null);
  const [summary, setSummary] = useState<SEOAuditRunSummary | null>(null);
  const [relatedRecommendations, setRelatedRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (context.loading || context.error || !runId) {
      setRun(null);
      setSummary(null);
      setRelatedRecommendations([]);
      setLoading(false);
      setError(null);
      setNotFound(false);
      return;
    }

    let cancelled = false;

    async function loadDetail() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      setRun(null);
      setSummary(null);
      setRelatedRecommendations([]);

      try {
        const runData = await fetchAuditRun(context.token, context.businessId, runId);
        if (cancelled) {
          return;
        }
        setRun(runData);

        const summaryPromise = fetchAuditRunSummary(context.token, context.businessId, runData.id).catch((err) => {
          if (err instanceof ApiRequestError && err.status === 404) {
            return null;
          }
          throw err;
        });
        const recommendationsPromise = fetchRecommendations(
          context.token,
          context.businessId,
          runData.site_id,
        ).catch((err) => {
          if (err instanceof ApiRequestError && err.status === 404) {
            return null;
          }
          throw err;
        });

        const [summaryData, recommendationsData] = await Promise.all([summaryPromise, recommendationsPromise]);
        if (cancelled) {
          return;
        }

        setSummary(summaryData);
        const related = (recommendationsData?.items || [])
          .filter((item) => item.audit_run_id === runData.id)
          .sort((a, b) => b.priority_score - a.priority_score);
        setRelatedRecommendations(related);
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiRequestError && err.status === 404) {
          setNotFound(true);
          return;
        }
        setError(safeAuditDetailErrorMessage(err));
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [context.businessId, context.error, context.loading, context.token, runId]);

  if (context.loading) {
    return <section className="panel">Loading audit run detail...</section>;
  }
  if (context.error) {
    return <section className="panel">Unable to load tenant context. Refresh and sign in again.</section>;
  }
  if (!runId) {
    return (
      <section className="panel stack">
        <h1>Audit Run Detail</h1>
        <p className="hint warning">Audit run identifier is missing.</p>
        <p>
          <Link href="/audits">Back to Audit Runs</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="stack">
      <div className="panel stack">
        <p>
          <Link href="/audits">Back to Audit Runs</Link>
        </p>
        <h1>Audit Run Detail</h1>
        <p>
          Audit Run: <code>{runId}</code>
        </p>

        {loading ? <p className="hint muted">Loading audit run detail...</p> : null}
        {!loading && notFound ? (
          <p className="hint warning">Audit run not found or not accessible in your tenant scope.</p>
        ) : null}
        {!loading && error ? <p className="hint error">{error}</p> : null}
      </div>

      {!loading && !notFound && !error && run ? (
        <>
          <div className="panel stack">
            <h2>Run Context</h2>
            <p>
              Business ID: <code>{run.business_id}</code>
            </p>
            <p>
              Site ID: <code>{run.site_id}</code>
            </p>
            <p>Status: {run.status}</p>
            <p>Created: {formatDateTime(run.created_at)}</p>
            <p>Started: {formatDateTime(run.started_at)}</p>
            <p>Completed: {formatDateTime(run.completed_at)}</p>
            <p>Error Summary: {run.error_summary || "-"}</p>
          </div>

          <div className="panel stack">
            <h2>Run Metrics</h2>
            <table className="table">
              <tbody>
                <tr>
                  <th>Configured Max Pages</th>
                  <td>{run.max_pages}</td>
                </tr>
                <tr>
                  <th>Configured Max Depth</th>
                  <td>{run.max_depth}</td>
                </tr>
                <tr>
                  <th>Pages Discovered</th>
                  <td>{run.pages_discovered}</td>
                </tr>
                <tr>
                  <th>Pages Crawled</th>
                  <td>{run.pages_crawled}</td>
                </tr>
                <tr>
                  <th>Pages Skipped</th>
                  <td>{run.pages_skipped}</td>
                </tr>
                <tr>
                  <th>Duplicate URLs Skipped</th>
                  <td>{run.duplicate_urls_skipped}</td>
                </tr>
                <tr>
                  <th>Errors Encountered</th>
                  <td>{run.errors_encountered}</td>
                </tr>
                <tr>
                  <th>Crawl Duration (ms)</th>
                  <td>{run.crawl_duration_ms ?? "-"}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="panel stack">
            <h2>Summary</h2>
            {summary ? (
              <table className="table">
                <tbody>
                  <tr>
                    <th>Total Findings</th>
                    <td>{summary.total_findings}</td>
                  </tr>
                  <tr>
                    <th>Critical Findings</th>
                    <td>{summary.critical_findings}</td>
                  </tr>
                  <tr>
                    <th>Warning Findings</th>
                    <td>{summary.warning_findings}</td>
                  </tr>
                  <tr>
                    <th>Info Findings</th>
                    <td>{summary.info_findings}</td>
                  </tr>
                  <tr>
                    <th>Health Score</th>
                    <td>{summary.health_score}</td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <p className="hint muted">No audit summary is available for this run.</p>
            )}
          </div>

          <div className="panel stack">
            <h2>Related Recommendations</h2>
            {relatedRecommendations.length === 0 ? (
              <p className="hint muted">No recommendations are currently linked to this audit run.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Category</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {relatedRecommendations.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link href={`/recommendations/${item.id}?site_id=${encodeURIComponent(item.site_id)}`}>
                          {item.title}
                        </Link>
                      </td>
                      <td>{item.status}</td>
                      <td>
                        {item.priority_score} ({item.priority_band})
                      </td>
                      <td>{item.category}</td>
                      <td>{recommendationSource(item)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}

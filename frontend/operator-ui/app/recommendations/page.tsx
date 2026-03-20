"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useOperatorContext } from "../../components/useOperatorContext";
import { ApiRequestError, fetchRecommendations } from "../../lib/api/client";
import type { Recommendation, RecommendationListFilters } from "../../lib/api/types";

type FilterState = {
  status: "" | NonNullable<RecommendationListFilters["status"]>;
  priorityBand: "" | NonNullable<RecommendationListFilters["priority_band"]>;
  category: "" | NonNullable<RecommendationListFilters["category"]>;
};

const DEFAULT_FILTERS: FilterState = {
  status: "",
  priorityBand: "",
  category: "",
};

const STATUS_FILTER_OPTIONS: Array<{ label: string; value: FilterState["status"] }> = [
  { label: "All statuses", value: "" },
  { label: "Open", value: "open" },
  { label: "In Progress", value: "in_progress" },
  { label: "Accepted", value: "accepted" },
  { label: "Dismissed", value: "dismissed" },
  { label: "Snoozed", value: "snoozed" },
  { label: "Resolved", value: "resolved" },
];

const PRIORITY_FILTER_OPTIONS: Array<{ label: string; value: FilterState["priorityBand"] }> = [
  { label: "All priorities", value: "" },
  { label: "Critical", value: "critical" },
  { label: "High", value: "high" },
  { label: "Medium", value: "medium" },
  { label: "Low", value: "low" },
];

const CATEGORY_FILTER_OPTIONS: Array<{ label: string; value: FilterState["category"] }> = [
  { label: "All categories", value: "" },
  { label: "SEO", value: "SEO" },
  { label: "Content", value: "CONTENT" },
  { label: "Structure", value: "STRUCTURE" },
  { label: "Technical", value: "TECHNICAL" },
];

function deriveSourceType(item: Recommendation): string {
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

function safeRecommendationsErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 401) {
      return "Session expired. Sign in again.";
    }
    if (error.status === 403) {
      return "You are not authorized to view recommendations.";
    }
    if (error.status === 404) {
      return "Recommendation data for the selected site was not found.";
    }
  }
  return "Unable to load recommendations right now. Please try again.";
}

export default function RecommendationsPage() {
  const router = useRouter();
  const context = useOperatorContext();
  const [items, setItems] = useState<Recommendation[]>([]);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [loadingItems, setLoadingItems] = useState(false);
  const [itemsError, setItemsError] = useState<string | null>(null);

  const hasActiveFilters = Boolean(filters.status || filters.priorityBand || filters.category);

  useEffect(() => {
    if (context.loading || context.error || !context.selectedSiteId) {
      setItems([]);
      setItemsError(null);
      setLoadingItems(false);
      return;
    }
    let cancelled = false;
    const selectedSiteId = context.selectedSiteId;

    async function loadRecommendations() {
      setLoadingItems(true);
      setItemsError(null);
      try {
        const activeFilters: RecommendationListFilters = {};
        if (filters.status) {
          activeFilters.status = filters.status;
        }
        if (filters.priorityBand) {
          activeFilters.priority_band = filters.priorityBand;
        }
        if (filters.category) {
          activeFilters.category = filters.category;
        }
        const response = await fetchRecommendations(context.token, context.businessId, selectedSiteId, activeFilters);
        if (!cancelled) {
          setItems(response.items);
        }
      } catch (err) {
        if (!cancelled) {
          setItemsError(safeRecommendationsErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setLoadingItems(false);
        }
      }
    }
    void loadRecommendations();
    return () => {
      cancelled = true;
    };
  }, [
    context.businessId,
    context.error,
    context.loading,
    context.selectedSiteId,
    context.token,
    filters.status,
    filters.priorityBand,
    filters.category,
  ]);

  if (context.loading) {
    return <section className="panel">Loading recommendations...</section>;
  }
  if (context.error) {
    return <section className="panel">Unable to load tenant context. Refresh and sign in again.</section>;
  }
  if (context.sites.length === 0) {
    return (
      <section className="panel stack">
        <h1>Recommendation Workflow</h1>
        <p className="hint muted">No SEO sites are configured yet. Add a site first to view recommendations.</p>
      </section>
    );
  }

  return (
    <section className="panel stack">
      <h1>Recommendation Workflow</h1>
      <label htmlFor="site-picker-recommendations">Site</label>
      <select
        id="site-picker-recommendations"
        value={context.selectedSiteId || ""}
        onChange={(event) => context.setSelectedSiteId(event.target.value)}
      >
        {context.sites.map((site) => (
          <option key={site.id} value={site.id}>
            {site.display_name}
          </option>
        ))}
      </select>

      <div
        className="stack"
        style={{
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          alignItems: "end",
        }}
      >
        <div className="stack" style={{ gap: "0.35rem" }}>
          <label htmlFor="recommendation-filter-status">Status</label>
          <select
            id="recommendation-filter-status"
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                status: event.target.value as FilterState["status"],
              }))
            }
          >
            {STATUS_FILTER_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="stack" style={{ gap: "0.35rem" }}>
          <label htmlFor="recommendation-filter-priority">Priority</label>
          <select
            id="recommendation-filter-priority"
            value={filters.priorityBand}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                priorityBand: event.target.value as FilterState["priorityBand"],
              }))
            }
          >
            {PRIORITY_FILTER_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="stack" style={{ gap: "0.35rem" }}>
          <label htmlFor="recommendation-filter-category">Category</label>
          <select
            id="recommendation-filter-category"
            value={filters.category}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                category: event.target.value as FilterState["category"],
              }))
            }
          >
            {CATEGORY_FILTER_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => setFilters(DEFAULT_FILTERS)}
          disabled={loadingItems || !hasActiveFilters}
        >
          Clear Filters
        </button>
      </div>

      {loadingItems ? <p className="hint muted">Loading recommendations...</p> : null}
      {itemsError ? <p className="hint error">{itemsError}</p> : null}

      <table className="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Summary</th>
            <th>Status</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Source</th>
            <th>Recommendation Run</th>
            <th>Business</th>
            <th>Site</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              role="link"
              tabIndex={0}
              style={{ cursor: "pointer" }}
              onClick={() => router.push(`/recommendations/${item.id}?site_id=${encodeURIComponent(item.site_id)}`)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  router.push(`/recommendations/${item.id}?site_id=${encodeURIComponent(item.site_id)}`);
                }
              }}
            >
              <td>{item.title}</td>
              <td>{item.rationale}</td>
              <td>{item.status}</td>
              <td>{item.category}</td>
              <td>
                {item.priority_score} ({item.priority_band})
              </td>
              <td>{deriveSourceType(item)}</td>
              <td>{item.recommendation_run_id}</td>
              <td>{item.business_id}</td>
              <td>{item.site_id}</td>
            </tr>
          ))}
          {items.length === 0 && !loadingItems ? (
            <tr>
              <td colSpan={9}>
                {hasActiveFilters
                  ? "No recommendations match the current filters."
                  : "No recommendations found for this site."}
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}

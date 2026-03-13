export type VisibilityMetricSource =
  | "gbp"
  | "gbp_performance"
  | "ga4"
  | "search_console"
  | "ai_visibility";

export type VisibilityMetric = {
  id: string;
  businessId: string;
  metricDate: string;
  source: VisibilityMetricSource;
  profileViews: number | null;
  mapViews: number | null;
  websiteClicks: number | null;
  phoneCalls: number | null;
  directionRequests: number | null;
  searchImpressions: number | null;
  searchClicks: number | null;
  avgPosition: number | null;
  aiAnswerMentions: number | null;
  aiAnswerSharePct: number | null;
  rawPayload: Record<string, unknown>;
  createdAt: string;
};

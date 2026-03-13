export type MarketingMetric = {
  id: string;
  businessId: string;
  metricPeriodStart: string;
  metricPeriodEnd: string;
  adSpend: number;
  leadsTotal: number;
  leadsMarketing: number;
  jobsWon: number;
  revenueFromJobs: number;
  avgJobValue: number | null;
  costPerLead: number | null;
  costPerJob: number | null;
  responseTimeMinutes: number | null;
  romiPct: number | null;
  rawPayload: Record<string, unknown>;
  createdAt: string;
};

import type { Env } from "../config/env.js";
import type { DashboardService } from "../services/dashboard.service.js";
import type { BusinessService } from "../services/business.service.js";
import type { LeadIntakeService } from "../services/lead-intake.service.js";
import type { SyncMetricsJob } from "../jobs/sync-metrics.job.js";

export type RouteDeps = {
  env: Env;
  businessService: BusinessService;
  leadService: LeadIntakeService;
  dashboardService: DashboardService;
  syncMetricsJob: SyncMetricsJob;
};

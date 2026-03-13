import Fastify from "fastify";
import { loadEnv } from "./config/env.js";
import { buildAdapters } from "./integrations/factory.js";
import { SyncMetricsJob } from "./jobs/sync-metrics.job.js";
import { registerBusinessRoutes } from "./routes/businesses.routes.js";
import { registerDashboardRoutes } from "./routes/dashboard.routes.js";
import { registerHealthRoutes } from "./routes/health.routes.js";
import { registerIntegrationRoutes } from "./routes/integrations.routes.js";
import { registerLeadRoutes } from "./routes/leads.routes.js";
import { BusinessService } from "./services/business.service.js";
import { DashboardService } from "./services/dashboard.service.js";
import { LeadIntakeService } from "./services/lead-intake.service.js";

export function buildApp() {
  const env = loadEnv();
  const adapters = buildAdapters({
    useMockIntegrations: env.USE_MOCK_INTEGRATIONS,
    googleServiceAccountJson: env.GOOGLE_SERVICE_ACCOUNT_JSON
  });

  const businessService = new BusinessService();
  const leadService = new LeadIntakeService(adapters.leadIntake);
  const dashboardService = new DashboardService(adapters, leadService);
  const syncMetricsJob = new SyncMetricsJob(adapters);

  const app = Fastify({ logger: true });

  const deps = {
    env,
    businessService,
    leadService,
    dashboardService,
    syncMetricsJob
  };

  void registerHealthRoutes(app);
  void registerBusinessRoutes(app, deps);
  void registerLeadRoutes(app, deps);
  void registerDashboardRoutes(app, deps);
  void registerIntegrationRoutes(app, deps);

  return app;
}

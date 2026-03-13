import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { RouteDeps } from "./types.js";

const syncBodySchema = z.object({
  startDate: z.string().date(),
  endDate: z.string().date()
});

export async function registerIntegrationRoutes(app: FastifyInstance, deps: RouteDeps) {
  app.post("/businesses/:businessId/sync/metrics", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);
    const body = syncBodySchema.safeParse(request.body);

    if (!params.success || !body.success) {
      return reply.status(400).send({ error: "invalid_payload" });
    }

    const business = deps.businessService.getById(params.data.businessId);
    if (!business) {
      return reply.status(404).send({ error: "business_not_found" });
    }

    const result = await deps.syncMetricsJob.runForBusiness(business, body.data);
    return { data: result };
  });

  app.get("/businesses/:businessId/integrations/status", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);

    if (!params.success) {
      return reply.status(400).send({ error: "invalid_business_id" });
    }

    const business = deps.businessService.getById(params.data.businessId);
    if (!business) {
      return reply.status(404).send({ error: "business_not_found" });
    }

    return {
      data: {
        mode: deps.env.USE_MOCK_INTEGRATIONS ? "mock" : "live",
        gbpConfigured: Boolean(business.gbpLocationId),
        ga4Configured: Boolean(business.ga4PropertyId),
        searchConsoleConfigured: Boolean(business.searchConsoleSiteUrl),
        googleCredentialsPresent: Boolean(deps.env.GOOGLE_SERVICE_ACCOUNT_JSON)
      }
    };
  });
}

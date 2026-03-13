import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { DashboardRange } from "../services/dashboard.service.js";
import type { RouteDeps } from "./types.js";

const rangeSchema = z.enum(["7d", "30d", "90d"]);

export async function registerDashboardRoutes(app: FastifyInstance, deps: RouteDeps) {
  app.get("/businesses/:businessId/dashboard", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);
    const query = z
      .object({
        range: rangeSchema.optional()
      })
      .safeParse(request.query);

    if (!params.success || !query.success) {
      return reply.status(400).send({ error: "invalid_request" });
    }

    try {
      const business = deps.businessService.getByIdOrThrow(params.data.businessId);
      const data = await deps.dashboardService.getDashboard(business, (query.data.range ?? "30d") as DashboardRange);
      return { data };
    } catch (error) {
      return reply.status(404).send({
        error: "business_not_found",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  app.get("/businesses/:businessId/visibility", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);

    if (!params.success) {
      return reply.status(400).send({ error: "invalid_business_id" });
    }

    const business = deps.businessService.getById(params.data.businessId);
    if (!business) {
      return reply.status(404).send({ error: "business_not_found" });
    }

    const data = await deps.dashboardService.getDashboard(business, "30d");
    return {
      data: data.visibility
    };
  });

  app.get("/businesses/:businessId/competitors/latest", async () => {
    return {
      data: [
        {
          competitorName: "Lars Construction",
          competitorRating: 4.9,
          competitorReviewCount: 142,
          localPackRank: 1,
          snapshotDate: new Date().toISOString().slice(0, 10)
        },
        {
          competitorName: "Metro Fire Repair",
          competitorRating: 4.5,
          competitorReviewCount: 67,
          localPackRank: 2,
          snapshotDate: new Date().toISOString().slice(0, 10)
        }
      ]
    };
  });

  app.get("/businesses/:businessId/marketing-metrics", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);

    if (!params.success) {
      return reply.status(400).send({ error: "invalid_business_id" });
    }

    const business = deps.businessService.getById(params.data.businessId);
    if (!business) {
      return reply.status(404).send({ error: "business_not_found" });
    }

    const data = await deps.dashboardService.getDashboard(business, "30d");

    return {
      data: {
        sessions: data.marketing.ga4.totals.sessions,
        conversions: data.marketing.ga4.totals.conversions,
        leads: data.leads.total,
        jobsWon: data.kpis.jobsWonThisMonth,
        revenueFromMarketing: data.kpis.revenueFromMarketing
      }
    };
  });
}

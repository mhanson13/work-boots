import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { RouteDeps } from "./types.js";

const createBusinessSchema = z.object({
  name: z.string().min(2),
  slug: z.string().min(2),
  ownerName: z.string().min(2),
  timezone: z.string().optional()
});

export async function registerBusinessRoutes(app: FastifyInstance, deps: RouteDeps) {
  app.get("/businesses", async () => {
    return { data: deps.businessService.list() };
  });

  app.post("/businesses", async (request, reply) => {
    const parsed = createBusinessSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.status(400).send({
        error: "invalid_payload",
        details: parsed.error.flatten()
      });
    }

    const created = deps.businessService.create(parsed.data);
    return reply.status(201).send({ data: created });
  });
}

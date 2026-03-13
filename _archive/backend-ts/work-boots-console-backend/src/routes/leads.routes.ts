import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { RouteDeps } from "./types.js";

const webhookSchema = z.object({
  businessId: z.string().uuid(),
  from: z.string(),
  subject: z.string(),
  textBody: z.string(),
  htmlBody: z.string().optional(),
  messageId: z.string().optional(),
  receivedAt: z.string().datetime()
});

const createLeadSchema = z.object({
  source: z.enum(["godaddy_email", "phone_call", "manual", "other"]),
  submittedAt: z.string().datetime(),
  customerName: z.string().optional(),
  customerPhone: z.string().optional(),
  customerEmail: z.string().email().optional(),
  serviceType: z.string().optional(),
  city: z.string().optional(),
  postalCode: z.string().optional(),
  message: z.string().optional()
});

const updateLeadSchema = z.object({
  status: z.enum(["new", "contacted", "qualified", "quoted", "won", "lost", "archived"]).optional(),
  estimatedJobValue: z.number().nonnegative().nullable().optional(),
  actualJobValue: z.number().nonnegative().nullable().optional(),
  firstResponseAt: z.string().datetime().nullable().optional()
});

const addLeadEventSchema = z.object({
  eventType: z.string().min(2),
  eventAt: z.string().datetime().optional(),
  payload: z.record(z.unknown()).optional()
});

export async function registerLeadRoutes(app: FastifyInstance, deps: RouteDeps) {
  app.post("/webhooks/godaddy/email", async (request, reply) => {
    const parsed = webhookSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.status(400).send({
        error: "invalid_payload",
        details: parsed.error.flatten()
      });
    }

    try {
      deps.businessService.getByIdOrThrow(parsed.data.businessId);
      const lead = deps.leadService.ingestGoDaddyEmail(parsed.data.businessId, parsed.data);
      return reply.status(201).send({ data: lead });
    } catch (error) {
      return reply.status(422).send({
        error: "ingest_failed",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  app.get("/businesses/:businessId/leads", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ error: "invalid_business_id" });
    }

    return {
      data: deps.leadService.listLeads(params.data.businessId)
    };
  });

  app.post("/businesses/:businessId/leads", async (request, reply) => {
    const params = z.object({ businessId: z.string().uuid() }).safeParse(request.params);
    const body = createLeadSchema.safeParse(request.body);

    if (!params.success || !body.success) {
      return reply.status(400).send({ error: "invalid_payload" });
    }

    const lead = deps.leadService.ingestGoDaddyEmail(params.data.businessId, {
      from: "manual@workboots.console",
      subject: `Manual lead (${body.data.source})`,
      textBody: `Name: ${body.data.customerName ?? "Unknown"}\nPhone: ${body.data.customerPhone ?? ""}\nEmail: ${
        body.data.customerEmail ?? ""
      }\nService: ${body.data.serviceType ?? ""}\nCity: ${body.data.city ?? ""}\nZip: ${
        body.data.postalCode ?? ""
      }\nMessage: ${body.data.message ?? ""}`,
      messageId: undefined,
      receivedAt: body.data.submittedAt
    });

    return reply.status(201).send({ data: lead });
  });

  app.patch("/businesses/:businessId/leads/:leadId", async (request, reply) => {
    const params = z
      .object({
        businessId: z.string().uuid(),
        leadId: z.string().uuid()
      })
      .safeParse(request.params);

    const body = updateLeadSchema.safeParse(request.body);

    if (!params.success || !body.success) {
      return reply.status(400).send({ error: "invalid_payload" });
    }

    try {
      const updated = deps.leadService.updateLead(params.data.leadId, body.data);
      return { data: updated };
    } catch (error) {
      return reply.status(404).send({
        error: "lead_not_found",
        message: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  app.post("/businesses/:businessId/leads/:leadId/events", async (request, reply) => {
    const params = z
      .object({
        businessId: z.string().uuid(),
        leadId: z.string().uuid()
      })
      .safeParse(request.params);
    const body = addLeadEventSchema.safeParse(request.body);

    if (!params.success || !body.success) {
      return reply.status(400).send({ error: "invalid_payload" });
    }

    const event = deps.leadService.addEvent({
      businessId: params.data.businessId,
      leadId: params.data.leadId,
      eventType: body.data.eventType,
      eventAt: body.data.eventAt ?? new Date().toISOString(),
      payload: body.data.payload ?? {}
    });

    return reply.status(201).send({ data: event });
  });
}

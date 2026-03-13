import { randomUUID } from "node:crypto";
import type { ParsedLead, RawEmailPayload } from "../integrations/types.js";
import type { GoDaddyLeadIntakeAdapter } from "../integrations/types.js";

export type LeadRecord = ParsedLead & {
  id: string;
  businessId: string;
  status: "new" | "contacted" | "qualified" | "quoted" | "won" | "lost" | "archived";
  estimatedJobValue: number | null;
  actualJobValue: number | null;
  firstResponseAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type LeadEventRecord = {
  id: string;
  leadId: string;
  businessId: string;
  eventType: string;
  eventAt: string;
  payload: Record<string, unknown>;
};

export class LeadIntakeService {
  private readonly leads = new Map<string, LeadRecord>();
  private readonly leadEvents: LeadEventRecord[] = [];

  constructor(private readonly adapter: GoDaddyLeadIntakeAdapter) {}

  ingestGoDaddyEmail(businessId: string, payload: RawEmailPayload): LeadRecord {
    const parsed = this.adapter.parseEmail(payload);
    if (!parsed) {
      throw new Error("Unable to parse GoDaddy lead email payload.");
    }

    const now = new Date().toISOString();
    const lead: LeadRecord = {
      id: randomUUID(),
      businessId,
      ...parsed,
      status: "new",
      estimatedJobValue: null,
      actualJobValue: null,
      firstResponseAt: null,
      createdAt: now,
      updatedAt: now
    };

    this.leads.set(lead.id, lead);

    this.addEvent({
      leadId: lead.id,
      businessId,
      eventType: "lead_received",
      eventAt: parsed.submittedAt,
      payload: { source: parsed.source }
    });

    return lead;
  }

  listLeads(businessId: string): LeadRecord[] {
    return [...this.leads.values()]
      .filter((lead) => lead.businessId === businessId)
      .sort((a, b) => (a.submittedAt < b.submittedAt ? 1 : -1));
  }

  getLead(leadId: string): LeadRecord | null {
    return this.leads.get(leadId) ?? null;
  }

  updateLead(
    leadId: string,
    input: Partial<Pick<LeadRecord, "status" | "estimatedJobValue" | "actualJobValue" | "firstResponseAt">>
  ): LeadRecord {
    const current = this.getLead(leadId);
    if (!current) {
      throw new Error(`Lead not found: ${leadId}`);
    }

    const updated: LeadRecord = {
      ...current,
      ...input,
      updatedAt: new Date().toISOString()
    };

    this.leads.set(leadId, updated);

    this.addEvent({
      leadId,
      businessId: updated.businessId,
      eventType: "status_changed",
      eventAt: updated.updatedAt,
      payload: {
        status: updated.status,
        estimatedJobValue: updated.estimatedJobValue,
        actualJobValue: updated.actualJobValue
      }
    });

    return updated;
  }

  addEvent(input: Omit<LeadEventRecord, "id">): LeadEventRecord {
    const event: LeadEventRecord = {
      id: randomUUID(),
      ...input
    };

    this.leadEvents.push(event);
    return event;
  }

  listLeadEvents(businessId: string): LeadEventRecord[] {
    return this.leadEvents.filter((event) => event.businessId === businessId);
  }

  averageResponseMinutes(businessId: string): number | null {
    const leads = this.listLeads(businessId).filter((lead) => Boolean(lead.firstResponseAt));
    if (!leads.length) {
      return null;
    }

    const totalMinutes = leads.reduce((sum, lead) => {
      const submittedAtMs = new Date(lead.submittedAt).getTime();
      const firstResponseAtMs = new Date(lead.firstResponseAt as string).getTime();
      const diffMinutes = Math.max((firstResponseAtMs - submittedAtMs) / 60000, 0);
      return sum + diffMinutes;
    }, 0);

    return Math.round((totalMinutes / leads.length) * 10) / 10;
  }
}

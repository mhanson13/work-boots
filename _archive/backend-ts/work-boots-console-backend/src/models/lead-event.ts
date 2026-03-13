export type LeadEventType =
  | "lead_received"
  | "auto_ack_sent"
  | "owner_notified"
  | "owner_contacted"
  | "appointment_set"
  | "quote_sent"
  | "status_changed"
  | "won"
  | "lost"
  | "note_added";

export type LeadEvent = {
  id: string;
  leadId: string;
  businessId: string;
  eventType: LeadEventType;
  eventAt: string;
  actorType: "system" | "owner" | "admin";
  actorId: string | null;
  channel: "sms" | "email" | "phone" | "dashboard" | null;
  payload: Record<string, unknown>;
  createdAt: string;
};

import type { RawEmailPayload } from "../types.js";

const fieldPatterns: Record<string, RegExp[]> = {
  customerName: [/name\s*[:|-]\s*(.+)/i, /customer\s*[:|-]\s*(.+)/i],
  customerPhone: [
    /phone\s*[:|-]\s*([+()\-\d\s]{7,})/i,
    /mobile\s*[:|-]\s*([+()\-\d\s]{7,})/i
  ],
  customerEmail: [
    /email\s*[:|-]\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i,
    /e-mail\s*[:|-]\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i
  ],
  serviceType: [/service\s*[:|-]\s*(.+)/i, /project\s*type\s*[:|-]\s*(.+)/i],
  city: [/city\s*[:|-]\s*(.+)/i],
  postalCode: [/zip\s*[:|-]\s*(\d{5}(?:-\d{4})?)/i, /postal\s*code\s*[:|-]\s*(\S+)/i],
  message: [/message\s*[:|-]\s*([\s\S]+)/i]
};

function extractField(text: string, patterns: RegExp[]): string | null {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) {
      return match[1].trim();
    }
  }

  return null;
}

export function parseGoDaddyLeadEmail(payload: RawEmailPayload) {
  const body = payload.textBody ?? "";

  if (!body.trim()) {
    return null;
  }

  const parsed = {
    source: "godaddy_email" as const,
    externalId: payload.messageId ?? null,
    submittedAt: payload.receivedAt,
    customerName: extractField(body, fieldPatterns.customerName),
    customerPhone: extractField(body, fieldPatterns.customerPhone),
    customerEmail: extractField(body, fieldPatterns.customerEmail),
    serviceType: extractField(body, fieldPatterns.serviceType),
    city: extractField(body, fieldPatterns.city),
    postalCode: extractField(body, fieldPatterns.postalCode),
    message: extractField(body, fieldPatterns.message)
  };

  const hasPrimaryContact = Boolean(parsed.customerPhone || parsed.customerEmail);
  return hasPrimaryContact ? parsed : null;
}

import { parseGoDaddyLeadEmail } from "./godaddy-email-parser.js";
import type { GoDaddyLeadIntakeAdapter, RawEmailPayload } from "../types.js";

export class GoDaddyEmailAdapter implements GoDaddyLeadIntakeAdapter {
  parseEmail(payload: RawEmailPayload) {
    return parseGoDaddyLeadEmail(payload);
  }
}

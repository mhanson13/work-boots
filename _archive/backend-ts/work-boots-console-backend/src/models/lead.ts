export type LeadSource = "godaddy_email" | "phone_call" | "manual" | "other";

export type LeadStatus =
  | "new"
  | "contacted"
  | "qualified"
  | "quoted"
  | "won"
  | "lost"
  | "archived";

export type Lead = {
  id: string;
  businessId: string;
  source: LeadSource;
  externalId: string | null;
  submittedAt: string;
  customerName: string | null;
  customerPhone: string | null;
  customerEmail: string | null;
  serviceType: string | null;
  city: string | null;
  postalCode: string | null;
  message: string | null;
  status: LeadStatus;
  estimatedJobValue: number | null;
  actualJobValue: number | null;
  firstResponseAt: string | null;
  lastContactedAt: string | null;
  closedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

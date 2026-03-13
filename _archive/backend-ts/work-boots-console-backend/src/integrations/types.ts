import type { LeadSource } from "../models/lead.js";

export type DateRange = {
  startDate: string;
  endDate: string;
};

export type RawEmailPayload = {
  messageId?: string;
  from: string;
  subject: string;
  textBody: string;
  htmlBody?: string;
  receivedAt: string;
};

export type ParsedLead = {
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
};

export interface GoDaddyLeadIntakeAdapter {
  parseEmail(payload: RawEmailPayload): ParsedLead | null;
}

export type GbpProfileSummary = {
  rating: number | null;
  reviewCount: number;
  category: string | null;
  profileCompletenessPct: number;
};

export interface GbpClient {
  getProfileSummary(locationId: string): Promise<GbpProfileSummary>;
}

export type GbpPerformanceMetrics = {
  daily: Array<{
    date: string;
    profileViews: number;
    websiteClicks: number;
    phoneCalls: number;
    directionRequests: number;
  }>;
};

export interface GbpPerformanceClient {
  getPerformance(locationId: string, range: DateRange): Promise<GbpPerformanceMetrics>;
}

export type Ga4TrafficMetrics = {
  totals: {
    sessions: number;
    users: number;
    conversions: number;
  };
  byChannel: Array<{
    channel: string;
    sessions: number;
    conversions: number;
  }>;
};

export interface Ga4Client {
  getTraffic(propertyId: string, range: DateRange): Promise<Ga4TrafficMetrics>;
}

export type SearchConsoleMetrics = {
  totals: {
    clicks: number;
    impressions: number;
    ctr: number;
    avgPosition: number;
  };
  topQueries: Array<{
    query: string;
    clicks: number;
    impressions: number;
    position: number;
  }>;
};

export interface SearchConsoleClient {
  getPerformance(siteUrl: string, range: DateRange): Promise<SearchConsoleMetrics>;
}

export type IntegrationAdapters = {
  leadIntake: GoDaddyLeadIntakeAdapter;
  gbp: GbpClient;
  gbpPerformance: GbpPerformanceClient;
  ga4: Ga4Client;
  searchConsole: SearchConsoleClient;
};

import type { IntegrationAdapters } from "../integrations/types.js";
import type { BusinessRecord } from "./business.service.js";
import type { LeadIntakeService } from "./lead-intake.service.js";

export type DashboardRange = "7d" | "30d" | "90d";

function dateRangeFromPreset(range: DashboardRange): { startDate: string; endDate: string } {
  const end = new Date();
  const days = range === "7d" ? 7 : range === "30d" ? 30 : 90;
  const start = new Date();
  start.setDate(end.getDate() - (days - 1));

  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10)
  };
}

export class DashboardService {
  constructor(
    private readonly adapters: IntegrationAdapters,
    private readonly leadService: LeadIntakeService
  ) {}

  async getDashboard(business: BusinessRecord, range: DashboardRange = "30d") {
    const dateRange = dateRangeFromPreset(range);

    const [gbpSummary, gbpPerformance, ga4, searchConsole] = await Promise.all([
      business.gbpLocationId ? this.adapters.gbp.getProfileSummary(business.gbpLocationId) : null,
      business.gbpLocationId
        ? this.adapters.gbpPerformance.getPerformance(business.gbpLocationId, dateRange)
        : { daily: [] },
      business.ga4PropertyId
        ? this.adapters.ga4.getTraffic(business.ga4PropertyId, dateRange)
        : { totals: { sessions: 0, users: 0, conversions: 0 }, byChannel: [] },
      business.searchConsoleSiteUrl
        ? this.adapters.searchConsole.getPerformance(business.searchConsoleSiteUrl, dateRange)
        : { totals: { clicks: 0, impressions: 0, ctr: 0, avgPosition: 0 }, topQueries: [] }
    ]);

    const leads = this.leadService.listLeads(business.id);
    const leadsToday = leads.filter((lead) => lead.submittedAt.slice(0, 10) === dateRange.endDate).length;
    const jobsWonThisMonth = leads.filter(
      (lead) => lead.status === "won" && lead.updatedAt.slice(0, 7) === dateRange.endDate.slice(0, 7)
    ).length;

    const revenueFromMarketing = leads
      .filter((lead) => lead.status === "won")
      .reduce((sum, lead) => sum + (lead.actualJobValue ?? 0), 0);

    return {
      business: {
        id: business.id,
        name: business.name,
        ownerName: business.ownerName
      },
      range,
      kpis: {
        leadsToday,
        avgResponseMinutes: this.leadService.averageResponseMinutes(business.id),
        jobsWonThisMonth,
        revenueFromMarketing
      },
      visibility: {
        gbpSummary,
        gbpPerformance,
        searchConsole
      },
      marketing: {
        ga4
      },
      leads: {
        total: leads.length,
        byStatus: leads.reduce<Record<string, number>>((acc, lead) => {
          acc[lead.status] = (acc[lead.status] ?? 0) + 1;
          return acc;
        }, {})
      }
    };
  }
}

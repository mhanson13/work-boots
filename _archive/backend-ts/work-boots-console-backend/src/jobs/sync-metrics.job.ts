import type { BusinessRecord } from "./business.service.js";
import type { IntegrationAdapters } from "../integrations/types.js";

export class SyncMetricsJob {
  constructor(private readonly adapters: IntegrationAdapters) {}

  async runForBusiness(business: BusinessRecord, range: { startDate: string; endDate: string }) {
    const [gbpSummary, gbpPerformance, ga4, searchConsole] = await Promise.all([
      business.gbpLocationId ? this.adapters.gbp.getProfileSummary(business.gbpLocationId) : null,
      business.gbpLocationId
        ? this.adapters.gbpPerformance.getPerformance(business.gbpLocationId, range)
        : { daily: [] },
      business.ga4PropertyId
        ? this.adapters.ga4.getTraffic(business.ga4PropertyId, range)
        : { totals: { sessions: 0, users: 0, conversions: 0 }, byChannel: [] },
      business.searchConsoleSiteUrl
        ? this.adapters.searchConsole.getPerformance(business.searchConsoleSiteUrl, range)
        : { totals: { clicks: 0, impressions: 0, ctr: 0, avgPosition: 0 }, topQueries: [] }
    ]);

    return {
      businessId: business.id,
      syncedAt: new Date().toISOString(),
      gbpSummary,
      gbpDays: gbpPerformance.daily.length,
      ga4Totals: ga4.totals,
      searchConsoleTotals: searchConsole.totals
    };
  }
}

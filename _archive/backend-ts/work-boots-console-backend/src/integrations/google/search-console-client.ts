import type { DateRange, SearchConsoleClient, SearchConsoleMetrics } from "../types.js";

export class GoogleSearchConsoleClient implements SearchConsoleClient {
  constructor(private readonly serviceAccountJson: string | undefined) {}

  async getPerformance(siteUrl: string, _range: DateRange): Promise<SearchConsoleMetrics> {
    if (!this.serviceAccountJson) {
      throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON is required for live Search Console calls.");
    }

    // TODO: Replace with real Search Console API call.
    return {
      totals: {
        clicks: 0,
        impressions: 0,
        ctr: 0,
        avgPosition: 0
      },
      topQueries: [
        {
          query: `${siteUrl}::placeholder`,
          clicks: 0,
          impressions: 0,
          position: 0
        }
      ]
    };
  }
}

import type { DateRange, SearchConsoleClient, SearchConsoleMetrics } from "../types.js";

export class MockSearchConsoleClient implements SearchConsoleClient {
  async getPerformance(_siteUrl: string, _range: DateRange): Promise<SearchConsoleMetrics> {
    return {
      totals: {
        clicks: 602,
        impressions: 6820,
        ctr: 0.088,
        avgPosition: 11.2
      },
      topQueries: [
        {
          query: "fire restoration denver",
          clicks: 161,
          impressions: 980,
          position: 4.2
        },
        {
          query: "smoke damage cleanup",
          clicks: 120,
          impressions: 710,
          position: 6.4
        },
        {
          query: "water and fire repair company",
          clicks: 88,
          impressions: 690,
          position: 8.8
        }
      ]
    };
  }
}

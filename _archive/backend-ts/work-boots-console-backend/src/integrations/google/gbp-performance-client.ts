import type { DateRange, GbpPerformanceClient, GbpPerformanceMetrics } from "../types.js";

export class GoogleBusinessProfilePerformanceClient implements GbpPerformanceClient {
  constructor(private readonly serviceAccountJson: string | undefined) {}

  async getPerformance(locationId: string, range: DateRange): Promise<GbpPerformanceMetrics> {
    if (!this.serviceAccountJson) {
      throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON is required for live GBP Performance calls.");
    }

    // TODO: Replace with real GBP Performance API call.
    return {
      daily: [
        {
          date: range.startDate,
          profileViews: 0,
          websiteClicks: 0,
          phoneCalls: 0,
          directionRequests: 0
        }
      ]
    };
  }
}

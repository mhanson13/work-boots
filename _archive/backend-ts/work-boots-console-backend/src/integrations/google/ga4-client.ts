import type { DateRange, Ga4Client, Ga4TrafficMetrics } from "../types.js";

export class GoogleAnalyticsDataClient implements Ga4Client {
  constructor(private readonly serviceAccountJson: string | undefined) {}

  async getTraffic(propertyId: string, _range: DateRange): Promise<Ga4TrafficMetrics> {
    if (!this.serviceAccountJson) {
      throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON is required for live GA4 calls.");
    }

    // TODO: Replace with real GA4 Data API call.
    return {
      totals: {
        sessions: 0,
        users: 0,
        conversions: 0
      },
      byChannel: [
        {
          channel: `property:${propertyId}`,
          sessions: 0,
          conversions: 0
        }
      ]
    };
  }
}

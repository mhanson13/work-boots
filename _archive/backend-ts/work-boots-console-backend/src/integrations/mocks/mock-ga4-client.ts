import type { DateRange, Ga4Client, Ga4TrafficMetrics } from "../types.js";

export class MockGa4Client implements Ga4Client {
  async getTraffic(_propertyId: string, _range: DateRange): Promise<Ga4TrafficMetrics> {
    return {
      totals: {
        sessions: 1310,
        users: 940,
        conversions: 41
      },
      byChannel: [
        {
          channel: "organic",
          sessions: 730,
          conversions: 22
        },
        {
          channel: "direct",
          sessions: 390,
          conversions: 12
        },
        {
          channel: "referral",
          sessions: 190,
          conversions: 7
        }
      ]
    };
  }
}

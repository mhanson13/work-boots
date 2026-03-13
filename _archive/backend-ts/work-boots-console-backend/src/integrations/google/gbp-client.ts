import type { GbpClient, GbpProfileSummary } from "../types.js";

export class GoogleBusinessProfileClient implements GbpClient {
  constructor(private readonly serviceAccountJson: string | undefined) {}

  async getProfileSummary(locationId: string): Promise<GbpProfileSummary> {
    if (!this.serviceAccountJson) {
      throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON is required for live GBP calls.");
    }

    // TODO: Replace with real Google Business Profile API call.
    return {
      rating: 4.6,
      reviewCount: 0,
      category: `location:${locationId}`,
      profileCompletenessPct: 80
    };
  }
}

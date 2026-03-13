import type { GbpClient, GbpProfileSummary } from "../types.js";

export class MockGbpClient implements GbpClient {
  async getProfileSummary(_locationId: string): Promise<GbpProfileSummary> {
    return {
      rating: 4.7,
      reviewCount: 83,
      category: "Fire damage restoration service",
      profileCompletenessPct: 92
    };
  }
}

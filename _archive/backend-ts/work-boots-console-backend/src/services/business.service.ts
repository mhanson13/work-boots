import { randomUUID } from "node:crypto";

export type BusinessRecord = {
  id: string;
  name: string;
  slug: string;
  ownerName: string;
  timezone: string;
  gbpLocationId: string | null;
  ga4PropertyId: string | null;
  searchConsoleSiteUrl: string | null;
};

export class BusinessService {
  private readonly businesses = new Map<string, BusinessRecord>([
    [
      "11111111-1111-1111-1111-111111111111",
      {
        id: "11111111-1111-1111-1111-111111111111",
        name: "T&M Fire",
        slug: "tm-fire",
        ownerName: "Matt Hansen",
        timezone: "America/Denver",
        gbpLocationId: process.env.GBP_LOCATION_ID ?? "1234567890",
        ga4PropertyId: process.env.GA4_PROPERTY_ID ?? "987654321",
        searchConsoleSiteUrl: process.env.SEARCH_CONSOLE_SITE_URL ?? "sc-domain:tmfire.example"
      }
    ]
  ]);

  list(): BusinessRecord[] {
    return [...this.businesses.values()];
  }

  getById(id: string): BusinessRecord | null {
    return this.businesses.get(id) ?? null;
  }

  getByIdOrThrow(id: string): BusinessRecord {
    const business = this.getById(id);
    if (!business) {
      throw new Error(`Business not found: ${id}`);
    }

    return business;
  }

  create(input: { name: string; slug: string; ownerName: string; timezone?: string }): BusinessRecord {
    const id = randomUUID();
    const record: BusinessRecord = {
      id,
      name: input.name,
      slug: input.slug,
      ownerName: input.ownerName,
      timezone: input.timezone ?? "America/Denver",
      gbpLocationId: null,
      ga4PropertyId: null,
      searchConsoleSiteUrl: null
    };

    this.businesses.set(id, record);
    return record;
  }
}

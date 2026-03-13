export type Business = {
  id: string;
  name: string;
  slug: string;
  ownerName: string | null;
  phone: string | null;
  email: string | null;
  timezone: string;
  serviceAreas: string[];
  services: string[];
  godaddySiteUrl: string | null;
  gbpLocationId: string | null;
  ga4PropertyId: string | null;
  searchConsoleSiteUrl: string | null;
  defaultCurrency: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
};

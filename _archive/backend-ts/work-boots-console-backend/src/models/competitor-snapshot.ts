export type CompetitorSnapshot = {
  id: string;
  businessId: string;
  snapshotDate: string;
  competitorName: string;
  competitorPlaceId: string | null;
  competitorRating: number | null;
  competitorReviewCount: number | null;
  localPackRank: number | null;
  shareOfVoicePct: number | null;
  keywords: Array<{ keyword: string; rank?: number }>;
  notes: string | null;
  createdAt: string;
};

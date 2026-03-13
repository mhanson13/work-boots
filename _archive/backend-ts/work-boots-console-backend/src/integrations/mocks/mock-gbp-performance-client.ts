import type { DateRange, GbpPerformanceClient, GbpPerformanceMetrics } from "../types.js";

function dateList(range: DateRange): string[] {
  const start = new Date(range.startDate);
  const end = new Date(range.endDate);
  const values: string[] = [];

  for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    values.push(date.toISOString().slice(0, 10));
  }

  return values;
}

export class MockGbpPerformanceClient implements GbpPerformanceClient {
  async getPerformance(_locationId: string, range: DateRange): Promise<GbpPerformanceMetrics> {
    const dates = dateList(range);

    return {
      daily: dates.map((date, index) => ({
        date,
        profileViews: 20 + index,
        websiteClicks: 4 + (index % 3),
        phoneCalls: 2 + (index % 2),
        directionRequests: 1 + (index % 2)
      }))
    };
  }
}

import { GoDaddyEmailAdapter } from "./email/godaddy-email-adapter.js";
import { GoogleAnalyticsDataClient } from "./google/ga4-client.js";
import { GoogleBusinessProfileClient } from "./google/gbp-client.js";
import { GoogleBusinessProfilePerformanceClient } from "./google/gbp-performance-client.js";
import { GoogleSearchConsoleClient } from "./google/search-console-client.js";
import { MockGa4Client } from "./mocks/mock-ga4-client.js";
import { MockGbpClient } from "./mocks/mock-gbp-client.js";
import { MockGbpPerformanceClient } from "./mocks/mock-gbp-performance-client.js";
import { MockSearchConsoleClient } from "./mocks/mock-search-console-client.js";
import type { IntegrationAdapters } from "./types.js";

export type IntegrationFactoryOptions = {
  useMockIntegrations: boolean;
  googleServiceAccountJson?: string;
};

export function buildAdapters(options: IntegrationFactoryOptions): IntegrationAdapters {
  const leadIntake = new GoDaddyEmailAdapter();

  if (options.useMockIntegrations) {
    return {
      leadIntake,
      gbp: new MockGbpClient(),
      gbpPerformance: new MockGbpPerformanceClient(),
      ga4: new MockGa4Client(),
      searchConsole: new MockSearchConsoleClient()
    };
  }

  return {
    leadIntake,
    gbp: new GoogleBusinessProfileClient(options.googleServiceAccountJson),
    gbpPerformance: new GoogleBusinessProfilePerformanceClient(options.googleServiceAccountJson),
    ga4: new GoogleAnalyticsDataClient(options.googleServiceAccountJson),
    searchConsole: new GoogleSearchConsoleClient(options.googleServiceAccountJson)
  };
}

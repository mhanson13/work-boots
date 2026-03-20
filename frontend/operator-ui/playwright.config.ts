import { defineConfig } from "@playwright/test";

const baseUrl = "http://127.0.0.1:3101";

export default defineConfig({
  testDir: "./smoke",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: baseUrl,
    headless: true,
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname 127.0.0.1 --port 3101",
    url: baseUrl,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});

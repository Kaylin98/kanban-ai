import { defineConfig, devices } from "@playwright/test";

// Set BASE_URL (e.g. http://localhost:8000) to test a running container instead of the dev server.
const baseURL = process.env.BASE_URL;

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: baseURL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: baseURL
    ? undefined
    : {
        command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
        url: "http://127.0.0.1:3000",
        reuseExistingServer: true,
        timeout: 120_000,
      },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

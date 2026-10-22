import { defineConfig, devices } from "@playwright/test";

// By default, builds the frontend and serves it with the backend on port 8001.
// Set BASE_URL (e.g. http://localhost:8000) to test a running container instead.
const baseURL = process.env.BASE_URL;

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: baseURL ?? "http://127.0.0.1:8001",
    trace: "retain-on-failure",
  },
  webServer: baseURL
    ? undefined
    : {
        command:
          "npm run build && uv run --directory ../backend uvicorn app.main:app --host 127.0.0.1 --port 8001",
        url: "http://127.0.0.1:8001/api/health",
        reuseExistingServer: true,
        timeout: 180_000,
      },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

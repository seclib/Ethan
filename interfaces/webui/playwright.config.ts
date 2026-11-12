import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  // En mode dev, Next compile chaque route/chunk à la demande : un premier
  // accès à /settings ou /projects peut dépasser les 5 s par défaut, surtout
  // avec plusieurs workers en parallèle. 10 s absorbe la compilation à froid
  // sans masquer les vraies régressions (les parcours chauds restent < 1 s).
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.ETHAN_WEBUI_URL || "http://localhost:3001",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3001",
    reuseExistingServer: !process.env.CI,
  },
});
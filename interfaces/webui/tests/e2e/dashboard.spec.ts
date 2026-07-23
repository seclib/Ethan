import { test, expect } from "@playwright/test";

test.describe("Dashboard Flow", () => {
  test("dashboard loads with KPI cards", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".kpi-card").first()).toBeVisible();
  });

  test("dashboard has navigation sidebar", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".sidebar")).toBeVisible();
  });

  test("dashboard has top bar", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".top-bar")).toBeVisible();
  });

  test("command palette accessible via keyboard", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Meta+k");
    await expect(page.locator(".cmd-modal")).toBeVisible();
  });

  test("mission control accessible via keyboard", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Meta+t");
    await expect(page.locator(".mission-overlay")).toBeVisible();
  });
});
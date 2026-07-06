import { test, expect } from "@playwright/test";

test.describe("ETHAN WebUI", () => {
  test("homepage loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator(".kpi-card").first()).toBeVisible();
  });

  test("navigation to flux", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/flux"]');
    await expect(page.locator("text=Flux")).toBeVisible();
  });

  test("navigation to agents", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/agents"]');
    await expect(page.locator("text=Agents")).toBeVisible();
  });

  test("navigation to memory", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/memory"]');
    await expect(page.locator("text=Mémoire")).toBeVisible();
  });

  test("navigation to skills", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/skills"]');
    await expect(page.locator("text=Skills")).toBeVisible();
  });

  test("navigation to config", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/config"]');
    await expect(page.locator(".config-section").first()).toBeVisible();
  });

  test("mission control opens", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Meta+t");
    await expect(page.locator(".mission-overlay")).toBeVisible();
    await expect(page.locator(".mission-card").first()).toBeVisible();
  });

  test("command palette opens", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Meta+k");
    await expect(page.locator("text=Dashboard")).toBeVisible();
  });
});

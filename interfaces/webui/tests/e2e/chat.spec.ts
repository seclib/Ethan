import { test, expect } from "@playwright/test";

test.describe("Chat", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders chat page", async ({ page }) => {
    await page.click("text=Chat");
    await expect(page.locator("h1")).toContainText("Chat");
  });

  test("shows empty state", async ({ page }) => {
    await page.click("text=Chat");
    await expect(page.locator("text=Commencez une conversation avec ETHAN")).toBeVisible();
  });

  test("sends a message", async ({ page }) => {
    await page.click("text=Chat");
    await page.fill('input[placeholder="Message ETHAN..."]', "Bonjour");
    await page.click("button:has(svg)");
    await expect(page.locator(".space-y-4 > div").first()).toContainText("Bonjour");
  });
});
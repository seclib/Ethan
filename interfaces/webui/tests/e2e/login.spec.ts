import { test, expect } from "@playwright/test";

test.describe("Login Flow", () => {
  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("text=Connexion")).toBeVisible();
  });

  test("login form is visible", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
    await expect(page.locator("button[type='submit']")).toBeVisible();
  });

  test("login form validation", async ({ page }) => {
    await page.goto("/login");
    await page.click("button[type='submit']");
    // Should show validation errors or prevent submission
    await expect(page).toHaveURL(/\/login/);
  });
});
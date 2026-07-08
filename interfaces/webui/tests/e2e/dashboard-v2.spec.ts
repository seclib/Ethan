import { test, expect } from "@playwright/test";

test.describe("Dashboard V2 — Navigation & Pages", () => {
  test("should navigate to Agents page", async ({ page }) => {
    await page.goto("/agents");
    await expect(page.locator("h1")).toContainText("Agents");
    await expect(page.locator("text=Manage your AI agents")).toBeVisible();
  });

  test("should navigate to Missions page", async ({ page }) => {
    await page.goto("/missions");
    await expect(page.locator("h1")).toContainText("Missions");
    await expect(page.locator("text=Active and completed missions")).toBeVisible();
  });

  test("should navigate to Goals page", async ({ page }) => {
    await page.goto("/goals");
    await expect(page.locator("h1")).toContainText("Goals");
    await expect(page.locator("text=Active goals and task decomposition")).toBeVisible();
  });

  test("should navigate to Memory Facts page", async ({ page }) => {
    await page.goto("/memory/facts");
    await expect(page.locator("h1")).toContainText("Memory Facts");
    await expect(page.locator("text=Atomic facts with confidence")).toBeVisible();
  });

  test("should navigate to Skills Lab page", async ({ page }) => {
    await page.goto("/skills/lab");
    await expect(page.locator("h1")).toContainText("Skills Lab");
    await expect(page.locator("text=Test, validate, and install skills")).toBeVisible();
  });

  test("should navigate to Flux page", async ({ page }) => {
    await page.goto("/flux");
    await expect(page.locator("h1")).toContainText("Event Flux");
    await expect(page.locator("text=Real-time event stream")).toBeVisible();
  });

  test("should navigate to Settings page", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
    await expect(page.locator("text=System configuration and governance")).toBeVisible();
  });

  test("should have sidebar navigation visible", async ({ page }) => {
    await page.goto("/agents");
    // Sidebar should be visible
    await expect(page.locator("aside")).toBeVisible();
    // Should contain ETHAN branding
    await expect(page.locator("text=ETHAN")).toBeVisible();
    // Should have navigation items
    await expect(page.locator("text=Agents")).toBeVisible();
    await expect(page.locator("text=Missions")).toBeVisible();
    await expect(page.locator("text=Goals")).toBeVisible();
  });

  test("should navigate between pages via sidebar", async ({ page }) => {
    await page.goto("/agents");
    // Click on Goals in sidebar
    await page.locator('a[href="/goals"]').click();
    await expect(page.locator("h1")).toContainText("Goals");

    // Click on Missions in sidebar
    await page.locator('a[href="/missions"]').click();
    await expect(page.locator("h1")).toContainText("Missions");

    // Click on Flux in sidebar
    await page.locator('a[href="/flux"]').click();
    await expect(page.locator("h1")).toContainText("Event Flux");
  });

  test("should show loading state when data is being fetched", async ({ page }) => {
    // Intercept API calls to simulate loading
    await page.route("**/api/v1/agents", (route) => {
      // Delay response to show loading state
      setTimeout(() => route.fulfill({ status: 200, body: "[]" }), 1000);
    });

    await page.goto("/agents");
    await expect(page.locator("text=Loading agents...")).toBeVisible({ timeout: 500 });
  });

  test("should show error state when API fails", async ({ page }) => {
    await page.route("**/api/v1/agents", (route) => {
      route.fulfill({ status: 500, body: JSON.stringify({ error: "Server error" }) });
    });

    await page.goto("/agents");
    await expect(page.locator("text=Error:")).toBeVisible({ timeout: 5000 });
  });

  test("should display empty state when no data", async ({ page }) => {
    await page.route("**/api/v1/missions", (route) => {
      route.fulfill({ status: 200, body: "[]" });
    });

    await page.goto("/missions");
    await expect(page.locator("text=No missions yet")).toBeVisible();
  });
});
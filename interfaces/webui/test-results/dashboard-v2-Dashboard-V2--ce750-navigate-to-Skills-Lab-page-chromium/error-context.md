# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard-v2.spec.ts >> Dashboard V2 — Navigation & Pages >> should navigate to Skills Lab page
- Location: tests/e2e/dashboard-v2.spec.ts:28:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Skills Lab"
Received string:    "ETHAN"
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')
    14 × locator resolved to <h1 class="text-xl font-semibold tracking-[0.15em] text-white/90 uppercase select-none">ETHAN</h1>
       - unexpected value "ETHAN"

```

```yaml
- heading "ETHAN" [level=1]
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | 
  3   | test.describe("Dashboard V2 — Navigation & Pages", () => {
  4   |   test("should navigate to Agents page", async ({ page }) => {
  5   |     await page.goto("/agents");
  6   |     await expect(page.locator("h1")).toContainText("Agents");
  7   |     await expect(page.locator("text=Manage your AI agents")).toBeVisible();
  8   |   });
  9   | 
  10  |   test("should navigate to Missions page", async ({ page }) => {
  11  |     await page.goto("/missions");
  12  |     await expect(page.locator("h1")).toContainText("Missions");
  13  |     await expect(page.locator("text=Active and completed missions")).toBeVisible();
  14  |   });
  15  | 
  16  |   test("should navigate to Goals page", async ({ page }) => {
  17  |     await page.goto("/goals");
  18  |     await expect(page.locator("h1")).toContainText("Goals");
  19  |     await expect(page.locator("text=Active goals and task decomposition")).toBeVisible();
  20  |   });
  21  | 
  22  |   test("should navigate to Memory Facts page", async ({ page }) => {
  23  |     await page.goto("/memory/facts");
  24  |     await expect(page.locator("h1")).toContainText("Memory Facts");
  25  |     await expect(page.locator("text=Atomic facts with confidence")).toBeVisible();
  26  |   });
  27  | 
  28  |   test("should navigate to Skills Lab page", async ({ page }) => {
  29  |     await page.goto("/skills/lab");
> 30  |     await expect(page.locator("h1")).toContainText("Skills Lab");
      |                                      ^ Error: expect(locator).toContainText(expected) failed
  31  |     await expect(page.locator("text=Test, validate, and install skills")).toBeVisible();
  32  |   });
  33  | 
  34  |   test("should navigate to Flux page", async ({ page }) => {
  35  |     await page.goto("/flux");
  36  |     await expect(page.locator("h1")).toContainText("Event Flux");
  37  |     await expect(page.locator("text=Real-time event stream")).toBeVisible();
  38  |   });
  39  | 
  40  |   test("should navigate to Settings page", async ({ page }) => {
  41  |     await page.goto("/settings");
  42  |     await expect(page.locator("h1")).toContainText("Settings");
  43  |     await expect(page.locator("text=System configuration and governance")).toBeVisible();
  44  |   });
  45  | 
  46  |   test("should have sidebar navigation visible", async ({ page }) => {
  47  |     await page.goto("/agents");
  48  |     // Sidebar should be visible
  49  |     await expect(page.locator("aside")).toBeVisible();
  50  |     // Should contain ETHAN branding
  51  |     await expect(page.locator("text=ETHAN")).toBeVisible();
  52  |     // Should have navigation items
  53  |     await expect(page.locator("text=Agents")).toBeVisible();
  54  |     await expect(page.locator("text=Missions")).toBeVisible();
  55  |     await expect(page.locator("text=Goals")).toBeVisible();
  56  |   });
  57  | 
  58  |   test("should navigate between pages via sidebar", async ({ page }) => {
  59  |     await page.goto("/agents");
  60  |     // Click on Goals in sidebar
  61  |     await page.locator('a[href="/goals"]').click();
  62  |     await expect(page.locator("h1")).toContainText("Goals");
  63  | 
  64  |     // Click on Missions in sidebar
  65  |     await page.locator('a[href="/missions"]').click();
  66  |     await expect(page.locator("h1")).toContainText("Missions");
  67  | 
  68  |     // Click on Flux in sidebar
  69  |     await page.locator('a[href="/flux"]').click();
  70  |     await expect(page.locator("h1")).toContainText("Event Flux");
  71  |   });
  72  | 
  73  |   test("should show loading state when data is being fetched", async ({ page }) => {
  74  |     // Intercept API calls to simulate loading
  75  |     await page.route("**/api/v1/agents", (route) => {
  76  |       // Delay response to show loading state
  77  |       setTimeout(() => route.fulfill({ status: 200, body: "[]" }), 1000);
  78  |     });
  79  | 
  80  |     await page.goto("/agents");
  81  |     await expect(page.locator("text=Loading agents...")).toBeVisible({ timeout: 500 });
  82  |   });
  83  | 
  84  |   test("should show error state when API fails", async ({ page }) => {
  85  |     await page.route("**/api/v1/agents", (route) => {
  86  |       route.fulfill({ status: 500, body: JSON.stringify({ error: "Server error" }) });
  87  |     });
  88  | 
  89  |     await page.goto("/agents");
  90  |     await expect(page.locator("text=Error:")).toBeVisible({ timeout: 5000 });
  91  |   });
  92  | 
  93  |   test("should display empty state when no data", async ({ page }) => {
  94  |     await page.route("**/api/v1/missions", (route) => {
  95  |       route.fulfill({ status: 200, body: "[]" });
  96  |     });
  97  | 
  98  |     await page.goto("/missions");
  99  |     await expect(page.locator("text=No missions yet")).toBeVisible();
  100 |   });
  101 | });
```
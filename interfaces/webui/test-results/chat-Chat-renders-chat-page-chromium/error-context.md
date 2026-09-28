# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> Chat >> renders chat page
- Location: tests/e2e/chat.spec.ts:8:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Chat"
Received string:    "ETHAN"
Timeout: 5000ms

Call log:
  - Expect "toContainText" locator('h1') with timeout 5000ms
  - waiting for locator('h1')
    13 × locator resolved to <h1 class="text-xl font-semibold tracking-[0.15em] text-white/90 uppercase select-none">ETHAN</h1>
       - unexpected value "ETHAN"

```

```yaml
- heading "ETHAN" [level=1]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Chat", () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto("/");
  6  |   });
  7  | 
  8  |   test("renders chat page", async ({ page }) => {
  9  |     await page.click("text=Chat");
> 10 |     await expect(page.locator("h1")).toContainText("Chat");
     |                                      ^ Error: expect(locator).toContainText(expected) failed
  11 |   });
  12 | 
  13 |   test("shows empty state", async ({ page }) => {
  14 |     await page.click("text=Chat");
  15 |     await expect(page.locator("text=Commencez une conversation avec ETHAN")).toBeVisible();
  16 |   });
  17 | 
  18 |   test("sends a message", async ({ page }) => {
  19 |     await page.click("text=Chat");
  20 |     await page.fill('input[placeholder="Message ETHAN..."]', "Bonjour");
  21 |     await page.click("button:has(svg)");
  22 |     await expect(page.locator(".space-y-4 > div").first()).toContainText("Bonjour");
  23 |   });
  24 | });
```
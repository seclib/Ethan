# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: app.spec.ts >> ETHAN WebUI >> mission control opens
- Location: tests/e2e/app.spec.ts:39:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.mission-overlay')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.mission-overlay') with timeout 5000ms
  - waiting for locator('.mission-overlay')

```

```yaml
- navigation:
  - img "ETHAN"
  - text: ETHAN
  - button "Replier la sidebar":
    - img
  - button "Nouveau chat":
    - text: Nouveau chat
    - img
  - button "Rechercher":
    - img
    - text: Rechercher… Ctrl K
  - button "Projets":
    - img
    - text: Projets
    - img
  - link "Agents":
    - /url: /agents
    - img
    - text: Agents
  - button "Pilotage" [expanded]:
    - text: Pilotage
    - img
  - link "Missions":
    - /url: /missions
    - img
    - text: Missions
  - link "Calendar":
    - /url: /calendar
    - img
    - text: Calendar
  - link "Notes":
    - /url: /notes
    - img
    - text: Notes
  - link "Inbox":
    - /url: /inbox
    - img
    - text: Inbox
  - link "Deep Research":
    - /url: /research
    - img
    - text: Deep Research
  - link "Cookbook":
    - /url: /cookbook
    - img
    - text: Cookbook
  - button "Administration" [expanded]:
    - text: Administration
    - img
  - link "Diagnostics":
    - /url: /diagnostics
    - img
    - text: Diagnostics
  - link "Logs":
    - /url: /logs
    - img
    - text: Logs
  - link "Analytics":
    - /url: /analytics
    - img
    - text: Analytics
  - link "Groups":
    - /url: /groups
    - img
    - text: Groups
  - link "Plugins":
    - /url: /plugins
    - img
    - text: Plugins
  - link "Connexions":
    - /url: /connections
    - img
    - text: Connexions
  - link "Monitoring":
    - /url: /monitoring
    - img
    - text: Monitoring
  - link "Security":
    - /url: /security
    - img
    - text: Security
  - link "Settings":
    - /url: /settings
    - img
    - text: Settings
  - text: Utilisateur
  - button "Déconnexion":
    - img
- main:
  - link "Retour au chat":
    - /url: /
    - img "ETHAN"
  - text: Ethan Ethan Hors ligne Ethan OS Classified Access
  - time: 2026-09-21 13:08:00 UTC
  - main:
    - heading "ETHAN" [level=1]
    - paragraph: Cognitive Operating System
    - text: Secure Authentication Terminal Operator ID
    - textbox "Operator ID":
      - /placeholder: Enter operator identifier
    - text: Password
    - textbox "Password":
      - /placeholder: ••••••••
    - checkbox "Remember device"
    - text: Remember device
    - button "Forgot credentials"
    - button "Login"
    - complementary:
      - text: NETWORK ONLINE AI CORE READY PLUGIN ENGINE ONLINE MEMORY SYNCED VECTOR DATABASE CONNECTED GPU AVAILABLE SECURITY LEVEL OMEGA SYSTEM CLOCK
      - time: 2026-09-21 13:08:00 UTC
      - text: ACTIVE SESSION NONE VERSION 2.4.1
    - paragraph: ETHAN Cognitive Operating System v2.4.1 — Authorized Personnel Only
    - paragraph: Unauthorized access is prohibited and may be prosecuted under applicable law.
- button "Ouvrir la boîte de réception":
  - img
- alert
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("ETHAN WebUI", () => {
  4  |   test("homepage loads", async ({ page }) => {
  5  |     await page.goto("/");
  6  |     await expect(page.locator(".kpi-card").first()).toBeVisible();
  7  |   });
  8  | 
  9  |   test("navigation to flux", async ({ page }) => {
  10 |     await page.goto("/");
  11 |     await page.click('a[href="/flux"]');
  12 |     await expect(page.locator("text=Flux")).toBeVisible();
  13 |   });
  14 | 
  15 |   test("navigation to agents", async ({ page }) => {
  16 |     await page.goto("/");
  17 |     await page.click('a[href="/agents"]');
  18 |     await expect(page.locator("text=Agents")).toBeVisible();
  19 |   });
  20 | 
  21 |   test("navigation to memory", async ({ page }) => {
  22 |     await page.goto("/");
  23 |     await page.click('a[href="/memory"]');
  24 |     await expect(page.locator("text=Mémoire")).toBeVisible();
  25 |   });
  26 | 
  27 |   test("navigation to skills", async ({ page }) => {
  28 |     await page.goto("/");
  29 |     await page.click('a[href="/skills"]');
  30 |     await expect(page.locator("text=Skills")).toBeVisible();
  31 |   });
  32 | 
  33 |   test("navigation to config", async ({ page }) => {
  34 |     await page.goto("/");
  35 |     await page.click('a[href="/config"]');
  36 |     await expect(page.locator(".config-section").first()).toBeVisible();
  37 |   });
  38 | 
  39 |   test("mission control opens", async ({ page }) => {
  40 |     await page.goto("/");
  41 |     await page.keyboard.press("Meta+t");
> 42 |     await expect(page.locator(".mission-overlay")).toBeVisible();
     |                                                    ^ Error: expect(locator).toBeVisible() failed
  43 |     await expect(page.locator(".mission-card").first()).toBeVisible();
  44 |   });
  45 | 
  46 |   test("command palette opens", async ({ page }) => {
  47 |     await page.goto("/");
  48 |     await page.keyboard.press("Meta+k");
  49 |     await expect(page.locator("text=Dashboard")).toBeVisible();
  50 |   });
  51 | });
  52 | 
```
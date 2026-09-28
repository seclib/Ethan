# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard Flow >> dashboard has top bar
- Location: tests/e2e/dashboard.spec.ts:14:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.top-bar')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.top-bar') with timeout 5000ms
  - waiting for locator('.top-bar')

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
  - time: 2026-09-21 13:08:40 UTC
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
      - time: 2026-09-21 13:08:40 UTC
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
  3  | test.describe("Dashboard Flow", () => {
  4  |   test("dashboard loads with KPI cards", async ({ page }) => {
  5  |     await page.goto("/");
  6  |     await expect(page.locator(".kpi-card").first()).toBeVisible();
  7  |   });
  8  | 
  9  |   test("dashboard has navigation sidebar", async ({ page }) => {
  10 |     await page.goto("/");
  11 |     await expect(page.locator(".sidebar")).toBeVisible();
  12 |   });
  13 | 
  14 |   test("dashboard has top bar", async ({ page }) => {
  15 |     await page.goto("/");
> 16 |     await expect(page.locator(".top-bar")).toBeVisible();
     |                                            ^ Error: expect(locator).toBeVisible() failed
  17 |   });
  18 | 
  19 |   test("command palette accessible via keyboard", async ({ page }) => {
  20 |     await page.goto("/");
  21 |     await page.keyboard.press("Meta+k");
  22 |     await expect(page.locator(".cmd-modal")).toBeVisible();
  23 |   });
  24 | 
  25 |   test("mission control accessible via keyboard", async ({ page }) => {
  26 |     await page.goto("/");
  27 |     await page.keyboard.press("Meta+t");
  28 |     await expect(page.locator(".mission-overlay")).toBeVisible();
  29 |   });
  30 | });
```
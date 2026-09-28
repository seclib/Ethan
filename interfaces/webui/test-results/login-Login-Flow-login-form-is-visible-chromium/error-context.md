# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.ts >> Login Flow >> login form is visible
- Location: tests/e2e/login.spec.ts:9:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('input[type=\'email\']')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('input[type=\'email\']') with timeout 5000ms
  - waiting for locator('input[type=\'email\']')

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
  - time: 2026-09-21 13:08:46 UTC
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
      - time: 2026-09-21 13:08:46 UTC
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
  3  | test.describe("Login Flow", () => {
  4  |   test("login page loads", async ({ page }) => {
  5  |     await page.goto("/login");
  6  |     await expect(page.locator("text=Connexion")).toBeVisible();
  7  |   });
  8  | 
  9  |   test("login form is visible", async ({ page }) => {
  10 |     await page.goto("/login");
> 11 |     await expect(page.locator("input[type='email']")).toBeVisible();
     |                                                       ^ Error: expect(locator).toBeVisible() failed
  12 |     await expect(page.locator("input[type='password']")).toBeVisible();
  13 |     await expect(page.locator("button[type='submit']")).toBeVisible();
  14 |   });
  15 | 
  16 |   test("login form validation", async ({ page }) => {
  17 |     await page.goto("/login");
  18 |     await page.click("button[type='submit']");
  19 |     // Should show validation errors or prevent submission
  20 |     await expect(page).toHaveURL(/\/login/);
  21 |   });
  22 | });
```
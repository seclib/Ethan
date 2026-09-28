# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> Chat >> shows empty state
- Location: tests/e2e/chat.spec.ts:13:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Commencez une conversation avec ETHAN')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('text=Commencez une conversation avec ETHAN') with timeout 5000ms
  - waiting for locator('text=Commencez une conversation avec ETHAN')

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
  - time: 2026-09-21 13:08:12 UTC
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
      - time: 2026-09-21 13:08:12 UTC
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
  3  | test.describe("Chat", () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto("/");
  6  |   });
  7  | 
  8  |   test("renders chat page", async ({ page }) => {
  9  |     await page.click("text=Chat");
  10 |     await expect(page.locator("h1")).toContainText("Chat");
  11 |   });
  12 | 
  13 |   test("shows empty state", async ({ page }) => {
  14 |     await page.click("text=Chat");
> 15 |     await expect(page.locator("text=Commencez une conversation avec ETHAN")).toBeVisible();
     |                                                                              ^ Error: expect(locator).toBeVisible() failed
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
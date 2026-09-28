# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard-v2.spec.ts >> Dashboard V2 — Navigation & Pages >> should have sidebar navigation visible
- Location: tests/e2e/dashboard-v2.spec.ts:46:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('aside')
Expected: visible
Error: strict mode violation: locator('aside') resolved to 2 elements:
    1) <aside aria-hidden="true" class="fixed right-0 top-0 z-drawer h-[100dvh] w-full border-l bg-background shadow-2xl transition-transform duration-300 translate-x-full">…</aside> aka getByText('InspectorSelect an item (')
    2) <aside class="hidden lg:flex flex-col w-[240px] border-l border-white/5 bg-white/[0.015]">…</aside> aka getByRole('complementary')

Call log:
  - Expect "toBeVisible" locator('aside') with timeout 5000ms
  - waiting for locator('aside')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [aria-hidden] [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]: Inspector
        - button [ref=e6] [cursor=pointer]
      - paragraph [ref=e14]: Select an item (Mission, Agent, Goal) to inspect its details.
    - navigation [ref=e15]:
      - generic [ref=e16]:
        - generic [ref=e17]:
          - img "ETHAN" [ref=e18]
          - generic [ref=e19]: ETHAN
        - button "Replier la sidebar" [ref=e20] [cursor=pointer]
      - generic [ref=e24]:
        - button "Nouveau chat" [ref=e25] [cursor=pointer]
        - button "Rechercher" [ref=e30] [cursor=pointer]:
          - generic [ref=e34]: Rechercher…
          - generic [ref=e35]: Ctrl K
      - generic [ref=e36]:
        - button "Projets" [ref=e38] [cursor=pointer]
        - generic [ref=e45]:
          - link "Agents" [ref=e46] [cursor=pointer]:
            - /url: /agents
          - generic [ref=e51]:
            - button "Pilotage" [expanded] [ref=e52] [cursor=pointer]
            - generic [ref=e57]:
              - link "Missions" [ref=e58] [cursor=pointer]:
                - /url: /missions
              - link "Calendar" [ref=e64] [cursor=pointer]:
                - /url: /calendar
              - link "Notes" [ref=e68] [cursor=pointer]:
                - /url: /notes
              - link "Inbox" [ref=e73] [cursor=pointer]:
                - /url: /inbox
              - link "Deep Research" [ref=e78] [cursor=pointer]:
                - /url: /research
              - link "Cookbook" [ref=e88] [cursor=pointer]:
                - /url: /cookbook
          - generic [ref=e92]:
            - button "Administration" [expanded] [ref=e93] [cursor=pointer]
            - generic [ref=e98]:
              - link "Diagnostics" [ref=e99] [cursor=pointer]:
                - /url: /diagnostics
              - link "Logs" [ref=e103] [cursor=pointer]:
                - /url: /logs
              - link "Analytics" [ref=e108] [cursor=pointer]:
                - /url: /analytics
              - link "Groups" [ref=e112] [cursor=pointer]:
                - /url: /groups
              - link "Plugins" [ref=e118] [cursor=pointer]:
                - /url: /plugins
              - link "Connexions" [ref=e122] [cursor=pointer]:
                - /url: /connections
              - link "Monitoring" [ref=e131] [cursor=pointer]:
                - /url: /monitoring
              - link "Security" [ref=e136] [cursor=pointer]:
                - /url: /security
        - link "Settings" [ref=e142] [cursor=pointer]:
          - /url: /settings
      - generic [ref=e147]:
        - generic "Utilisateur" [ref=e148] [cursor=pointer]:
          - generic [aria-hidden] [ref=e149]: U
        - button "Déconnexion" [ref=e152] [cursor=pointer]
    - main [ref=e156]:
      - generic [ref=e157]:
        - generic [ref=e158]:
          - link "Retour au chat" [ref=e159] [cursor=pointer]:
            - /url: /
            - img "ETHAN" [ref=e160]
          - generic [ref=e161]: Ethan
          - generic [aria-hidden] [ref=e162]: /
          - generic [ref=e163]: Ethan
        - generic [ref=e164]: Hors ligne
      - generic [ref=e170]:
        - generic [ref=e172]:
          - generic [ref=e173]:
            - generic [ref=e174]: Ethan OS
            - generic [ref=e176]: Classified Access
          - time [ref=e179]: 2026-09-21 13:08:29 UTC
        - main [ref=e180]:
          - generic [ref=e182]:
            - generic [ref=e184]:
              - generic [ref=e185]:
                - generic [aria-hidden] [ref=e187]: ▄▄▓▓?▓▓▓?▄▄ ▄▓#▓▓▓%▓▓?▓▓▓!▓▄ ▐▓▓9▓7▓!▓?▓▓1▓▓▓▓▌ ▓▓▓▓▓#▓▓▓▓?▓▓▓▓!▓▓▓▓ ▓▓▓▓▓▓9▓▓▓▓▓▓x▓▓▓▓▓▓▓ ▓▓ !? ▓▓▓▓ ?! ▓▓ ▓▓▓ 97 ▓▓ 31 ▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓ /\ ▓▓▓▓▓▓▓▓▓ ▓▓M▓▓▓x▓▓▓▓T▓▓▓▓▓Q▓▓▓▓ ▓▓▓9▓▓▓▓▓?▓▓▓▓▓!▓▓▓▓ ▀▓▓▓▓?▓▓▓▓▓▓▓?▓▓▓▀ ▐▓!▓▓?▓▓!▓▓?▓▓▌ ▀▓▓?▓▓▓▓?▓▓▀
                - heading "ETHAN" [level=1] [ref=e188]
                - paragraph [ref=e189]: Cognitive Operating System
                - generic [ref=e190]: Secure Authentication Terminal
              - generic [ref=e195]:
                - generic [ref=e196]:
                  - generic [ref=e197]: Operator ID
                  - textbox "Operator ID" [ref=e198]:
                    - /placeholder: Enter operator identifier
                - generic [ref=e199]:
                  - generic [ref=e200]: Password
                  - textbox "Password" [ref=e201]:
                    - /placeholder: ••••••••
                - generic [ref=e202]:
                  - generic [ref=e203] [cursor=pointer]:
                    - checkbox "Remember device" [ref=e204]
                    - generic [ref=e205]: Remember device
                  - button "Forgot credentials" [ref=e206] [cursor=pointer]
                - button "Authenticating" [disabled] [ref=e207]
            - complementary [ref=e213]:
              - generic [ref=e214]:
                - generic [ref=e215]:
                  - generic [ref=e216]:
                    - generic [ref=e217]: NETWORK
                    - generic [ref=e218]: ONLINE
                  - generic [ref=e221]:
                    - generic [ref=e222]: AI CORE
                    - generic [ref=e223]: READY
                  - generic [ref=e226]:
                    - generic [ref=e227]: PLUGIN ENGINE
                    - generic [ref=e228]: ONLINE
                  - generic [ref=e231]:
                    - generic [ref=e232]: MEMORY
                    - generic [ref=e233]: SYNCED
                  - generic [ref=e236]:
                    - generic [ref=e237]: VECTOR DATABASE
                    - generic [ref=e238]: CONNECTED
                  - generic [ref=e241]:
                    - generic [ref=e242]: GPU
                    - generic [ref=e243]: AVAILABLE
                  - generic [ref=e246]:
                    - generic [ref=e247]: SECURITY LEVEL
                    - generic [ref=e248]: OMEGA
                - generic [ref=e253]:
                  - generic [ref=e254]: SYSTEM CLOCK
                  - time [ref=e255]: 2026-09-21 13:08:29 UTC
                - generic [ref=e257]:
                  - generic [ref=e258]: ACTIVE SESSION
                  - generic [ref=e259]: NONE
                - generic [ref=e261]:
                  - generic [ref=e262]: VERSION
                  - generic [ref=e263]: 2.4.1
          - generic [ref=e264]:
            - paragraph [ref=e265]: ETHAN Cognitive Operating System v2.4.1 — Authorized Personnel Only
            - paragraph [ref=e266]: Unauthorized access is prohibited and may be prosecuted under applicable law.
  - button "Ouvrir la boîte de réception" [ref=e267] [cursor=pointer]
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
  30  |     await expect(page.locator("h1")).toContainText("Skills Lab");
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
> 49  |     await expect(page.locator("aside")).toBeVisible();
      |                                         ^ Error: expect(locator).toBeVisible() failed
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
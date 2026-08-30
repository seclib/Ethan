# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard-v2.spec.ts >> Dashboard V2 — Navigation & Pages >> should navigate between pages via sidebar
- Location: tests/e2e/dashboard-v2.spec.ts:58:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('a[href="/goals"]')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - complementary [ref=e3]:
    - generic [ref=e4]:
      - generic [ref=e5]: Inspector
      - button [ref=e6] [cursor=pointer]
    - paragraph [ref=e14]: Select an item (Mission, Agent, Goal) to inspect its details.
  - generic [ref=e15]:
    - button "Search (Ctrl+K)" [ref=e16] [cursor=pointer]
    - link "Chat" [ref=e20] [cursor=pointer]:
      - /url: /
    - link "Chat" [ref=e23] [cursor=pointer]:
      - /url: /
    - link "Workspace" [ref=e26] [cursor=pointer]:
      - /url: /workspace
    - link "Calendar" [ref=e32] [cursor=pointer]:
      - /url: /calendar
    - link "Notes" [ref=e35] [cursor=pointer]:
      - /url: /notes
    - link "Knowledge" [ref=e39] [cursor=pointer]:
      - /url: /knowledge
    - link "Missions" [ref=e44] [cursor=pointer]:
      - /url: /missions
    - link "Agents" [ref=e49] [cursor=pointer]:
      - /url: /agents
    - link "Tools" [ref=e53] [cursor=pointer]:
      - /url: /tools
    - link "Providers" [ref=e57] [cursor=pointer]:
      - /url: /providers
    - link "Models" [ref=e62] [cursor=pointer]:
      - /url: /models
    - link "Settings" [ref=e67] [cursor=pointer]:
      - /url: /settings
  - navigation [ref=e71]:
    - generic [ref=e72]:
      - button "Toggle sidebar" [ref=e73] [cursor=pointer]
      - generic [ref=e75]:
        - img "ETHAN" [ref=e76]
        - generic [ref=e77]: ETHAN
    - generic [ref=e78]:
      - generic [ref=e79]: Navigation
      - link "Workspace" [ref=e80] [cursor=pointer]:
        - /url: /workspace
      - link "Calendar" [ref=e87] [cursor=pointer]:
        - /url: /calendar
      - link "Notes" [ref=e91] [cursor=pointer]:
        - /url: /notes
      - link "Knowledge" [ref=e96] [cursor=pointer]:
        - /url: /knowledge
      - link "Missions" [ref=e102] [cursor=pointer]:
        - /url: /missions
      - link "Agents" [ref=e108] [cursor=pointer]:
        - /url: /agents
      - link "Skills" [ref=e113] [cursor=pointer]:
        - /url: /skills
      - link "Tools" [ref=e117] [cursor=pointer]:
        - /url: /tools
      - link "Inbox" [ref=e122] [cursor=pointer]:
        - /url: /inbox
      - link "Research" [ref=e127] [cursor=pointer]:
        - /url: /research
      - link "Cookbook" [ref=e137] [cursor=pointer]:
        - /url: /cookbook
      - generic [ref=e141]: Système
      - link "Providers" [ref=e142] [cursor=pointer]:
        - /url: /providers
      - link "Models" [ref=e148] [cursor=pointer]:
        - /url: /models
      - link "Settings" [ref=e153] [cursor=pointer]:
        - /url: /settings
      - link "Security" [ref=e158] [cursor=pointer]:
        - /url: /security
    - generic [ref=e163]:
      - generic [ref=e164] [cursor=pointer]:
        - generic [ref=e165]: E
        - generic [ref=e166]: User
      - link "Settings" [ref=e168] [cursor=pointer]:
        - /url: /settings
  - main [ref=e172]:
    - generic [ref=e174]:
      - generic [ref=e176]:
        - generic [ref=e177]:
          - generic [ref=e178]: Ethan OS
          - generic [ref=e180]: Classified Access
        - time [ref=e183]: 2026-08-26 07:55:14 UTC
      - main [ref=e184]:
        - generic [ref=e186]:
          - generic [ref=e188]:
            - generic [ref=e189]:
              - img "ETHAN" [ref=e191]
              - heading "ETHAN" [level=1] [ref=e192]
              - paragraph [ref=e193]: Cognitive Operating System
              - generic [ref=e194]: Secure Authentication Terminal
            - generic [ref=e199]:
              - generic [ref=e200]:
                - generic [ref=e201]: Operator ID
                - textbox "Operator ID" [ref=e202]:
                  - /placeholder: Enter operator identifier
              - generic [ref=e203]:
                - generic [ref=e204]: Password
                - textbox "Password" [ref=e205]:
                  - /placeholder: ••••••••
              - generic [ref=e206]:
                - generic [ref=e207] [cursor=pointer]:
                  - checkbox "Remember device" [ref=e208]
                  - generic [ref=e209]: Remember device
                - button "Forgot credentials" [ref=e210] [cursor=pointer]
              - button [disabled] [ref=e211]
          - complementary [ref=e217]:
            - generic [ref=e218]:
              - generic [ref=e219]:
                - generic [ref=e220]:
                  - generic [ref=e221]: NETWORK
                  - generic [ref=e222]: ONLINE
                - generic [ref=e225]:
                  - generic [ref=e226]: AI CORE
                  - generic [ref=e227]: READY
                - generic [ref=e230]:
                  - generic [ref=e231]: PLUGIN ENGINE
                  - generic [ref=e232]: ONLINE
                - generic [ref=e235]:
                  - generic [ref=e236]: MEMORY
                  - generic [ref=e237]: SYNCED
                - generic [ref=e240]:
                  - generic [ref=e241]: VECTOR DATABASE
                  - generic [ref=e242]: CONNECTED
                - generic [ref=e245]:
                  - generic [ref=e246]: GPU
                  - generic [ref=e247]: AVAILABLE
                - generic [ref=e250]:
                  - generic [ref=e251]: SECURITY LEVEL
                  - generic [ref=e252]: OMEGA
              - generic [ref=e257]:
                - generic [ref=e258]: SYSTEM CLOCK
                - time [ref=e259]: 2026-08-26 07:55:14 UTC
              - generic [ref=e261]:
                - generic [ref=e262]: ACTIVE SESSION
                - generic [ref=e263]: NONE
              - generic [ref=e265]:
                - generic [ref=e266]: VERSION
                - generic [ref=e267]: 2.4.1
        - generic [ref=e268]:
          - paragraph [ref=e269]: ETHAN Cognitive Operating System v2.4.1 — Authorized Personnel Only
          - paragraph [ref=e270]: Unauthorized access is prohibited and may be prosecuted under applicable law.
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
> 61  |     await page.locator('a[href="/goals"]').click();
      |                                            ^ Error: locator.click: Test timeout of 30000ms exceeded.
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
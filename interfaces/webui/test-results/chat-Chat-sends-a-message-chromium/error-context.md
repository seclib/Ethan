# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> Chat >> sends a message
- Location: tests/e2e/chat.spec.ts:18:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[placeholder="Message ETHAN..."]')

```

# Page snapshot

```yaml
- generic [active] [ref=f1e1]:
  - generic [ref=f1e2]:
    - complementary [aria-hidden] [ref=f1e3]:
      - generic [ref=f1e4]:
        - generic [ref=f1e5]: Inspector
        - button [ref=f1e6] [cursor=pointer]
      - paragraph [ref=f1e14]: Select an item (Mission, Agent, Goal) to inspect its details.
    - navigation [ref=f1e15]:
      - generic [ref=f1e16]:
        - generic [ref=f1e17]:
          - img "ETHAN" [ref=f1e18]
          - generic [ref=f1e19]: ETHAN
        - button "Replier la sidebar" [ref=f1e20] [cursor=pointer]
      - generic [ref=f1e24]:
        - button "Nouveau chat" [ref=f1e25] [cursor=pointer]
        - button "Rechercher" [ref=f1e30] [cursor=pointer]:
          - generic [ref=f1e34]: Rechercher…
          - generic [ref=f1e35]: Ctrl K
      - generic [ref=f1e36]:
        - button "Projets" [ref=f1e38] [cursor=pointer]
        - generic [ref=f1e45]:
          - link "Agents" [ref=f1e46] [cursor=pointer]:
            - /url: /agents
          - generic [ref=f1e51]:
            - button "Pilotage" [expanded] [ref=f1e52] [cursor=pointer]
            - generic [ref=f1e57]:
              - link "Missions" [ref=f1e58] [cursor=pointer]:
                - /url: /missions
              - link "Calendar" [ref=f1e64] [cursor=pointer]:
                - /url: /calendar
              - link "Notes" [ref=f1e68] [cursor=pointer]:
                - /url: /notes
              - link "Inbox" [ref=f1e73] [cursor=pointer]:
                - /url: /inbox
              - link "Deep Research" [ref=f1e78] [cursor=pointer]:
                - /url: /research
              - link "Cookbook" [ref=f1e88] [cursor=pointer]:
                - /url: /cookbook
          - generic [ref=f1e92]:
            - button "Administration" [expanded] [ref=f1e93] [cursor=pointer]
            - generic [ref=f1e98]:
              - link "Diagnostics" [ref=f1e99] [cursor=pointer]:
                - /url: /diagnostics
              - link "Logs" [ref=f1e103] [cursor=pointer]:
                - /url: /logs
              - link "Analytics" [ref=f1e108] [cursor=pointer]:
                - /url: /analytics
              - link "Groups" [ref=f1e112] [cursor=pointer]:
                - /url: /groups
              - link "Plugins" [ref=f1e118] [cursor=pointer]:
                - /url: /plugins
              - link "Connexions" [ref=f1e122] [cursor=pointer]:
                - /url: /connections
              - link "Monitoring" [ref=f1e131] [cursor=pointer]:
                - /url: /monitoring
              - link "Security" [ref=f1e136] [cursor=pointer]:
                - /url: /security
        - link "Settings" [ref=f1e142] [cursor=pointer]:
          - /url: /settings
      - generic [ref=f1e147]:
        - generic "Utilisateur" [ref=f1e148] [cursor=pointer]:
          - generic [aria-hidden] [ref=f1e149]: U
        - button "Déconnexion" [ref=f1e152] [cursor=pointer]
    - main [ref=f1e156]:
      - generic [ref=f1e157]:
        - generic [ref=f1e158]:
          - link "Retour au chat" [ref=f1e159] [cursor=pointer]:
            - /url: /
            - img "ETHAN" [ref=f1e160]
          - generic [ref=f1e161]: Ethan
          - generic [aria-hidden] [ref=f1e162]: /
          - generic [ref=f1e163]: Ethan
        - generic [ref=f1e164]: Hors ligne
      - generic [ref=f1e170]:
        - generic [ref=f1e172]:
          - generic [ref=f1e173]:
            - generic [ref=f1e174]: Ethan OS
            - generic [ref=f1e176]: Classified Access
          - time [ref=f1e179]: 2026-09-21 13:08:39 UTC
        - main [ref=f1e180]:
          - generic [ref=f1e182]:
            - generic [ref=f1e184]:
              - generic [ref=f1e185]:
                - generic [aria-hidden] [ref=f1e187]: ▄▄▓▓?▓▓▓?▄▄ ▄▓#▓▓▓%▓▓?▓▓▓!▓▄ ▐▓▓9▓7▓!▓?▓▓1▓▓▓▓▌ ▓▓▓▓▓#▓▓▓▓?▓▓▓▓!▓▓▓▓ ▓▓▓▓▓▓9▓▓▓▓▓▓x▓▓▓▓▓▓▓ ▓▓ !? ▓▓▓▓ ?! ▓▓ ▓▓▓ 97 ▓▓ 31 ▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓ /\ ▓▓▓▓▓▓▓▓▓ ▓▓M▓▓▓x▓▓▓▓T▓▓▓▓▓Q▓▓▓▓ ▓▓▓9▓▓▓▓▓?▓▓▓▓▓!▓▓▓▓ ▀▓▓▓▓?▓▓▓▓▓▓▓?▓▓▓▀ ▐▓!▓▓?▓▓!▓▓?▓▓▌ ▀▓▓?▓▓▓▓?▓▓▀
                - heading "ETHAN" [level=1] [ref=f1e188]
                - paragraph [ref=f1e189]: Cognitive Operating System
                - generic [ref=f1e190]: Secure Authentication Terminal
              - generic [ref=f1e195]:
                - generic [ref=f1e196]:
                  - generic [ref=f1e197]: Operator ID
                  - textbox "Operator ID" [ref=f1e198]:
                    - /placeholder: Enter operator identifier
                - generic [ref=f1e199]:
                  - generic [ref=f1e200]: Password
                  - textbox "Password" [ref=f1e201]:
                    - /placeholder: ••••••••
                - generic [ref=f1e202]:
                  - generic [ref=f1e203] [cursor=pointer]:
                    - checkbox "Remember device" [ref=f1e204]
                    - generic [ref=f1e205]: Remember device
                  - button "Forgot credentials" [ref=f1e206] [cursor=pointer]
                - button "Login" [ref=f1e207] [cursor=pointer]
            - complementary [ref=f1e209]:
              - generic [ref=f1e210]:
                - generic [ref=f1e211]:
                  - generic [ref=f1e212]:
                    - generic [ref=f1e213]: NETWORK
                    - generic [ref=f1e214]: ONLINE
                  - generic [ref=f1e217]:
                    - generic [ref=f1e218]: AI CORE
                    - generic [ref=f1e219]: READY
                  - generic [ref=f1e222]:
                    - generic [ref=f1e223]: PLUGIN ENGINE
                    - generic [ref=f1e224]: ONLINE
                  - generic [ref=f1e227]:
                    - generic [ref=f1e228]: MEMORY
                    - generic [ref=f1e229]: SYNCED
                  - generic [ref=f1e232]:
                    - generic [ref=f1e233]: VECTOR DATABASE
                    - generic [ref=f1e234]: CONNECTED
                  - generic [ref=f1e237]:
                    - generic [ref=f1e238]: GPU
                    - generic [ref=f1e239]: AVAILABLE
                  - generic [ref=f1e242]:
                    - generic [ref=f1e243]: SECURITY LEVEL
                    - generic [ref=f1e244]: OMEGA
                - generic [ref=f1e249]:
                  - generic [ref=f1e250]: SYSTEM CLOCK
                  - time [ref=f1e251]: 2026-09-21 13:08:39 UTC
                - generic [ref=f1e253]:
                  - generic [ref=f1e254]: ACTIVE SESSION
                  - generic [ref=f1e255]: NONE
                - generic [ref=f1e257]:
                  - generic [ref=f1e258]: VERSION
                  - generic [ref=f1e259]: 2.4.1
          - generic [ref=f1e260]:
            - paragraph [ref=f1e261]: ETHAN Cognitive Operating System v2.4.1 — Authorized Personnel Only
            - paragraph [ref=f1e262]: Unauthorized access is prohibited and may be prosecuted under applicable law.
  - button "Ouvrir la boîte de réception" [ref=f1e263] [cursor=pointer]
  - alert [ref=f1e267]
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
  15 |     await expect(page.locator("text=Commencez une conversation avec ETHAN")).toBeVisible();
  16 |   });
  17 | 
  18 |   test("sends a message", async ({ page }) => {
  19 |     await page.click("text=Chat");
> 20 |     await page.fill('input[placeholder="Message ETHAN..."]', "Bonjour");
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  21 |     await page.click("button:has(svg)");
  22 |     await expect(page.locator(".space-y-4 > div").first()).toContainText("Bonjour");
  23 |   });
  24 | });
```
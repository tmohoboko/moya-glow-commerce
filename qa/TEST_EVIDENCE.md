# Test evidence

Date: 2026-09-26. Executor: Codex / Playwright 1.63.0.
Target: local Vite production preview, http://127.0.0.1:4173.
Browser: installed Chromium 148.0.7778.96 (explicit executable override).
Viewports: desktop 1280×720 and mobile 375×812.

Commands executed:

```sh
npm install
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/home/tmdev012/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome npm test
```

Install passed (20 packages, zero reported vulnerabilities). Build passed with Vite 7.3.6. No lint script exists.
Final suite: **10 passed in 10.0 seconds**. Initial run: 9 passed, 1 failed due to category label ambiguity; fixed by explicitly naming the select and reran all checks successfully.

| ID | Executed check | Result |
|---|---|---|
| SMOKE-001 | Homepage heading visible; no captured page errors | PASS |
| SMOKE-002 | 30 product cards and usable detail page | PASS |
| SMOKE-003 | Vitamin C search returns one product; no-result state | PASS |
| SMOKE-004 | Makeup filter returns eight matching products | PASS |
| SMOKE-005 | Add item and retain cart after refresh | PASS |
| SMOKE-006 | Increase to two and decrease to one | PASS |
| SMOKE-007 | Remove item; empty bag and zero count | PASS |
| SMOKE-008 | Subtotal 149 → 298 → 427 with second product | PASS |
| SMOKE-009 | Mobile catalogue and cart visible; no horizontal overflow | PASS |
| SMOKE-010 | Unknown page/product and home recovery | PASS |

Machine results: [smoke-results.json](smoke-results.json).
Screenshots: [mobile](mobile-home.png), [desktop](desktop-home.png). Mobile screenshot visually inspected for clipping and structure.

The current default Chromium download was slow and reset once; stopped it after the existing installed Chromium completed all tests. For a fresh machine use `npx playwright install chromium`, or set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an existing Chrome binary.

Not executed: production smoke tests, Safari/Firefox, real-device checks, manual exploratory session, accessibility audit. Screenshots are initial QA evidence, not full design acceptance.

# Test evidence

## Current patch execution — 2026-10-09

Fresh npm ci and Vite production build: PASS. Local Chromium regression: **16/16 PASS**, zero unexpected/skipped/flaky results. [Machine report](release-local-results.json) · [Execution details and tested source fingerprints](FRONTEND_RELEASE_PATCH.md).

Current screenshots: [mobile](release-local/mobile-home.png), [desktop](release-local/desktop-home.png). Reviewed visually for clipping and branding. Hosted regression and full manual acceptance are pending.

## Prior evidence index — reviewed 2026-10-09

- [L Beauty catalogue patch](LBEAUTY_CATALOGUE_PATCH.md): 2026-09-28 local build PASS and 12/12 local Playwright PASS.
- [L Beauty artwork verification](LBEAUTY_SERVICE_ARTWORK.md): 2026-09-30 local build PASS and 13/13 local Playwright PASS; limited desktop/mobile/cart visual review.
- [Prior machine report](smoke-results.json): starts 2026-09-30T16:55:45.502Z, production preview on port 4173, 13 passed, zero unexpected/skipped/flaky results, approximately 16.1 seconds. This replaces the older report; it is not a hosted run.
- Final branding and vector-wordmark commits were made after this recorded run. A fresh run is required to certify application commit `0089e4e4da04141f53a0ab803c5c2495e301c543`.
- Hosted L Beauty, completed manual exploratory and cross-browser acceptance remain unverified. See [release acceptance](RELEASE_ACCEPTANCE.md).

The prior index describes earlier runs; it is preserved for traceability. The current patch execution is recorded above.

## Historical Moya Glow execution — 2026-09-26

The following records the earlier 30-product application and its hosted run. Current JSON/screenshots were later refreshed for L Beauty and must not be used as machine proof of this historical run.

Date: 2026-09-26. Executor: Codex / Playwright 1.63.0.
Historical production target: https://moya-glow-commerce.vercel.app (public production).
Deployed application commit: a400eff043587ce6ee6050c6c915ac27ff55b3a1.
Deployment: dpl_EyLyux87MruETfA3vbtgGgJwWUvn.
Earlier local target: http://127.0.0.1:4173.
Browser: installed Chromium 148.0.7778.96 (explicit executable override).
Viewports: desktop 1280×720 and mobile 375×812.

Commands executed:

```sh
npm install
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/home/tmdev012/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome npm test
```

Install passed (20 packages, zero reported vulnerabilities). Build passed with Vite 7.3.6. No lint script exists.
Production suite: **10 passed in 14.4 seconds**. Earlier local suite: **10 passed in 10.0 seconds**. Initial run: 9 passed, 1 failed due to category label ambiguity; fixed by explicitly naming the select and reran all checks successfully.

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

Historical machine results: [smoke-results.json at the release-evidence commit](https://github.com/tmohoboko/moya-glow-commerce/blob/2c8260fe86e3481be07648973b1d866482f5fb26/qa/smoke-results.json).
Historical screenshots: [mobile](https://github.com/tmohoboko/moya-glow-commerce/blob/2c8260fe86e3481be07648973b1d866482f5fb26/qa/mobile-home.png), [desktop](https://github.com/tmohoboko/moya-glow-commerce/blob/2c8260fe86e3481be07648973b1d866482f5fb26/qa/desktop-home.png). Mobile screenshot visually inspected for clipping and structure.

The current default Chromium download was slow and reset once; stopped it after the existing installed Chromium completed all tests. For a fresh machine use `npx playwright install chromium`, or set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an existing Chrome binary.

Not executed: Safari/Firefox, real-device checks, manual exploratory session, accessibility audit. Screenshots are initial QA evidence, not full design acceptance.

## Production execution

```sh
BASE_URL=https://moya-glow-commerce.vercel.app PLAYWRIGHT_CHROMIUM_EXECUTABLE=/home/tmdev012/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome npm test
```

All SMOKE-001 through SMOKE-010 checks above were rerun against production and passed. At the historical release-evidence commit, the JSON report and both screenshots reflected that production run. Current files have since been replaced with local L Beauty evidence. Direct requests to unknown page/product routes recovered correctly through the Vercel SPA rewrite. No login or deployment protection bypass was needed.

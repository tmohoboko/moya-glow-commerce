# L Beauty release acceptance

## Current decision — 2026-10-09

**HOLD full release sign-off.** Local storefront demonstration is supported by recorded evidence; current production storefront and integrated backend acceptance remain unverified. This review updates documentation only and does not certify a new build, test run or deployment.

Latest reviewed application commit: [0089e4e4da04141f53a0ab803c5c2495e301c543](https://github.com/tmohoboko/moya-glow-commerce/commit/0089e4e4da04141f53a0ab803c5c2495e301c543), 2026-09-30. Subsequent documentation commits do not change application behavior.

| Gate | Recorded evidence | Current acceptance |
|---|---|---|
| Catalogue | 46 services, 11 categories, price/source review; [catalogue patch](LBEAUTY_CATALOGUE_PATCH.md) | Implemented |
| Artwork / branding | 46 individual SVG cards, L Beauty hero, vector header/footer wordmark; [artwork evidence](LBEAUTY_SERVICE_ARTWORK.md) | Implemented; final branding commits require fresh regression |
| Build | Local Vite build PASS recorded for catalogue/artwork patches | Latest application source build pending |
| Local Playwright | [Committed report](smoke-results.json): 13/13 PASS, 2026-09-30, local production preview, zero failures/skips/flaky results | Recorded run predates final branding/vector changes |
| Hosted storefront | Historical 10/10 PASS on 2026-09-26 for Moya Glow | L Beauty deployment identity and hosted regression pending |
| Manual QA | Catalogue/price review and desktop/mobile/cart visual inspection documented | Full manual acceptance not verified |
| Cross-browser / real devices | Chromium checks only; mobile viewport is emulated | Pending |
| Backend integration | Separate enterprise branch records local API/Docker health/readiness passes | Persistent HTTPS backend and hosted E2E pending |

### Manual evidence reconciliation

Connected Google Drive searches for L Beauty, Moya, Playwright, storefront and QA evidence filenames did not locate relevant project QA records. This is an evidence gap, not proof that no manual testing occurred.

On the separate enterprise prototype branch, [Cycle 01 test cases](https://github.com/tmohoboko/moya-glow-commerce/blob/port/adfund-enterprise-prototype/qa/cycle-01/TEST_CASES.csv) still mark all 20 cases NOT RUN; its [assessment](https://github.com/tmohoboko/moya-glow-commerce/blob/port/adfund-enterprise-prototype/qa/cycle-01/RELEASE_ASSESSMENT.md) records zero executions and PENDING. Do not count these as completed passes. Reconcile dated execution records and screenshots before manual sign-off.

### Required release gates

- [ ] Record a fresh build and complete regression run against the reviewed application source, with commit SHA and target.
- [ ] Confirm the L Beauty production deployment identity, then run the complete hosted storefront suite.
- [ ] Record completed manual exploratory acceptance, responsive checks, supported-browser coverage and defect dispositions.
- [ ] For integrated enterprise acceptance, provision persistent HTTPS FastAPI hosting, verify health/readiness and frontend API connectivity, and run hosted catalogue/auth/admin E2E checks.

The backend belongs to `port/adfund-enterprise-prototype`, not the static `main` storefront. Its [release evidence](https://github.com/tmohoboko/moya-glow-commerce/blob/port/adfund-enterprise-prototype/docs/RELEASE_EVIDENCE.md) identifies the public enterprise host as a static fallback with unavailable account/admin APIs. Local backend passes do not certify hosted functionality. Backend hosting blocks integrated release, while the static catalogue can be assessed separately with its explicit no-booking/no-orders/no-payments scope.

Automatic GitHub deployment is not enabled according to the recorded evidence; a push alone is not deployment confirmation. No deployment or hosting change was performed in this review.

## Historical Moya Glow acceptance — 2026-09-26

The following is retained as the acceptance record for the earlier 30-product release. It does not sign off the current L Beauty application.

2026-09-26 — Local acceptance PASS; production release PASS.

- [x] Source exists at repository root: React + Vite, no backend.
- [x] Exactly 30 mock products, local placeholder images and descriptions.
- [x] Homepage, catalogue, detail pages, search and category filtering.
- [x] Add, increase/decrease, remove, subtotal, persistent and empty cart.
- [x] Responsive desktop/mobile layout and graceful unknown routes.
- [x] npm install succeeds; audit reports zero vulnerabilities.
- [x] npm run build succeeds.
- [x] Ten automated smoke checks pass against production preview.
- [x] Valid Git HEAD and main branch.
- [x] README and QA artifacts present; shipping-kit directories preserved.
- [x] Staged content inspected and scanned for obvious secrets.
- [x] Public GitHub repository created and main pushed.
- [x] Vercel production deployment and all ten production smoke tests.
- [ ] Manual exploratory and cross-browser QA.

## Published release

- GitHub: https://github.com/tmohoboko/moya-glow-commerce (public).
- GitHub CLI: authenticated as tmohoboko; main pushed and remote SHA verified.
- Vercel CLI: authenticated as tmohoboko; project tmdev/moya-glow-commerce.
- Production: https://moya-glow-commerce.vercel.app
- Deployment URL: https://moya-glow-commerce-mcp52s7vx-tmdev.vercel.app
- Deployment ID: dpl_EyLyux87MruETfA3vbtgGgJwWUvn; state READY; target production.
- Application commit: a400eff043587ce6ee6050c6c915ac27ff55b3a1. Subsequent release-evidence commit changes documentation/results only.
- Vercel cloud build succeeded. Public production smoke suite: 10/10 passed in 14.4 seconds.

## Remaining integration limitation

Vercel's automatic GitHub connection failed during deployment and again with `npx vercel git connect https://github.com/tmohoboko/moya-glow-commerce --yes`. This does not block the deployed site or CLI releases. Automatic deploy-on-push is not enabled; enabling it requires resolving the Vercel GitHub integration access. No release-blocking authorization issues remain.

## QA limitations

No open application defects identified by the executed smoke suite. One accessible-label defect was fixed and retested. Local and production Chromium were tested. Real payments and checkout are intentionally excluded; the bag explicitly identifies the demo limitation.

# L Beauty Storefront

L Beauty service catalogue and shopping-bag demo, maintained in the original Moya Glow repository. No booking, orders or payments are processed.

## Stack

React, JavaScript, Vite, responsive CSS, Playwright, Git, and Vercel deployment configuration. The static storefront on `main` requires no backend or runtime secrets. The separate enterprise prototype branch contains FastAPI integration; its hosted backend acceptance remains pending.

## Features

46 services across 11 categories; individual SVG service artwork; L Beauty hero and vector wordmark; searchable and filterable catalogue; service detail pages; persistent shopping bag; quantity controls, removal, subtotal in ZAR, empty states, and graceful unknown routes. Special Effects and Bridal retain “From” pricing throughout cards, details and bag; totals are base estimates. Cart storage is best-effort when browser storage is unavailable. Quantities are capped at 99 per product.

## Local development

```sh
npm install
npm run dev
```

## Production build

```sh
npm run build
npm run preview
```

## Testing

```sh
npx playwright install chromium
npm test
```

Tests run against the production preview on port 4173. To test a deployed site, run `BASE_URL=https://your-site.vercel.app npm test`. Results are written to `qa/smoke-results.json`; mobile and desktop screenshots are saved in `qa/`. No lint script is configured. If using an existing Chromium installation, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/absolute/path/to/chrome` when running `npm test`.

## Deployment

Vercel settings: Vite, build command `npm run build`, output directory `dist`. SPA rewrites are provided in `vercel.json`.

```sh
npx --yes vercel@61.1.0 login
npx --yes vercel@61.1.0 link --yes --project moya-glow-commerce --scope tmdev
npm run release:vercel
```

Production: https://moya-glow-commerce.vercel.app

Repository: https://github.com/tmohoboko/moya-glow-commerce

The original Moya Glow production deployment is recorded for 2026-09-26. Deployment of the subsequent L Beauty patches has not been confirmed. Automatic GitHub deployments are not connected according to the recorded release evidence; pushing `main` alone does not deploy. The existing release mechanism is `npx vercel --prod --yes`. Deployment evidence and pending gates are recorded in [release acceptance](qa/RELEASE_ACCEPTANCE.md).

## QA status

Release patch: 2026-10-09. **Full release sign-off: HOLD.**

- Current patch: clean npm ci and production build **PASS**; local Playwright **16/16 PASS**, zero failures, skips or flaky results. New checks cover page titles/history, 320/375/768px layouts and vector branding. [Executed patch evidence](qa/FRONTEND_RELEASE_PATCH.md) · [Current machine report](qa/release-local-results.json).
- Historical production Chromium result: **10/10 PASS** on 2026-09-26 for the earlier 30-product Moya Glow release; not current L Beauty hosted acceptance.
- Limited visual review is documented. Completed manual exploratory, cross-browser and real-device acceptance is not verified. Relevant Google Drive QA evidence was not found during the 2026-10-09 connected search.
- Pending: deployment identity and hosted regression, completed manual acceptance; persistent HTTPS FastAPI hosting and hosted integration checks for the enterprise scope.

Evidence: [test evidence](qa/TEST_EVIDENCE.md), [catalogue patch](qa/LBEAUTY_CATALOGUE_PATCH.md), [artwork verification](qa/LBEAUTY_SERVICE_ARTWORK.md), [machine report](qa/smoke-results.json), [release gates](qa/RELEASE_ACCEPTANCE.md), [defect log](qa/DEFECT_LOG.csv).

Build and local regression were executed for this patch. Production deployment is blocked by missing Vercel authentication; backend provisioning and hosted regression were not performed. The new CI workflow runs build/regression on main and PRs; check its Actions result separately.

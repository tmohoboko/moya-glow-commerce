# Moya Glow Commerce

A functioning beauty storefront MVP for initial QA. Uses mock products and illustrative local packaging images. No orders or payments are processed.

## Stack

React, JavaScript, Vite, responsive CSS, Playwright, Git, and Vercel deployment configuration. No backend or runtime secrets required.

## Features

30 products across skincare, makeup, body care, and hair care; searchable and filterable catalogue; product detail pages; persistent shopping bag; quantity controls, removal, subtotal in ZAR, empty states, and graceful unknown routes. Cart storage is best-effort when browser storage is unavailable. Quantities are capped at 99 per product.

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
npx vercel login
npx vercel --prod --yes
```

Deployment execution and any account blockers are recorded in `qa/RELEASE_ACCEPTANCE.md`.

## QA status

See `qa/TEST_EVIDENCE.md` for executed checks, `qa/RELEASE_ACCEPTANCE.md` for release gates, and `qa/DEFECT_LOG.csv` for unresolved defects. Browser coverage is Chromium; manual exploratory QA is still required.

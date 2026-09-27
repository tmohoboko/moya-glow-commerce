# Moya Glow Commerce

A functioning beauty storefront MVP for initial QA. Uses mock products and illustrative local packaging images. No orders or payments are processed.

## Stack

React, JavaScript, Vite, responsive CSS, FastAPI, SQLite, Playwright, Docker, Git, and Vercel deployment configuration. Static storefront mode requires no backend; the enterprise mode uses the additive FastAPI service.

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

Tests run against the production preview on port 4173. To test a deployed site, run `BASE_URL=https://your-site.vercel.app npm test`. Results are written to `qa/smoke-results.json`; mobile and desktop screenshots are saved in `qa/`. Run `npm run lint` for JavaScript lint and `npm run test:api` for backend checks. If using an existing Chromium installation, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/absolute/path/to/chrome` when running `npm test`.

## Deployment

Vercel settings: Vite, build command `npm run build`, output directory `dist`. SPA rewrites are provided in `vercel.json`.

```sh
# Original production linkage is protected on this branch.
# Use the isolated enterprise deployment instructions below.
```

Production: https://moya-glow-commerce.vercel.app

Repository: https://github.com/tmohoboko/moya-glow-commerce

Original production deployed through the authenticated Vercel CLI. Automatic GitHub deployments are not connected. Do not deploy this branch through the original root linkage. Deployment evidence is recorded in `qa/RELEASE_ACCEPTANCE.md`.

## QA status

All ten production Chromium smoke checks passed on 2026-09-26. See `qa/TEST_EVIDENCE.md` for executed checks, `qa/RELEASE_ACCEPTANCE.md` for release gates, and `qa/DEFECT_LOG.csv` for unresolved defects. Browser coverage is Chromium; manual exploratory QA is still required.

## Enterprise port prototype

This branch adds FastAPI + persistent SQLite alongside the existing React storefront. See [release evidence](docs/RELEASE_EVIDENCE.md), [QA gaps](docs/GAP_REPORT.md), [decisions](docs/PORT_DECISIONS.md), and [test plan](docs/TEST_PLAN.md).

Start the complete local app (separate Compose project and volume; port 8013):

```sh
docker compose up --build -d --wait
docker compose exec app python -m backend.app.manage create-user --email operator@example.com --role admin
```

Open http://127.0.0.1:8013/account and sign in using the password you entered. Additional roles: catalogue_manager, support_agent, analyst, customer. No default accounts exist. API documentation: http://127.0.0.1:8013/docs. Orders start empty; order placement and all payments stay disabled. Test-only orders exist only in disposable QA databases.

Without Docker: install `backend/requirements.txt` into `.venv`, build with `VITE_CATALOG_API=true npm run build`, then start `MOYA_SEED_DEMO=true .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers`. Provision users with `.venv/bin/python -m backend.app.manage create-user ...`. SQLite defaults to ignored `data/moya.sqlite3`. For split local development, use `VITE_CATALOG_API=true npm run dev` (Vite proxies `/api` to port 8000).

Catalogue replacement: [validated import instructions](docs/CATALOGUE_IMPORT.md). The original mock catalogue is an explicit temporary seed. Published API results preserve the existing product shape.

The separate Vercel enterprise project serves the static storefront/account shell until persistent backend hosting is configured. Static preview does not provide account/admin mutations or maintenance propagation. Do not deploy from the root `.vercel` linkage: it belongs to the original production site.

### Google sign-in (optional)

Password login remains available. Configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` on the backend only; all three must be present and the redirect URI must be valid. `/api/auth/providers` exposes enabled provider names only. With missing configuration, the account page disables **Continue with Google**, including on the static Vercel fallback.

The browser starts at `/api/auth/google/start`, returns through `/api/auth/google/callback`, and exchanges a short-lived HttpOnly handoff cookie at `/api/auth/google/session` for the existing in-memory Moya bearer session. New Google identities create customers only. Initial linking uses normalized verified email; subsequent sign-ins use Google's stable subject ID. Existing active staff keep their operator-assigned roles; no Google claim can grant a staff role. Google access/refresh tokens are not stored.

See [Google Console and local setup](docs/DEPLOYMENT.md#google-oidc-setup). Tests mock Google network traffic and require no real credentials. Real hosted Google login is still blocked until a persistent backend is available and configured; no live deployment was changed by this patch.

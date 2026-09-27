# Release evidence — 2026-09-27

Repository: `/home/tmdev012/Reception/moya-glow-commerce`.
Branch: `port/adfund-enterprise-prototype`; baseline `d2a9f03`.
Implementation commit: `f5d1759b0566dae92f6f707ff851207e5cc15e84`. A subsequent documentation-only commit records the completed CI result. Implementation commit message: `feat: port enterprise commerce capabilities into Moya Glow`.

## Live result

New public host: **https://moya-glow-enterprise-port.vercel.app**.
Immutable deployment: https://moya-glow-enterprise-port-mvhuxjk30-tmdev.vercel.app.
Deployment ID: `dpl_4cDhV52EA674HZfu2JAhAyRjyZT7`.
Vercel project: `tmdev/moya-glow-enterprise-port`; CLI reported READY.
Inspect: https://vercel.com/tmdev/moya-glow-enterprise-port/4cDhV52EA674HZfu2JAhAyRjyZT7.

**Public host is a static fallback, not a hosted enterprise backend.** Storefront/cart and account shell work; account/admin API calls report service unavailable. No persistent backend workflow/credentials existed. The full React/FastAPI enterprise app runs locally at http://127.0.0.1:8013 with a healthy Docker service and dedicated persistent volume. See DEPLOYMENT.md for exact next commands and hosting prerequisites.

Original https://moya-glow-commerce.vercel.app returned HTTP 200 after the new deployment. Original root `.vercel/project.json` SHA-256 remained identical before/after; the new project ID differs. No original production redeploy, force push, merge, payment action or donor source deletion was performed.

## Executed gates

| Gate | Result | Evidence |
|---|---|---|
| Frontend static build | PASS | Vite production build locally and on Vercel |
| Frontend API build | PASS | `VITE_CATALOG_API=true npm run build`, also Docker multi-stage build |
| Lint | PASS | `npm run lint` |
| Frontend unit | PASS, 2 tests | `npm run test:unit` |
| Backend API | PASS, 15 tests | `npm run test:api`; role matrix, CRUD, auth, support, order, maintenance, import |
| Existing local storefront Playwright | PASS, 10 tests | `qa/local-storefront-results.json` |
| Enterprise Playwright | PASS, 7 tests | `qa/enterprise-results.json`; real disposable FastAPI service |
| Live storefront Playwright | PASS, 10 tests | `qa/smoke-results.json`, base URL is new live host |
| Live account shell | PASS | Browser sign-in attempt reports backend unavailable; `qa/live-account-shell.png` |
| Admin visual evidence | PASS | `qa/enterprise-dashboard.png`, `qa/enterprise-products.png`; 375px document overflow check passed |
| Postman / Newman | PASS, 25 requests / 50 assertions | `qa/newman-summary.txt`; disposable database only |
| Docker clean start | PASS | `docker compose up --build -d --wait`, new project/network/volume; subsequent rebuild healthy |
| Health/readiness | PASS | HTTP 200 `/api/health` (`payments: disabled`), `/api/readiness` (`ready`) on port 8013 |
| Catalogue import command | PASS | 30 records dry-run validated locally and inside final Docker container |
| Catalogue replacement gate | REACHED | `CATALOG_READY_FOR_REPLACEMENT`; atomic import/unpublish/audit tested |
| GitHub Actions | PASS | https://github.com/tmohoboko/moya-glow-commerce/actions/runs/36349077173; implementation commit f5d1759 |
| Secret scan / whitespace | PASS | Staged `scripts/secret-scan.py`; `git diff --check` |

## Failures encountered and resolved

- Initial API suite: 14 setup errors caused by seed SQL placeholder mismatch. Fixed; final 15 API tests pass.
- Initial lint setup: incompatible ESLint latest major/React plugin peer dependency. Compatible version installed; lint passes.
- Concurrent final browser runs: two enterprise cases failed during trace artifact cleanup because suites shared `test-results`. Configs now use separate storefront/enterprise output directories; all seven rerun cases pass.
- Initial live run: 9 pass, one `net::ERR_NETWORK_CHANGED` navigation failure. Complete rerun: 10 pass. No automatic retries or assertion weakening was added.
- Non-failing deprecation notices remain for HTTPX TestClient and parts of lint/Newman tooling; Docker also warned that optional buildx/Bake was absent, then built successfully.

No remaining failures in the executed final automated gates. GitHub Actions also passed lint, unit/API checks, both frontend builds, both browser suites, secret-scan step and artifact upload. Safari/Firefox, real devices, accessibility, load/abuse, hosted backend E2E and backup/restore have not been certified. QA debt is **14–22 engineer-hours**; see GAP_REPORT.md and DEFECT_LOG.md. This release is a prototype, and full hosted enterprise acceptance remains blocked on backend hosting.

## Scope of changes

- `backend/app/`: database/migrations integration, authentication/permissions, API, audit/logging, CLI provisioning and transactional catalogue import.
- `backend/migrations/`, `backend/seed-products.json`, `backend/tests/`: native commerce schema, original mock seed, API/security tests.
- `src/admin/`, `src/lib/`, `src/main.jsx`, `src/style.css`: account/admin screens, API client, optional live catalogue, preserved public views and cart.
- Docker/Compose, Vite proxy, lint/unit configuration, Playwright isolation, Postman collection/environment, GitHub CI workflow.
- Source decisions, Flutter compatibility, import/deployment instructions, test plan, defect/gap report and screenshots/results.

Purchased donor: AdFund 3.6.0, Laravel ^12.60/Flutter reference. No PHP, Flutter runtime, fundraising, wallet, crypto or new payment behavior entered the product.

## Google login patch — 2026-09-28

Bounded patch on `port/adfund-enterprise-prototype`; no live deployment or original Vercel linkage changed. Adds Google start/callback/provider-capabilities endpoints and same-origin session handoff; password login uses the same shared Moya session issuer. Adds forward migration `002_google_oidc.sql` for one-time OAuth states, stable social identities and one-time handoffs. Google credentials are backend environment settings only; provider is disabled without them. New users are customers; existing active users preserve roles. No provider access/refresh tokens are persisted.

Changed modules: `backend/app/google_auth.py`, `security.py`, `main.py`, forward SQL migration, pinned Authlib/dependencies, Compose environment, React account component, API/browser tests and deployment/QA documentation.

The first API run passed 40 tests and failed the signed-token success fixture. The test had replaced `httpx.Client` globally, interfering with Authlib's HTTP client initialization. HTTP client injection is now isolated; signature/issuer/audience/nonce/expiry/algorithm failures exercise actual signed-token validation with mocked network calls. No verification assertions were weakened.

Real Google login has not been attempted without operator credentials. Automated tests require neither Google credentials nor network. Public hosted OAuth remains blocked by missing persistent backend hosting. See the patch's final gate results below.

Google patch local gates:

| Gate | Result |
|---|---|
| Backend API/OIDC/security | **45 passed** (Google token/JWKS network mocked; real generated JWT signatures validated) |
| Enterprise browser | **12 passed**; `qa/google-auth-enterprise-results.json` |
| Original storefront regression | **10 passed**; `qa/google-auth-storefront-results.json` |
| Frontend unit / lint | **2 passed** / PASS |
| Static and API frontend builds | PASS |
| Docker rebuild/start / health / readiness | PASS, HTTP 200; existing volume migrated to 002 without resetting data |
| Docker provider capabilities without credentials | PASS: password only |

No unresolved local test failures. Non-failing HTTPX and Authlib JOSE deprecation warnings remain. CI executes the same required gates on the pushed implementation commit; its final run result is linked in the operator handoff. No real Google credentials were used, and no public hosted OAuth verification is claimed.

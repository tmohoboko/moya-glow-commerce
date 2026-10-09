# L Beauty frontend release patch — 2026-10-09

## Changes

- Browser titles now follow home, services, bag, valid service details and missing routes. Refresh and Back/Forward navigation are covered.
- Added three release regressions for route titles, layout at 320/375/768px and vector branding asset loading.
- Local preview binds to loopback for predictable execution. QA_RESULTS_PATH and QA_SCREENSHOT_DIR keep local, hosted and CI artifacts separate.
- Vercel configuration explicitly selects Vite and lockfile-based npm ci. .vercelignore excludes QA evidence and unrelated backend/enterprise directories from the frontend upload.
- Added a main/PR CI workflow to build, run Chromium regression and upload evidence.
- npm run release:vercel requires an existing named Vercel link and authentication, runs local checks, deploys the frontend, then runs hosted regression. It does not provision backend hosting.

## Executed checks

npm ci: PASS (21 packages). npm run build: PASS (Vite 7.3.6).

Playwright: **16/16 PASS**, zero skipped/unexpected/flaky results.
Machine start: 2026-10-09T09:03:05.349Z. Duration: 9.0 seconds.
Target: http://127.0.0.1:4173 (local production preview).

Standard browser download returned invalid archives in this environment. The run used npm-distributed @sparticuz/chromium with PLAYWRIGHT_CHROMIUM_EXECUTABLE=/tmp/chromium. This temporary browser tooling was not added to the project's dependencies. CI installs standard Playwright Chromium separately; its result is tracked by the Actions run.

Commands:

```sh
npm ci --no-audit --no-fund
npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/tmp/chromium QA_RESULTS_PATH=qa/release-local-results.json QA_SCREENSHOT_DIR=qa/release-local npm test
bash -n scripts/release-vercel.sh
```

[Machine report](release-local-results.json), [mobile screenshot](release-local/mobile-home.png), [desktop screenshot](release-local/desktop-home.png).
Desktop and mobile screenshots were visually reviewed for clipping and branding. This is limited visual review, not full manual/cross-browser acceptance. No CSS change was needed: current layout passed the tested widths.

## Deployment status

**Production update not performed: Vercel CLI is logged out in this environment, and the Vercel plugin is not connected.** No new Vercel project was created. The existing automatic GitHub deploy integration remains unverified. This commit is not proof of production deployment.

To release from an authenticated checkout of this patch:

```sh
npx --yes vercel@61.1.0 login
npx --yes vercel@61.1.0 link --yes --project moya-glow-commerce --scope tmdev
npx playwright install chromium
npm run release:vercel
```

Link only the existing tmdev/moya-glow-commerce project. Confirm its identity in the dashboard before linking. The release script refuses a missing/unnamed/wrong project link. Local and hosted reports use separate paths. A hosted regression failure exits nonzero after deployment; investigate the live result rather than calling the release accepted.

## Readiness

Local storefront build and regression: PASS for this patch. Full release: HOLD until current production deployment and hosted regression, completed manual acceptance, and persistent HTTPS backend integration (enterprise scope) are evidenced. Payments/booking/orders remain unavailable by design.

## Tested source fingerprints

- `src/main.jsx` SHA-256: `934d4db4bb00e445041316dd581b5bd9ab2d6aa149018e8ab63c109a9572b3ba`
- `index.html` SHA-256: `7c197a53ffc22b198ae2b3aab775568add02d7c28993beede0540f2d27d58173`
- `playwright.config.js` SHA-256: `56247c749790a168ee8ecaa3dc0958ed1534ed76e95a462bc60a1f00907fcb0b`
- `tests/release.spec.js` SHA-256: `8c7df5c959d5df32cfadc9589db63c1fe9a23c7f45c65a952879e62d24ac1461`
- `tests/smoke.spec.js` SHA-256: `4179e343ffa553792bfef34cce47c10e9807ece8dbd790b9f36cfc49f58fdbb9`

# Release acceptance

2026-09-26 — Local acceptance PASS; external release BLOCKED by account authorization.

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
- [ ] GitHub repository created and main pushed.
- [ ] Vercel production deployment and production smoke tests.
- [ ] Manual exploratory and cross-browser QA.

## External blockers

GitHub CLI is authenticated as `tmdev012` using the keyring. Target repository lookup failed. Automated creation with `gh repo create tmohoboko/moya-glow-commerce --public --source=. --remote=origin --push` was rejected: `tmdev012 cannot create a repository for tmohoboko`. No repository created or push completed. Requested HTTPS origin is configured. Authenticate as `tmohoboko` with `gh auth login --hostname github.com`, then retry repository creation. Do not force-push.

Vercel CLI 60.1.3 `whoami` reports `Logged out`. No deployment attempted without account authorization. Run `npx vercel login`, then `npm run build` and `npx vercel --prod --yes`. Configuration is ready: Vite, npm run build, dist, SPA rewrites. No production URL exists.

## QA limitations

No open application defects identified by the executed smoke suite. One accessible-label defect was fixed and retested. Only local Chromium was tested. Real payments and checkout are intentionally excluded; the bag explicitly identifies the demo limitation.

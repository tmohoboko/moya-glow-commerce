# Release acceptance

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

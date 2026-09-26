# Shipping log

2026-09-26

- Audited /home/tmdev012/Reception/moya-glow-commerce: shipping kit only, no package.json, dependencies, source, or Git repository. Preserved prompts/, qa/, scripts/, docs/, templates/.
- Added React/Vite storefront, 30 mock products, local SVG placeholder, responsive CSS, product routes, persistent cart, SPA deployment configuration and ignore rules.
- Ran npm install: success, zero reported vulnerabilities. Ran npm run build: success (including rebuild after category label correction).
- Initialized Git main; initial commit 377d4b3. Inspected staged changes and ran scripts/secret-scan.py before commit and attempted publish.
- gh auth status: authenticated as tmdev012. Target lookup unavailable; gh repo create for tmohoboko failed due to account permissions. Configured requested HTTPS origin. No push completed.
- Vercel CLI was absent; downloaded through npx. Executed CLI 60.1.3 whoami directly from npx cache: Logged out. Deployment blocked on login.
- Added ten Playwright tests and updated smoke/release launcher scripts. First run: nine passes and one category accessible-label failure. Added explicit select aria-label; rebuild and complete rerun: ten passes in 10 seconds.
- Used existing Chromium 148.0.7778.96 after default browser download was slow and reset. Stopped unnecessary browser download after tests passed.
- Captured desktop/mobile screenshots and JSON report. Inspected mobile screenshot. Updated README, defect log, test evidence and acceptance checklist with actual results and external blockers.

## Authenticated shipping continuation — 2026-09-26

- Rechecked gh auth status and npx vercel whoami: both now authenticated as tmohoboko.
- Confirmed clean main and existing valid commit; npm run build passed without source changes.
- Created public tmohoboko/moya-glow-commerce. Creation could not add the already-configured origin; retained correct origin, ran gh auth setup-git and git push -u origin main successfully. Remote SHA matched a400eff.
- npx vercel --prod --yes created project tmdev/moya-glow-commerce and deployed production successfully. Cloud build passed; alias https://moya-glow-commerce.vercel.app is live.
- Automatic GitHub integration failed during deploy and on explicit retry; CLI deployment remains usable. Recorded this nonblocking limitation.
- Ran existing ten smoke checks against public production: 10 passed in 14.4 seconds. Updated screenshots, JSON report, README and release evidence. No new application defects found.

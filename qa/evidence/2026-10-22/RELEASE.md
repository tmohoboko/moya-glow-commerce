# Delivery checklist — 22 October 2026

## Source and target
- Repository: tmohoboko/moya-glow-commerce, booking branch feat/booking-workflow; worktree qa-booking-local based on 8ccdfaf. Existing uncommitted booking/calendar fixes preserved and reviewed.
- Existing tmdev project prj_bh0BVwyX51a47jBCDXIR8wmmVct4, root ., frontend + FastAPI services.
- Baseline production dpl_9F9XuPzauvTaeGCKyDHbjU2M9aq3 runs 4dc80d32346f48c1b9699bbd5d690ccb12a9b008. New public calendar endpoint returns 404 there.
- Current remote booking CI passes: https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39548816243

## Checklist
- [x] Inspect branches, dirty files, history, CI, target, existing release evidence.
- [x] Clean npm ci and Vite build. No lint/type script exists in package.json.
- [x] SQLite backend: 57 passed, one Postgres-only skipped.
- [ ] Postgres backend suite.
- [x] Full browser regression: 33 passed on fresh disposable fixture; session lookup, registration/logout/login, full booking/invoice/reschedule/cancellation and catalogue/mobile regressions. React review: effect cleanup, no private data in public calendar, distinct confirmed vs temporary selection.
- [ ] Commit and push intended changes; preserve existing staged Oct 21 evidence.
- [ ] Stage exact production release and verify hosted routes, sessions, availability and persistence.
- [ ] Hosted staff quotation/booking/invoice payment: requires existing owner staff access and actual opening weekdays. Asked owner; do not fabricate schedule or silently grant privilege.
- [ ] Genuine Stripe sandbox invoice success/failure/cancellation and webhook persistence.

## Findings
Existing approved booking release intentionally parks unlinked cart checkout (410); previous paid orders remain visible. Retain quotation-led service journey, do not resurrect archived direct commerce checkout.
Public production /api/readiness returns ready=true, database=true, stripe=true, payment_mode=test. No live payments enabled.
Initial browser run: 31 passed, two failed in health precondition because API startup was still pending. Rerun after health 200 initially reused stale disposable fixture; account actions/second booking stalled. Archived that temporary database, reseeded a fresh fixture, then 33/33 passed. No checks weakened.

## Assessment
HOLD until hosted customer and staff journeys have evidence. Commercial owner acceptance remains separate.

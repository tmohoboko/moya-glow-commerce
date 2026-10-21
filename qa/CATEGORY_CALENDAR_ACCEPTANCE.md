# Six-task category and calendar acceptance

Runtime commit: `5305ba3be9a5cc00c6383eaacf1bbc81b47e788d`.
Production deployment: `dpl_Agn8fqyZgFxx2BF2ebSJVeqorLmV`, READY, Production alias verified.
Review: https://moya-glow-commerce.vercel.app/calendar
CI: https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39537559374

## Delivered

1. Six presentation groups consolidate related services, including Body, Facial and Intimate Wax under Waxing. All 46 service identities, prices and 11 underlying source categories remain preserved.
2. Photo-count order: Nails (12), Lashes & Brows (9), Makeup (7), Hands & Feet (6), Massage (4), Waxing (13, explicitly last). There are 50 distinct displayed gallery images; one shared nail/hand image belongs to two groups.
3. Shared treatment-specific framing across catalogue, detail, request and gallery. Nine lash/brow images show eyes/brows rather than full portraits. Three new salon-detail assets replace generic equipment/room views. Existing hover and reduced-motion handling retained.
4. Day/Week calendar navigation on public/personal and staff views, with Monday-based weeks, date controls, private appointment details and staff blocked-time indicators.
5. Accepted-quotation booking submit form shows treatment, total, duration, buffer, available/unavailable slots and selection confirmation. Changing date/view clears selection. Backend atomically rechecks capacity; a competing reservation returns a recoverable conflict rather than a false confirmation.
6. Build, API, browser regression and Production deployment completed.

## Evidence

- SQLite: 53 passed, one PostgreSQL-only test skipped.
- PostgreSQL 16: 54 passed, including concurrency and persistence coverage.
- Playwright: 29 passed, including complete customer/staff quotation → acceptance → Week slot form → booking → invoice journey, conflict recovery and mobile views.
- Production read-only HTTP checks: 14 passed; routes, readiness, 3 replacement assets, preserved catalogue and calendar API access controls.
- Live browser: category filter and focused lash photographs visually inspected; Day, Next day, Week, Next week and Today controls changed the displayed dates correctly, including a week crossing into November.
- Production screenshots and selected CI screenshots/report are packaged in CATEGORY_CALENDAR_EVIDENCE.zip. CI screenshots use disposable artificial accounts. No live payment or production appointment was created for this patch.
- Repository secret scan and whitespace check passed before runtime commit. No migration or environment-variable changes required.

## Existing business setup boundary

Production booking remains disabled until genuine salon hours are configured. There is no Production staff grant. A prior automatic approval review rejected granting staff access; this patch did not retry or bypass it. Privileged booking behavior was tested with a disposable CI-only staff fixture. The fixture is not a hosted login. No claims of live Google Calendar synchronization or clean Vercel runtime-log access are made.

Draft PR #5 remains unmerged. The deployed runtime SHA above is distinct from the subsequent evidence-only commit.

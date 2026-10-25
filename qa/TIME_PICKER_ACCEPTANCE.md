# Available-time picker acceptance

Production runtime: `6ecdb37f2f68e12150e09c3c36be3741a75e5944`.
Deployment: `dpl_7tfCKGMg3mZCgGjji1FdgEj5gR3A`, READY.
Review: https://moya-glow-commerce.vercel.app/appointments
CI: https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39539726538

Accepted quotations and rescheduling now expose an accessible Available time dropdown. Options come exclusively from authenticated availability responses, grouped by date in Week view and shown in South African time. The dropdown and slot buttons share one selection. No arbitrary free-text time can be submitted. Refresh, date/view changes and a booking conflict clear selection; confirmation stays disabled until a valid selection exists. The mobile picker occupies a full row.

Existing backend checks duration, buffer, salon hours and busy intervals, then locks/rechecks capacity when saving. Two simultaneous requests for one slot produce one success and one conflict. No backend schema, staff privileges or business hours were changed. Production slots still depend on real salon hours and accepted quotations.

Validation: build passed; focused booking API suite 19 passed; final CI browser regression 29 passed, including real quotation-to-invoice flow through the dropdown, refresh/selection clearing, occupied-slot omission, last-moment 409 recovery and mobile overflow check. Final backend jobs passed (SQLite and PostgreSQL). Production /appointments, deployed picker bundle and /api/readiness returned 200. `available-time-picker.png` is the final CI mobile conflict-recovery screenshot, using an artificial fixture; no Production reservation/payment was created.

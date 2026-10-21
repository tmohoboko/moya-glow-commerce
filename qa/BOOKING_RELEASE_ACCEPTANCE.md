# L Beauty quotation-led booking release — 20 October 2026

Engineering release verified. Client acceptance and Production staff-access
approval remain outstanding. Do not describe those as completed.

## Exact release

- Public site: https://moya-glow-commerce.vercel.app
- Appointment request: https://moya-glow-commerce.vercel.app/book?service=massage-full-body-450
- Customer appointments: https://moya-glow-commerce.vercel.app/appointments
- Staff interface: https://moya-glow-commerce.vercel.app/salon
- Runtime/source tested: `d583d74cf663572027c1705745ca7c12f07dc399`.
- Production deployment: `dpl_66dMiDXLVtRxwXSKW9PoeeujYgor` — READY.
- Exact deployment URL: https://moya-glow-commerce-ixo3qimoo-tmdev.vercel.app
- Earlier preview of identical application runtime (tests/docs later expanded):
  `dpl_9GDUsSwrNB2BZU5Ffd4DgBZvF4dG`, commit `b9971ad4cbcc13a94c169c3f63d5f5d579144f16`.
- Preview is Vercel-protected and retains its separate Neon database and no Stripe
  keys. Its combined readiness can return 503 for absent Stripe while booking
  data storage is configured. No protection was disabled.
- Draft PR #5: https://github.com/tmohoboko/moya-glow-commerce/pull/5
  Stacked on the existing account/storage/payment PR #4. Neither PR was merged.
- Previous commerce release is retained at `archive/commerce-sandbox-2026-10-20`.
- No Vercel Git integration or automatic production deployment was created;
  authenticated exact-commit deployment was used.

## Verified evidence

| Boundary | Result | Evidence |
| --- | --- | --- |
| Build/catalogue sync | PASS | Vite build + sync check in CI |
| Browser customer/staff journey | 24 PASS, 0 skipped/failed/flaky | `booking-browser-results.json` |
| SQLite API suite | 49 PASS, 1 Postgres-only skipped | CI backend job |
| Postgres 16 API suite | 50 PASS | CI backend job |
| Public hosted acceptance | 30 PASS | `booking-hosted-results.json` |
| Production Neon quotation | Confirmed independently | ID below, no fabricated booking |
| Production migration preserves original data | PASS | 11 users / 6 orders / 2 payment events before and immediately after migration |
| Staff role isolation | PASS | Customer access to staff API rejected with 403 |
| Actual Production staff grant | BLOCKED | Automatic approval review requires explicit user authorization |
| Manual client/business acceptance | NOT RUN | Owner/client to confirm workflow and business configuration |

Final CI run:
https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39421713221

- Regression job 118624033038: 24 passed (20.6 seconds).
- Backend job 118624032682: 49 passed/1 skipped SQLite, 50 passed Postgres.
- Privileged staff browser fixture exists only in the disposable CI SQLite DB.
  It is not a real or reusable hosted account.
- Browser coverage includes request → staff quotation → acceptance → available
  slot → invoice → calendar download → reschedule → cancellation and void invoice.
- API coverage includes two different concurrent customers competing for one
  interval; exactly one succeeds. It also checks cross-account access, cleanup
  buffers, opening hours, expiry/revision checks, walk-ins/blocks, fresh-process
  persistence, quote-derived invoice totals, payment-event receipts, and late
  payments following cancellation.
- The public hosted `hosted` CI job is deliberately skipped for this branch;
  hosted API verification was run explicitly after deployment readiness. Do not
  call the 24 CI browser checks public hosted browser regression.

## Hosted verification scope

The bounded verifier creates exactly one artificial customer and quotation, logs
out and back in, verifies persistence, then logs out again. It stores no password,
session token or checkout URL. Production customer quote ID:
`5d3703cf-a20c-43ae-8f0f-b77489bda63d`.

Independent Neon query confirms requested/online, amount NULL, duration NULL,
zero appointments. The name and notes explicitly identify automated QA; it is
not a real appointment request. No real user's data was changed by the verifier.
The data remains as audit evidence; it was not deleted.

Invoice-payment behavior was checked in SQLite/Postgres with the existing Stripe
transport/signature verification suite. The previous release's genuine hosted
Stripe success/decline/cancel/3DS evidence remains in
`HOSTED_RELEASE_ACCEPTANCE.md`. No new end-to-end hosted invoice payment was
executed in this release, because Production staff approval is still required.
No live payments, manual cash/EFT receipts or automatic refunds were enabled.

Live browser inspection confirmed the public appointment-request UI. The only
captured browser error was a browser-extension metadata message, not an L Beauty
application error. Runtime-log access remains unavailable with the current
Vercel connector permissions; no clean runtime-log claim is made.

## Remaining access approval — concrete action

Automatic approval review rejected inserting a Production `lb_staff` grant for
the owner's existing account. Stated reason: granting a real Production account
staff privilege requires explicit user authorization; an assistant's plan is
insufficient. The rejection was respected. No alternate account, endpoint,
browser or indirect database action was used to bypass it.

The pending action is one staff grant for existing user ID
`65019a44-4f95-46b7-8ceb-b28763df312a`. It permits viewing customer contact/request
information, issuing quotations/invoices, configuring hours and managing the
salon calendar. It does not change a password, create cloud credentials, grant
Neon/Vercel/Stripe account access, or activate real payments. Zero staff grants
were present following the rejection.

The owner still needs to enter actual opening hours and quotation terms. The
calendar starts disabled with all days closed; the implementation has no invented
client opening hours. There is one shared calendar and calendar downloads only,
not live Google Calendar synchronization. OTP/MFA/reset, reminders, deposit
rules, multiple therapists and live payments remain outside this change.

## Manual acceptance — owner's QA work

1. Log in using the existing account. After staff authorization, open `/salon`.
2. Configure the salon's actual weekdays/hours and enable its calendar.
3. Use a separate normal customer account to request a treatment, including
   removal/design details where relevant.
4. Staff: issue the agreed total, duration, cleanup buffer and terms.
5. Customer: review/accept, choose a time, confirm, inspect the invoice.
6. Verify staff calendar and customer history show the same appointment.
7. Check reschedule, cancellation and released capacity, including a walk-in.
8. Optionally test invoice payment using Stripe's public sandbox card 4242,
   expiry 12/34, CVC 123; verify the receipt independently from the return URL.
9. Record actual/expected results and defects; mark client acceptance separately
   from the automated results.

# Account and Stripe sandbox acceptance — 2026-10-20

Implementation: `b23f6c8ce9b841c728c60e6ab925711aa939b73e` on `feat/hosted-login-stripe`.

Review: https://github.com/tmohoboko/moya-glow-commerce/pull/4

## Executed

- Local backend: 29 passed, one Postgres-only check skipped.
- CI SQLite: 29 passed, one Postgres-only check skipped.
- CI Postgres 16: 30 passed, including simultaneous checkout retries and duplicate webhook delivery.
- CI Chromium: 21 passed, including registration, refresh, logout/login, private cookies, cart preservation and all 18 existing catalogue/photo/layout regressions.
- Catalogue synchronization, production Vite build and shell syntax checks passed.
- CI run: https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39371055832
- Vercel preview deployment `dpl_kfgCd5929pWEm1TLUh51tNMRARLf`: READY.
- Browser verified `/account` login/create-account screens and API JSON responses: health `{status:ok,service:lbeauty,payment_mode:test}`; readiness `{ready:false,database:false,stripe:false,payment_mode:test}`.
- Account screen captured in `backend-account-preview.jpg`.

## Pending hosted acceptance

No hosted database or Stripe settings were present at inspection. The code and UI are deployed for review; hosted account creation, durable hosted sessions/orders and a genuine Stripe sandbox Checkout have not been accepted. SDK transport fixtures and real HMAC verification in tests are not a real Stripe transaction.

The account owner must connect Neon and enter the sandbox key and webhook signing secret in Vercel. Start with Preview configuration. A stable branch deployment alias is required for webhook delivery across redeployments; a unique deployment URL must not be reused as the webhook target after its environment has changed. Production needs its own endpoint/signing secret and database branch when promoted.

After configuration: redeploy, verify readiness, create a customer account, complete a test card checkout and confirm the signed webhook changes the order to paid. Then check decline, 3D Secure, cancellation, retry, logout and refresh. Appointment availability, email verification/reset and real payment activation remain outside this test release.

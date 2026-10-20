# L Beauty

The existing 46-service, 11-category catalogue and photo gallery, with customer accounts and Stripe **sandbox-only** checkout. Appointment scheduling is arranged separately. Bridal and Special Effects require a confirmed quote and cannot be purchased at their “From” base prices.

## Run locally

Use Node 22+ and Python 3.12. In the first terminal:

```sh
npm ci
python -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In the second terminal:

```sh
npm run dev
```

Vite proxies `/api` to the local backend. Local development uses an ignored SQLite file if no database URL is supplied. Hosted Vercel deployments require Postgres; they never fall back to an ephemeral SQLite database. No demo accounts or known public passwords are seeded. Create a customer account with a password of at least 12 characters.

## Account and payment behavior

- Passwords use salted scrypt; sessions are stored as hashes and expire after eight hours. Browser sessions use HttpOnly, SameSite=Lax cookies, Secure on Vercel. Logout revokes the session; unsafe browser requests require a matching Origin. Login and registration have database-backed rate limits.
- Checkout accepts service IDs and integer quantities. The server loads prices from `backend/app/catalogue.json`, which is generated from the existing catalogue. It persists an order before requesting a hosted Stripe Checkout session and reuses its Stripe idempotency key after a network failure.
- Only `sk_test_` Stripe keys are accepted. Real charges are deliberately unavailable. The browser never receives the Stripe secret key or card details.
- Verified Stripe webhook events update payment status after matching order ID, session, amount, currency and sandbox mode. Duplicate and concurrent events are handled once; late failure/expiry events cannot undo a paid status. Returning to the success page does not mark an order paid.
- Customers can only see their own orders. There is no public administrative role, password reset, email verification, appointment reservation or production payment activation in this test release.

## Vercel setup

The feature uses Vercel Services (currently beta) to deploy Vite and FastAPI together under one origin. Top-level `/api/*` routing precedes the storefront fallback. The existing project is `moya-glow-commerce` in `tmdev`.

1. The Neon project and separate production/preview databases are provisioned, migrated and connected using private `DATABASE_URL` secrets. Reuse the resources in [deployed storage](docs/DEPLOYED_STORAGE.md); do not create duplicates. Preview is scoped to the Preview environment because this Vercel project has no connected Git integration.
2. Production has private `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` values from **Bee app sandbox**. This hosted Checkout integration needs no publishable key. Never expose these values through a `VITE_` variable. Protected Preview has database access only; use the public site for payment acceptance.
3. The existing sandbox webhook `lbeauty-vercel-sandbox` sends to `https://moya-glow-commerce.vercel.app/api/stripe/webhook`, listening to `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded` and `checkout.session.async_payment_failed`. Both API requests and webhook snapshots use `2025-10-29.clover`. Do not silently inherit the SDK's newer API version: Endive rejects this integration's card-only `payment_method_types` request parameter.
4. Redeploy after changing environment variables. Schema version 1 creates only additive `lb_*` tables on first database use, serialized by a Postgres advisory lock. Existing prototype tables are untouched. Future schema changes require versioned migrations.
5. Confirm `/api/health` returns 200 and `/api/readiness` returns 200. Readiness returns 503 until the database and both sandbox settings are present. It reports configuration readiness, not a verified charge.
6. Create your customer account, add Full Body (R450), and use the Stripe test card `4242 4242 4242 4242`, a future expiry and any three-digit CVC. Check the order becomes “Test payment confirmed” and that Stripe recorded a successful webhook delivery. Also check cancellation, declines and 3D Secure before accepting hosted payments.

Direct Stripe sandbox access, card success, cancellation, decline, 3D Secure and signed webhook delivery are verified. The release remains sandbox-only. See [hosted acceptance](qa/HOSTED_RELEASE_ACCEPTANCE.md) for the deployed commit, evidence and manual test steps.

## Validation

```sh
node scripts/sync-catalogue.mjs --check
.venv/bin/python -m pytest backend/tests -q
npm run build
npx playwright install chromium
npm test
```

Keep the backend running on port 8000 for browser tests. Playwright starts the production Vite preview on port 4173. CI runs browser regression plus the backend suite on SQLite and dedicated Postgres 16, including concurrent checkout/webhook delivery. The Stripe SDK transport and real HMAC verification are tested locally; real hosted Stripe acceptance requires the dashboard configuration and a genuine sandbox checkout.

When editing service data, run `node scripts/sync-catalogue.mjs` and commit the generated JSON with the frontend change. Do not place real credentials in `.env.example` or version control.

Production: https://moya-glow-commerce.vercel.app

Repository: https://github.com/tmohoboko/moya-glow-commerce

Official references: [Vercel Services](https://vercel.com/docs/services), [Neon integration](https://vercel.com/marketplace/neon), [Stripe Checkout](https://docs.stripe.com/checkout/quickstart), [webhook fulfillment](https://docs.stripe.com/checkout/fulfillment), [Stripe testing](https://docs.stripe.com/testing), [Stripe availability](https://stripe.com/global).

## Data model and state management

[Implemented ERD, state transitions and CORS/cookie decisions](docs/DATA_AND_STATE.md) document the actual Postgres tables and distinguish server persistence from browser bag state. The account UI uses explicit checking/authenticated/anonymous/unavailable states, with retry and stale-request cancellation. Persistence verification includes restoring an existing session from a fresh API process against the same database.

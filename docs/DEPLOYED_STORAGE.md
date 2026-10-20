# Deployed Postgres — 2026-10-20

Neon account connection is complete. A dedicated project was created in the account's **Free** organization. Existing FastAPI, SQLAlchemy and psycopg integrations are retained.

| Setting | Value |
|---|---|
| Project | `lbeauty-commerce` |
| Project ID | `muddy-dust-14468350` |
| Organization | `org-wispy-mouse-67791731` |
| Region | `aws-us-east-1`, near the current Vercel `iad1` runtime |
| Postgres | 16 |
| Database / role | `lbeauty` / `lbeauty_owner` |
| Production branch | `production` — `br-twilight-cake-b8cseak8` |
| Preview branch | `preview-login-stripe` — `br-gentle-flower-b8fmavp0` |
| Compute | 0.25 CU minimum/maximum per branch; Free-plan suspension defaults retained |
| Schema | Version 1, six `lb_*` tables |

The preview branch was created before schema initialization and before any customer records existed. Each environment now has its own schema and data.

## Applied migration

`backend/migrations/001_account_checkout.sql` was generated from the existing SQLAlchemy model. It contains additive `CREATE TABLE IF NOT EXISTS` / index statements and an idempotent schema-version insert, serialized by a transaction-level Postgres advisory lock. It was applied through Neon's database tools as one transaction, first to preview and then to production. The local runtime could not resolve Neon hostnames, so no local direct database connection is claimed.

Verified in separate database calls after commit, for **both branches**:

- `lb_users`, `lb_sessions`, `lb_orders`, `lb_payment_events`, `lb_rate_limits`, `lb_schema` exist.
- Schema version is 1.
- Sessions and orders reference users; payment events reference orders.
- Unique email, Stripe session and `(user_id, request_key)` constraints are present.
- At provisioning, user and order counts were zero. Subsequent acceptance tests created artificial customers and sandbox orders; no known public customer passwords were seeded.

## Vercel connection verified

The target is the existing `moya-glow-commerce` project, ID `prj_bh0BVwyX51a47jBCDXIR8wmmVct4`.

| Target | Server-only variable | Neon branch | Git scope |
|---|---|---|---|
| Preview | `DATABASE_URL` as sensitive/Secret | `preview-login-stripe` | Preview environment |
| Production | `DATABASE_URL` as sensitive/Secret | `production` | Production |

Application connections use Neon pooled hosts. Database credentials are not included in source or this document. The temporary local credential file was removed.

The account owner explicitly approved the Neon and Stripe secret transfers on 2026-10-20. Both environment-specific pooled database URLs were then saved successfully as private Vercel secrets. Branch-specific Preview scoping was rejected by Vercel because this project has no connected Git repository; the separate preview database is therefore scoped to the Preview environment. The Production URL is scoped only to Production.

Hosted registration, login, fresh-client session restoration, logout/revocation, ownership and origin checks passed. Production readiness returns HTTP 200 with database and Stripe true. Stripe sandbox success and 3D Secure orders each persisted as paid with one verified webhook event; cancellation and decline remained unpaid. See [hosted release acceptance](../qa/HOSTED_RELEASE_ACCEPTANCE.md) for deployment and test evidence.

Production also has private `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` values. Preview remains protected and has no Stripe secrets: its database works, but payment readiness is intentionally false. The public production URL is the sandbox payment test target. Live keys are rejected by the application.

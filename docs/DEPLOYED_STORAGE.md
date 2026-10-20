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
- User and order counts are zero. No known public customer passwords were seeded.

## Vercel connection pending

The target is the existing `moya-glow-commerce` project, ID `prj_bh0BVwyX51a47jBCDXIR8wmmVct4`.

| Target | Server-only variable | Neon branch | Git scope |
|---|---|---|---|
| Preview | `DATABASE_URL` as sensitive/Secret | `preview-login-stripe` | `feat/hosted-login-stripe` |
| Production | `DATABASE_URL` as sensitive/Secret | `production` | Production |

Application connections use Neon pooled hosts. Database credentials are not included in source or this document. The temporary local credential file was removed.

Automatic approval review rejected the attempted Preview secret write because transferring the specific Neon credential to Vercel requires explicit account-owner permission. Production secret creation was not attempted after that rejection. The next action is approval of the two environment-specific Neon-to-Vercel `DATABASE_URL` secret writes, followed by deployment and hosted registration/login/session/logout acceptance. No workaround for the rejected transfer was used.

The existing database and ERD are implemented. Hosted connectivity and functional login acceptance remain pending. Stripe sandbox configuration and payment acceptance are a later gate; schema provisioning alone does not validate them.

# QA gap report

## Working capabilities

Local full stack: preserved React storefront/cart; FastAPI authentication/login/logout/me; server RBAC for all four staff roles; database products/categories with stable public response shape; product/category create/edit/delete; stock and publication controls; validated atomic JSON ingestion; order list/detail/fulfillment transitions; customer-owned support tickets/replies and staff closure; transactional audit events; dashboard counts; structured errors/logging and correlation IDs; health/readiness; persistent maintenance toggle; login/support rate limiting; Docker volume persistence; CI workflow; Postman collection/environment; API/unit/Chromium suites.

Public static fallback: storefront/search/product detail/cart plus account/login shell. Backend-dependent operations clearly report service unavailability. Existing production project linkage is retained.

## Failed capabilities

Hosted authentication, admin CRUD, live database catalogue updates, support processing and maintenance propagation are unavailable on the static Vercel host because no persistent backend host was available. These features pass against the local FastAPI service. The complete hosted enterprise definition of done is not met.

## Deferred capabilities

All stretch work: CAPTCHA, 2FA, Google login, S3, localization, notifications, multi-currency, richer analytics. Also deferred: self-registration/reset/verification, ticket attachments, account management UI, pagination beyond latest 200, order ingestion from commerce providers, checkout/payment processing (intentionally disabled), final real catalogue. Flutter is reference-only.

## Test failures

Initial 14 API setup errors (SQL placeholder count) and initial lint setup failure (dependency peer conflict) were fixed and rerun. Concurrent Playwright runs also encountered trace-file collisions (fixed with isolated output directories), and one live navigation hit ERR_NETWORK_CHANGED (full rerun passed). No outstanding API/unit/browser assertions failed in completed final runs. Non-failing dependency deprecation warnings remain. See RELEASE_EVIDENCE.md for the exact executed gates and deployment-specific checks; unexecuted manual coverage is not counted as passing.

## Security concerns

No hardcoded runtime accounts, no real payment credentials, no tokens persisted in browser storage. Staff roles are enforced server-side, customer ticket ownership is checked, and audit writes share mutation transactions. Remaining: external security review, MFA/reset lifecycle, password policy review, proxy-aware rate limiting, request/body size limits at ingress, TLS/reverse proxy verification, dependency maintenance and load/abuse testing. The local listener is bound to loopback. Do not expose the development or QA fixture service publicly.

## Deployment concerns

SQLite needs one persistent instance and backups. Serverless ephemeral filesystems cannot safely host this backend. Docker uses a dedicated named volume and nonroot process. No existing backend deployment mechanism or backend credentials were found. The Vercel deployment is an explicitly limited static fallback. No original host was redeployed. CI configuration was added; remote CI results are not inferred from local results.

## Remaining QA estimate

**14–22 engineer-hours**, excluding hosting procurement and final catalogue preparation:
- Persistent HTTPS backend deployment, secrets/operator provisioning, hosted E2E and rollback: 4–6 h.
- Security/ownership/abuse and concurrency/load review: 4–6 h.
- Browser/device/accessibility exploratory QA: 3–5 h.
- Backup/restore, real catalogue import and staff UAT: 3–5 h.

## Recommended next release

Deploy the existing Docker artifact to an authorized persistent HTTPS host, configure backups and trusted edge limits, provision staff users, import operator-supplied catalogue, connect the new Vercel project through same-origin API rewrites, then repeat authenticated hosted E2E and manual QA. Keep all payment and order-placement paths disabled until separately designed and approved. Complete this release before stretch features.

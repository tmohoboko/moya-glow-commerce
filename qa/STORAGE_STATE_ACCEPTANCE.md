# Persistence and state verification — 2026-10-20

Implemented code: aa21fcb61b148aec04608d89c76f51aa759a5644.

- CI https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39373453506 passed both jobs: 23 Chromium tests; 34 SQLite checks with one Postgres-only skip; 35 Postgres 16 checks.
- Fresh-process persistence check restores an existing customer's session against the same database after launching a new Python API process.
- Relationship constraints, HTTPS cookie attributes, hostile-origin logout rejection and lack of foreign credentialed CORS grants passed.
- Browser loading/unavailable/retry-state tests passed, together with the existing registration/login/logout, bag, price, photo and responsive-layout regressions.
- Vercel preview deployment dpl_6NMZdasMsMkHhjn4bWXo7FKmMyR7 is READY. The stable branch preview was visually checked: missing storage shows an unavailable message and retry control; login remains disabled while checking/unavailable. Screenshot: storage-unavailable-state.jpg.
- Data model, state ownership and diagrams: ../docs/DATA_AND_STATE.md.
- The user accepted the header login action and login/register UI before this patch. Hosted registration/login and real sandbox payment remain unaccepted until provider setup is completed.

Provisioning state: no database environment variable was configured. The Vercel integration API denied the existing tmdev scope with 403; no local Vercel CLI credentials were available. A direct Neon connection was offered and is awaiting authorization. No hosted database creation or connection is claimed. Schema, configuration, deployment and automated verification remain engineering-owned; manual acceptance, scope and defect priority remain user-owned.

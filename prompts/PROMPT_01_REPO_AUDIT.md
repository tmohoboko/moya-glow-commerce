# PROMPT 1 — Repo Audit + Release Plan

You are the release engineer for this repository. Goal: ship the existing Moya Glow e-commerce MVP as fast as safely possible.

Do not redesign the product. Do not add optional features. First inspect the repo and establish facts.

Tasks:
1. Identify frontend, backend/API, Docker, tests, package managers, environment files, and deployment config.
2. Determine exact commands for install, dev, test, lint, and production build.
3. Run non-destructive checks only.
4. Detect release blockers: missing files, broken imports, invalid scripts, missing env vars, build errors, obvious secret leakage, Git state problems.
5. Create/update `RELEASE_PLAN.md` with:
   - architecture found
   - exact build commands
   - blockers ranked P0/P1/P2
   - fastest path to Vercel for frontend
   - whether backend is needed for MVP release or can remain separately documented
   - release gates A-E
6. Append command/results summary to `SHIP_LOG.md`.

Rules:
- Make no broad refactors.
- Do not delete features.
- Do not change frameworks.
- Do not touch production credentials.
- Stop only if human authentication/ownership is required.

Finish by printing exactly:
`PROMPT 1 COMPLETE — blockers: <count>; next: PROMPT 2`

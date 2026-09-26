# PROMPT 2 — Make the Production Build Green

Read `RELEASE_PLAN.md` and `SHIP_LOG.md` first.

Goal: pass Gate A with the smallest possible changes.

Tasks:
1. Install dependencies using the repo's lockfile/package manager.
2. Run lint/typecheck/tests if configured.
3. Run the production frontend build.
4. Fix only release-blocking issues. Prefer local/simple fixes over refactors.
5. If FastAPI/backend is present, perform a syntax/import/startup smoke check without expanding scope.
6. Ensure `.gitignore` excludes secrets, caches, build output, local databases, virtualenvs, node_modules.
7. Create `BUILD_REPORT.md` containing commands, failures, fixes, final status, and remaining non-blockers.
8. Append all material changes to `SHIP_LOG.md`.

Acceptance:
- frontend production build exits 0
- no secrets are staged
- app can start locally

Do not add features.

Finish by printing exactly:
`PROMPT 2 COMPLETE — Gate A: PASS|FAIL; next: PROMPT 3`

# PROMPT 3 — Git Hygiene + GitHub Ready

Read prior reports first.

Goal: pass Gate B.

Tasks:
1. Inspect Git status, branches, remote, and latest commits.
2. If this is not initialized, initialize Git safely.
3. Ensure branch is `main`.
4. Ensure all intended source/config/docs are tracked and generated junk/secrets are ignored.
5. Create a concise commit for current release-ready source.
6. If `origin` is missing, configure it ONLY if the repository URL is already known from current repo context. Otherwise stop and print the exact one-line command the human must run.
7. Push `main` if authentication is already available.
8. Never force-push.
9. Create `GIT_RELEASE_CHECK.md` with branch, commit SHA, remote, clean/dirty status, and push result.
10. Append results to `SHIP_LOG.md`.

If remote history conflicts, do not overwrite it. Diagnose and choose the safest merge/rebase path; pause only for an ownership/destructive decision.

Finish by printing exactly:
`PROMPT 3 COMPLETE — Gate B: PASS|BLOCKED; next: PROMPT 4`

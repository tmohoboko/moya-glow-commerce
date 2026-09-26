# PROMPT 6 — Ship Production Release

Goal: get the actual release URL and freeze feature work.

Tasks:
1. Confirm Gate A and Gate B are green.
2. Confirm automated smoke status.
3. Deploy to Vercel production if authentication exists; otherwise execute every non-auth step and provide only the minimal human command/click sequence remaining.
4. After deployment, test the production URL with the automated smoke suite where feasible.
5. Record production URL, deployment date, Git commit SHA, build status, automated smoke result in `RELEASE_EVIDENCE.md`.
6. Commit deployment/test configuration and docs; push normally.
7. Append results to `SHIP_LOG.md`.

Feature freeze: do not add enhancements in this prompt.

Finish by printing exactly:
`PROMPT 6 COMPLETE — Gate C: PASS|BLOCKED; production: <url-or-none>; next: HUMAN QA + PROMPT 7`

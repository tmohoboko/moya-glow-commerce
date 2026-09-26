# PROMPT 8 — Final Release Evidence + Portfolio Handoff

Goal: close the release with audit-friendly evidence suitable for a QA/job portfolio.

Tasks:
1. Verify production URL against current commit.
2. Run production build and automated smoke one final time.
3. Summarize manual QA from `qa/TEST_EVIDENCE.md` and defects from `qa/DEFECT_LOG.csv`.
4. Create/update README with:
   - product summary
   - stack
   - local run
   - test commands
   - production URL
   - QA/release evidence links
5. Create `RELEASE_NOTES.md` with shipped scope, known limitations, test status, commit SHA, deployment URL.
6. Create `PORTFOLIO_EVIDENCE.md` describing demonstrated skills: VS Code, Git/GitHub, Linux, Vercel, Docker if present, API/Postman if present, automated/manual QA, defect management.
7. Ensure working tree is clean and push final docs.
8. Append final status to `SHIP_LOG.md`.

Finish by printing exactly:
`PROMPT 8 COMPLETE — release CLOSED; Gate A-E status: <summary>`

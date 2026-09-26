# PROMPT 7 — QA Defect Fix Loop

Human QA has started. Read `qa/TEST_EVIDENCE.md`, `qa/DEFECT_LOG.csv`, and current release evidence.

Goal: fix only defects discovered during QA, in severity order, without scope creep.

For each OPEN defect:
1. Reproduce it.
2. Classify severity: Blocker/Critical/Major/Minor.
3. Find root cause.
4. Implement smallest safe fix.
5. Add/adjust an automated regression test when practical.
6. Run relevant tests + production build.
7. Update defect row with status, root cause, fix commit/evidence.
8. Do not combine unrelated fixes.

Stop when all Blocker/Critical defects are closed or a human product decision is required.

Append summary to `SHIP_LOG.md`.

Finish by printing exactly:
`PROMPT 7 COMPLETE — open blocker/critical: <count>; next: rerun QA or PROMPT 8`

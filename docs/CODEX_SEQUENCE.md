# Codex Execution Sequence

Run one prompt at a time. Do not combine them unless the current prompt ends cleanly.

1. `PROMPT_01_REPO_AUDIT.md` — facts + blockers
2. `PROMPT_02_BUILD_REPAIR.md` — green build
3. `PROMPT_03_GIT_GITHUB.md` — commit/push
4. `PROMPT_04_VERCEL_PREP.md` — deployment configuration
5. `PROMPT_05_AUTOMATED_SMOKE.md` — automate repetitive QA
6. `PROMPT_06_RELEASE_DEPLOY.md` — production release
7. **Human QA starts here** using `qa/TEST_EVIDENCE.md`
8. `PROMPT_07_DEFECT_FIX_LOOP.md` — only defects found by QA
9. Repeat QA / Prompt 7 until release criteria are met
10. `PROMPT_08_RELEASE_HANDOFF.md` — final evidence + portfolio handoff

## Speed rule

Before QA: accept only changes necessary to build, push, deploy, and automate smoke testing.

After QA starts: accept only changes tied to a defect ID or an explicit release requirement.

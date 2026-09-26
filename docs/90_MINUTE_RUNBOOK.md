# 90-Minute Shipping Runbook

## 0–10 min
- Copy this kit into project root.
- `bash scripts/preflight.sh`
- Run Prompt 1.

## 10–30 min
- Run Prompt 2.
- Gate A must become green.

## 30–45 min
- Run Prompt 3.
- Push `main`.

## 45–60 min
- Run Prompt 4 then Prompt 6 if deploy prerequisites are already satisfied.
- Human performs only auth/account steps Codex cannot perform.

## 60–70 min
- Run Prompt 5 if not already complete.
- Execute automated smoke against production.

## 70–90 min
- Human manual QA using `qa/TEST_EVIDENCE.md`.
- Log every defect in `qa/DEFECT_LOG.csv`.
- Feed Prompt 7 to Codex for Blocker/Critical defects.

If production is not live by minute 60, freeze all non-deployment work until Gate C is green.

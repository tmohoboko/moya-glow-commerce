# PROMPT 5 — Automated Storefront Smoke Tests

Goal: move effort from coding to QA by automating the repetitive checks.

Tasks:
1. Reuse any existing test framework. If none exists, add the lightest practical browser smoke-test setup (prefer Playwright when compatible).
2. Create a small critical-path suite only:
   - homepage loads
   - catalog/product cards render
   - product detail opens if supported
   - add-to-cart works
   - cart quantity/update works if supported
   - remove-from-cart works if supported
   - invalid route does not crash the app
   - no uncaught console errors during critical flow
3. Use robust selectors. Add test IDs only where necessary.
4. Do not rewrite UI just for tests.
5. Run tests against local production-like build where possible.
6. Save test code and a concise `AUTOMATED_TEST_REPORT.md`.
7. Append results to `SHIP_LOG.md`.

Acceptance: critical smoke suite is executable with one documented command.

Finish by printing exactly:
`PROMPT 5 COMPLETE — automated smoke: PASS|FAIL; next: PROMPT 6`

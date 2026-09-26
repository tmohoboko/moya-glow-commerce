# PROMPT 4 — Vercel Production Preparation

Goal: make deployment boring and deterministic.

Tasks:
1. Detect framework (e.g. Vite/React/Next) and root directory.
2. Verify production build one more time.
3. Add/fix only required Vercel configuration.
4. Identify required environment variables and create/update `.env.example` with placeholder values only.
5. Ensure client-side routing works on Vercel if this is an SPA.
6. Ensure API URLs are environment-driven rather than hard-coded localhost values.
7. Document exact Vercel settings in `VERCEL_DEPLOY.md`: framework preset, root directory, install command, build command, output directory, environment variables.
8. If Vercel CLI is installed and already authenticated, deploy production. If not authenticated, do NOT stall: prepare everything and print the shortest human auth/deploy command sequence.
9. Append results to `SHIP_LOG.md`.

Do not add new product scope.

Finish by printing exactly:
`PROMPT 4 COMPLETE — deploy-ready: YES|NO; next: PROMPT 5`

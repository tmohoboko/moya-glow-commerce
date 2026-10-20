#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Require the existing project link; never create a new Vercel project here.
if [[ ! -f .vercel/project.json ]]; then
  printf '%s\n' 'Link this checkout to the existing tmdev/moya-glow-commerce project first.' >&2
  exit 1
fi
node --input-type=module -e '
import {readFileSync} from "node:fs";
const p=JSON.parse(readFileSync(".vercel/project.json","utf8"));
if(!p.projectId || !p.orgId) throw new Error("Incomplete Vercel project link");
if(p.projectName!=="moya-glow-commerce") throw new Error("Verify or refresh the link to the existing moya-glow-commerce project");
'

npx --yes vercel@61.1.0 whoami
npx --yes vercel@61.1.0 project inspect --scope tmdev
npm ci --no-audit --no-fund
node scripts/sync-catalogue.mjs --check
.venv/bin/python -m pytest backend/tests -q
npm run build
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 >/tmp/lbeauty-release-api.log 2>&1 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT
for attempt in {1..40}; do
  kill -0 "$api_pid"
  if curl --fail --silent http://127.0.0.1:8000/api/health >/dev/null; then break; fi
  sleep 0.25
done
QA_RESULTS_PATH=qa/release-local-results.json QA_SCREENSHOT_DIR=qa/release-local npm test

commit=$(git rev-parse HEAD)
printf 'Deploying storefront and backend commit %s\n' "$commit"
npx --yes vercel@61.1.0 deploy --prod --yes --scope tmdev
# A failure here leaves the deployment live and exits nonzero; investigate it.
BASE_URL=https://moya-glow-commerce.vercel.app QA_RESULTS_PATH=qa/release-hosted-results.json QA_SCREENSHOT_DIR=qa/release-hosted npm test
curl --fail --silent https://moya-glow-commerce.vercel.app/api/readiness
printf 'Hosted regression passed for %s. Save the deployment URL and verify a real sandbox checkout and webhook before sign-off.\n' "$commit"

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Require the existing frontend link; never create a new Vercel project here.
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
npm run build
QA_RESULTS_PATH=qa/release-local-results.json QA_SCREENSHOT_DIR=qa/release-local npm test

commit=$(git rev-parse HEAD)
printf 'Deploying frontend commit %s\n' "$commit"
npx --yes vercel@61.1.0 deploy --prod --yes --scope tmdev
# A failure here leaves the deployment live and exits nonzero; investigate it.
BASE_URL=https://moya-glow-commerce.vercel.app QA_RESULTS_PATH=qa/release-hosted-results.json QA_SCREENSHOT_DIR=qa/release-hosted npm test
printf 'Hosted regression passed for frontend release from %s. Save the deployment URL and reports for sign-off.\n' "$commit"

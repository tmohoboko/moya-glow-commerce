#!/usr/bin/env bash
set -euo pipefail
npm run build
npm test
python3 scripts/secret-scan.py
git rev-parse --verify HEAD
git status --short --branch

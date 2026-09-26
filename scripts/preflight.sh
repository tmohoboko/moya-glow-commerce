#!/usr/bin/env bash
set -u
printf '\n== Moya Glow release preflight ==\n'
printf 'PWD: %s\n' "$PWD"
printf '\n-- project markers --\n'
find . -maxdepth 2 \( -name package.json -o -name pyproject.toml -o -name requirements.txt -o -name Dockerfile -o -name docker-compose.yml -o -name vite.config.* -o -name vercel.json \) -print 2>/dev/null | sort
printf '\n-- git --\n'
git status --short --branch 2>&1 || true
printf '\n-- remotes --\n'
git remote -v 2>&1 || true
printf '\n-- runtimes --\n'
node --version 2>/dev/null || true
npm --version 2>/dev/null || true
python3 --version 2>/dev/null || true
docker --version 2>/dev/null || true
printf '\nPreflight complete. Start with prompts/PROMPT_01_REPO_AUDIT.md\n'

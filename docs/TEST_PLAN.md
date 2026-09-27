# Test plan

Run from repository root. Browser tests use a disposable test database; fixture credentials never create accounts in the operator database.

1. `npm ci`; `python3 -m venv .venv`; `.venv/bin/pip install -r backend/requirements.txt`.
2. `npm run lint`; `npm run test:unit`; `npm run test:api`.
3. `npm run build`; `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/google-chrome npm test` (or install Playwright Chromium and omit executable override).
4. `VITE_CATALOG_API=true npm run build`; `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/google-chrome npm run test:enterprise`.
5. `docker compose up --build -d --wait`; `curl -fsS http://127.0.0.1:8013/api/health`; `curl -fsS http://127.0.0.1:8013/api/readiness`.
6. Newman against a disposable database: run `PYTHONPATH=. MOYA_TEST_PORT=8015 .venv/bin/python scripts/enterprise-test-server.py`, then run `npx --yes newman run tests/postman/MoyaGlow.postman_collection.json -e tests/postman/local.postman_environment.json --env-var baseUrl=http://127.0.0.1:8015 --env-var email=admin@example.test --env-var password=browser-test-only-pass`. The password is a test fixture only. Do not run this mutation suite against a real catalogue.
7. Stage coherent changes and run `python3 scripts/secret-scan.py`; `git diff --check`.
8. Read-only live smoke: `BASE_URL=https://moya-glow-enterprise-port.vercel.app PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/google-chrome npm test`.

Coverage: unchanged storefront/search/detail/cart/mobile behavior; exact catalogue contract; positive/negative role matrix; missing auth; wrong credentials; expiry/logout/deactivated accounts; category/product CRUD, publication and referential integrity; ticket ownership, staff reply/close; order transitions; audit atomicity; maintenance and correlation IDs; login limiting; transactional catalogue importer. Enterprise Chromium checks exercise real HTTP service, not API mocks.

Remaining manual checks: Safari/Firefox/mobile devices, screen-reader and keyboard review, concurrent edits/load, backup/restore drill, operator provisioning, TLS/edge configuration, hosted end-to-end backend tests. No money movement is tested or enabled.

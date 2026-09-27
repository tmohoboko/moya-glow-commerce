# Pre-port protection
Repository: /home/tmdev012/Reception/moya-glow-commerce
Remote: https://github.com/tmohoboko/moya-glow-commerce.git
Starting branch: port/adfund-enterprise-prototype (already existed).
Starting commit: d2a9f03. Working tree clean; no patch required. Earlier QA work is preserved in that commit.
No cleanup, reset, force push, or existing deployment linkage changes permitted.
Actual baseline: React/Vite static storefront with 30 mock products, disabled ordering/payments, ten Playwright checks. No FastAPI, catalogue HTTP API, Docker, CI, Stripe or PayFast integration exists in this repository.
New API preserves the exact existing public product object shape. FastAPI and isolated Docker/CI support are additive.

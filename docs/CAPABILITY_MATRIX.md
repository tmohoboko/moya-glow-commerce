# Capability matrix

| Capability | Decision | Tonight implementation |
|---|---|---|
| Moya storefront, brand, bag, disabled checkout | Keep | Existing React views/style/product fields preserved |
| Existing Vercel project | Keep | Original .vercel linkage untouched; isolated deployment staging |
| Auth / account / staff authentication | Port | FastAPI opaque expiring bearer sessions, scrypt, React login/account |
| Admin role permissions | Port | Server-side permissions for admin, catalogue_manager, support_agent, analyst; customer ownership |
| Catalogue CRUD, stock, publication | Port | Native commerce schema, migrations, JSON import; not a donor fundraising model |
| Orders | Port | Read/detail/validated fulfillment transitions; no order placement or charging |
| Support ticket conversations | Port | Owned tickets, replies, staff close/reopen |
| Maintenance | Port | Persisted toggle; public API 503; staff recovery stays available |
| Operational visibility | Port | Audit events, safe JSON errors/logging, request IDs, health/readiness |
| Dashboard | Port | Aggregate product/order/support counts; no invented revenue |
| Rate limiting | Port | Database counters for login/support, socket peer; single-instance scope |
| QA delivery | Port | API, unit, browser, Postman and Docker gates, CI |
| Password reset/registration/email verification | Defer | Operator-provisioned accounts only |
| CAPTCHA / 2FA / Google login | Defer | Must-have gates and deployment take priority |
| Notifications / localization / S3 / multi-currency | Defer | Existing donor patterns documented only |
| Flutter runtime/rewrite | Reject | Reference only; future client adapts to Moya API |
| Fundraising / campaign / donation | Reject | No domain model, API, UI or dependencies |
| Wallet / crypto / withdrawal / exchange | Reject | No port |
| New payment gateways / live money movement | Reject | Checkout and payments remain disabled |
| Laravel/PHP deployment | Reject | React + FastAPI only |

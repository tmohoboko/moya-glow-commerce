# Port decisions

1. Preserve the actual shipped repository, including its static preview mode. There was no existing FastAPI service, Docker/CI setup or Stripe/PayFast integration to preserve. New service is additive; payment activation is out of scope.
2. Adapt donor behaviors, not donor source or framework. Purchased source stays outside Git. All new commerce implementation is native Python/React.
3. SQLite with foreign keys and versioned SQL migrations fits a single-instance prototype. Use a persistent volume. Do not deploy SQLite on ephemeral serverless storage. Move to managed PostgreSQL before horizontal scaling.
4. Public `/api/products` returns the exact original six fields: id, name, price, category, image, description. Publication/stock are staff fields. Existing 30 mock products are opt-in seeds, not a final Moya catalogue. Inventory does not enable checkout.
5. `VITE_CATALOG_API=true` enables API-backed storefront (Docker does this). Static Vercel fallback retains original seed catalogue and functional cart. It does not claim a working hosted backend.
6. Opaque bearer tokens are held only in React memory; no tokens in localStorage/cookies. Refresh requires sign-in. Server sessions expire after eight hours; logout revokes the session. Passwords use salted scrypt. No default operator credentials or public account creation.
7. Admin has all resources; catalogue_manager has products/categories; support_agent has orders/support; analyst has aggregate dashboard only. Customers can access only their own support tickets. No UI-only authorization.
8. Write + audit commit in the same database transaction. Audit excludes passwords, tokens, ticket body and personal profile details. Operational logs record correlation ID, method, status and duration; error responses do not leak stack traces or validation inputs.
9. Fulfillment status transitions are limited and transactional. Payments remain references only; no provider actions or payment-state changes are exposed.
10. Maintenance blocks catalogue reads, including API-driven storefront content. Health, readiness and staff recovery endpoints remain reachable. Static fallback cannot receive maintenance changes without a deployed backend; disclose this limitation.
11. Login/support limiting uses socket peer and database counters (15 logins or 30 support writes per five minutes). Forwarded headers are ignored. At a reverse proxy this groups users by proxy; move to a trusted edge limiter before wider rollout.
12. No stretch capabilities until the full must-have release, including hosted backend, is validated.

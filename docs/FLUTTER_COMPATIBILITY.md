# Flutter compatibility

AdFund Flutter 3.6.0 is a requirements/reference client only. It is not included in builds, dependencies or deployments.

Inspected `lib/backend/services/api_endpoint.dart` and `lib/views/screens/auth/login/signin_screen.dart`. Donor sign-in uses an email/password form with validation and a loading flow. Endpoints use `/api/v1/user/login`, `/user/logout`, `/user/profile`, and OTP/password reset endpoints. Google sign-in and language endpoints exist; campaign and money routes are explicitly rejected.

Future Moya mobile client mapping:

| Client behavior | Moya REST endpoint / behavior |
|---|---|
| Sign in | POST /api/auth/login with email/password; generic 401 |
| Account | GET /api/auth/me; Bearer token required |
| Sign out | POST /api/auth/logout; invalidates server session |
| Browse | GET /api/products and /api/products/{id}; six-field product contract |
| Support | POST/GET /api/support/tickets; GET detail; POST messages |
| Staff | /api/admin/* with server permission checks |
| Error display | JSON detail + request_id; retry hints for 429/503 |

Flutter must adapt endpoint names and response parsing; it is not wire-compatible with the donor. Use secure platform token storage for a future mobile client and re-authenticate on 401. Do not use donor campaign/payment endpoints. Password reset, registration, Google login, localization, push notifications, offline sync, deep links and attachment upload are deferred. Mobile layout is responsive React tonight, not Flutter parity.

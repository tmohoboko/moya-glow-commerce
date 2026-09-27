# Isolated deployment and operator handoff

Original root `.vercel/project.json` belongs to `moya-glow-commerce`; never deploy the enterprise build through it. Tonight's isolated staging directory is ignored `.deploy-enterprise/`, linked to `moya-glow-enterprise-port` only. Purchased donor files and backend databases are not uploaded.

To redeploy only this new static project after updating its staged source:

```sh
npx vercel --prod --yes --cwd .deploy-enterprise
```

Verify staged `.vercel/project.json` has projectName `moya-glow-enterprise-port` before using this command. A fresh checkout does not contain the ignored staging directory; recreate it with frontend source/manifests/config, then `npx vercel link --yes --project moya-glow-enterprise-port --cwd .deploy-enterprise`. Do not copy root `.vercel` or `.env` files.

Full-stack hosting is blocked by the absence of an authorized persistent backend service/deployment workflow, not by build or Docker health failures. No backend URL or credentials were invented. There is no honest one-command cloud deployment until a host/account is selected and authorized.

The exact next command for a provisioned host with this checkout and Docker is:

```sh
docker compose up --build -d --wait
```

This starts the app on loopback port 8013 with a dedicated persistent volume. Configure the host's HTTPS reverse proxy to that port and a backup schedule, then provision the operator:

```sh
docker compose exec app python -m backend.app.manage create-user --email operator@example.com --role admin
```

Replace that email with the real operator. For the separate Vercel frontend, set build variable `VITE_CATALOG_API=true` and add an `/api/:path*` rewrite to the actual authorized HTTPS backend **before** the SPA rewrite. Preserve bearer Authorization headers; do not enable unrestricted CORS. Redeploy the new project and rerun hosted tests. Alternatively serve the complete React/FastAPI app directly from the persistent HTTPS host.

Rollback is confined to the new project: select its previous deployment in Vercel. Backend: preserve the named volume, stop only `moya-enterprise-port`, and restore a tested SQLite backup. Never use `docker compose down -v` on operator data. No automatic rollback of SQL migrations is claimed.

## Google OIDC setup

Create a **Web application** OAuth client in Google Cloud Console / Google Auth Platform. Configure the consent screen and add test users while the app is in testing. Register the exact authorized redirect URI, including scheme, host, port and path:

- Local Docker: `http://localhost:8013/api/auth/google/callback` (open the app using `localhost`, not `127.0.0.1`, for a consistent cookie host).
- Hosted: `https://YOUR_AUTHORIZED_HOST/api/auth/google/callback`.

Backend environment variables:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
```

Set these through the host's secret manager or ignored local `.env` file. Never put them in `VITE_*` variables, tracked files, command arguments, screenshots or logs. Compose forwards these three variables; apply with `docker compose up -d --build --wait`. Blank/missing configuration, an insecure non-loopback URI, incorrect callback path, userinfo, query string or fragment disables the provider. HTTPS is required except loopback HTTP for local development. No separate frontend return origin is supported: callback and frontend must share the public origin. With Vercel proxying a hosted backend, register the Vercel-origin callback and proxy all `/api/auth/google/*` paths, preserving cookies and Authorization headers. Do not deploy that routing until the backend exists.

Google state expires after five minutes, is bound to an HttpOnly SameSite=Lax browser cookie, and is consumed before code exchange. PKCE S256 and an ID-token nonce are used. Authlib verifies RS256 signatures against Google's HTTPS JWKS plus issuer, audience, expiry, authorized party and nonce. Verified email is mandatory. Identity mapping retains stable `sub`; conflicting links and inactive accounts are rejected. A 60-second, single-use HttpOnly SameSite=Strict cookie hands off to the account page; the ordinary bearer session is issued by a same-origin POST requiring `X-Moya-OAuth: 1`. No bearer token is placed in URLs or browser storage. Cookies are Secure under HTTPS. Redirect destinations are fixed and ignore user-supplied return URLs.

The Google callback contains an authorization code in its query string. Application logs omit URLs/query strings, Uvicorn access logging is disabled, and HTTP client logs are limited to warnings. Configure any external reverse proxy/APM to redact callback queries, cookies, Authorization headers and token endpoint bodies. Do not enable OAuth debug logging.

Validation: automated API tests use generated signing keys and mocked Google token/JWKS responses; browser tests cover disabled/enabled controls, safe static fallback and successful/expired handoff handling. Real Google interaction requires operator-supplied credentials and a configured consent screen. Hosted OAuth remains blocked by backend hosting; this patch does not deploy or invent credentials.

References: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect), [Google OIDC reference](https://developers.google.com/identity/openid-connect/reference), [Authlib web clients](https://docs.authlib.org/en/latest/oauth2/client/web/).

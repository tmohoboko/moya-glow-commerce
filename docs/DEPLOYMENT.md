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

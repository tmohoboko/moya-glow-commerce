# Replace the temporary catalogue

`CATALOG_READY_FOR_REPLACEMENT` was reached after importer/API/browser verification. The original 30 illustrative mock products remain in seed data; no final catalogue was invented.

JSON array fields: required id, name, price, category; optional image, description, stock (default 0), published (default true). Public API output stays id/name/price/category/image/description. IDs must be unique URL-safe identifiers. Price is ZAR, finite and nonnegative. Use HTTPS or a local image path. An empty import is rejected.

Validate without writing:

```sh
.venv/bin/python -m backend.app.import_catalogue /absolute/path/catalogue.json
```

Provision an operator if needed (interactive password; never store it in Git):

```sh
docker compose exec app python -m backend.app.manage create-user --email operator@example.com --role admin
```

For the running Docker service, copy the supplied file and validate/apply:

```sh
docker compose cp /absolute/path/catalogue.json app:/tmp/catalogue.json
docker compose exec app python -m backend.app.import_catalogue /tmp/catalogue.json
docker compose exec app python -m backend.app.import_catalogue /tmp/catalogue.json --apply --actor-email operator@example.com --unpublish-missing
```

Substitute the actual operator email. `--unpublish-missing` retires absent seed products without deleting order references. All rows and the import audit commit together. No uploads or credentials are embedded in frontend assets. Back up the database before real imports; CLI deployment remains operator controlled.

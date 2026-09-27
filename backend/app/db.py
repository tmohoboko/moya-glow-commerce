"""SQLite persistence for the single-instance prototype; versioned SQL migrations."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_PERMISSIONS = {
    'admin': ['products', 'categories', 'orders', 'support', 'audit', 'settings', 'dashboard'],
    'catalogue_manager': ['products', 'categories'],
    'support_agent': ['orders', 'support'],
    'analyst': ['dashboard'],
    'customer': [],
}

@contextmanager
def connection():
    path = Path(os.getenv('MOYA_DATABASE', 'data/moya.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def migrate():
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)')
        for path in sorted((ROOT / 'migrations').glob('*.sql')):
            if not db.execute('SELECT 1 FROM schema_migrations WHERE version=?', (path.name,)).fetchone():
                # Migration and its version marker commit atomically.
                db.executescript('BEGIN IMMEDIATE;\n' + path.read_text() + '\n' +
                    "INSERT INTO schema_migrations VALUES ('" + path.name + "');\nCOMMIT;")
        for role, resources in ROLE_PERMISSIONS.items():
            db.execute('INSERT OR IGNORE INTO roles VALUES (?)', (role,))
            db.executemany('INSERT OR IGNORE INTO permissions VALUES (?,?)', [(role, r) for r in resources])
        if os.getenv('MOYA_SEED_DEMO', 'false') == 'true' and not db.execute("SELECT 1 FROM app_settings WHERE key='seeded'").fetchone():
            for product in json.loads((ROOT / 'seed-products.json').read_text()):
                category = product['category'].lower().replace(' ', '-')
                db.execute('INSERT OR IGNORE INTO categories VALUES (?,?)', (category, product['category']))
                db.execute('INSERT OR IGNORE INTO products VALUES (?,?,?,?,?,?,?,?)', (
                    product['id'], product['name'], product['price'], category, product['image'], product['description'], 99, 1))
            db.execute("INSERT INTO app_settings VALUES ('seeded','true')")

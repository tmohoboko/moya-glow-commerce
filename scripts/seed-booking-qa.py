"""Seed ONLY the disposable GitHub Actions SQLite database, never a hosted DB."""
import os
import time
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from backend.app import db
from backend.app.security import password_hash

assert os.getenv('CI') == 'true'
assert not os.getenv('VERCEL')
assert os.getenv('DATABASE_URL') == 'sqlite:////tmp/lbeauty-browser-qa.sqlite3'
with db.transaction() as connection:
    user_id = str(uuid.uuid4())
    connection.execute(db.users.insert().values(id=user_id,email='salon-qa@example.com',
        password_hash=password_hash('ci-only-salon-password'),created_at=int(time.time())))
    connection.execute(db.staff.insert().values(user_id=user_id,created_at=int(time.time())))

"""Disposable browser-test service. Never uses the operator database."""
import os
import tempfile
from pathlib import Path
import uvicorn
from backend.app.db import migrate, connection
from backend.app.security import password_hash

with tempfile.TemporaryDirectory(prefix='moya-browser-') as directory:
    os.environ['MOYA_DATABASE']=str(Path(directory)/'test.sqlite3')
    os.environ['MOYA_SEED_DEMO']='true'
    migrate()
    with connection() as db:
        # These accounts exist only in this disposable localhost test process.
        for role in ['admin','catalogue_manager','support_agent','analyst','customer']:
            db.execute('INSERT INTO users VALUES (?,?,?,?,1)',(role,role+'@example.test',password_hash('browser-test-only-pass'),role))
        db.execute("INSERT INTO orders(id,total) VALUES ('test-order',149)")
        db.execute("INSERT INTO order_items(order_id,name,quantity,unit_price) VALUES ('test-order','Demo item',1,149)")
    uvicorn.run('backend.app.main:app',host='127.0.0.1',port=int(os.getenv('MOYA_TEST_PORT','8014')),proxy_headers=False)

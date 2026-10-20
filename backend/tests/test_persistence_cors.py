"""Storage survives a fresh API process; browser origin restrictions stay intact."""
import json
import os
import subprocess
import sys

from backend.app import db
from backend.tests.test_api import PASSWORD, register

# Reuse the isolated SQLite / dedicated local Postgres fixtures from the API suite.
from backend.tests.test_api import client, database  # noqa: F401


def test_account_and_session_survive_fresh_process(client):
    user = register(client)
    token = client.cookies.get("lb_session")
    script = """
import json, sys
from fastapi.testclient import TestClient
from backend.app.main import app
data=json.load(sys.stdin)
with TestClient(app, headers={'Origin':'http://testserver'}) as client:
    client.cookies.set('lb_session', data['token'])
    response=client.get('/api/auth/me')
    assert response.status_code==200, response.status_code
    assert response.json()==data['user']
"""
    result = subprocess.run([sys.executable, "-c", script], input=json.dumps({"token": token, "user": user}),
                            capture_output=True, text=True, timeout=25, env=os.environ.copy())
    assert result.returncode == 0, result.stderr


def test_cross_origin_logout_does_not_revoke_session(client):
    register(client)
    assert client.post("/api/auth/logout", headers={"Origin": "https://other.example"}).status_code == 403
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_foreign_origin_is_not_granted_credentialed_cors(client):
    response = client.options("/api/auth/login", headers={"Origin": "https://other.example",
        "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})
    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers
    # Same-origin browser requests need no CORS permission headers.
    assert client.post("/api/auth/login", json={"email": "absent@example.com", "password": PASSWORD}).status_code == 401


def test_https_session_cookie_is_secure(client):
    with type(client)(client.app, base_url="https://testserver", headers={"Origin": "https://testserver"}) as secure_client:
        response = secure_client.post("/api/auth/register", json={"email": "secure@example.com", "password": PASSWORD})
        assert response.status_code == 201
        assert "; Secure" in response.headers["set-cookie"]
        assert secure_client.get("/api/auth/me").status_code == 200


def test_foreign_keys_enforce_real_user_relationships(client):
    from sqlalchemy.exc import IntegrityError
    import pytest
    with pytest.raises(IntegrityError):
        with db.engine().begin() as connection:
            connection.execute(db.sessions.insert().values(token_hash="f"*64, user_id="absent", expires_at=9999999999))

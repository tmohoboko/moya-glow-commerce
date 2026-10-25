import concurrent.futures
import hashlib
import hmac
import json
import os
import time
import uuid
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from backend.app import db, payments
from backend.app.main import CATALOGUE, app
from backend.app.security import COOKIE

ORIGIN = {"Origin": "http://testserver"}
PASSWORD = "test-password-for-local-tests"


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    db.engine.cache_clear()
    database_url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path}/test.sqlite3")
    if os.getenv("TEST_DATABASE_URL"):
        parsed = urlsplit(database_url)
        assert parsed.hostname == "127.0.0.1" and parsed.path == "/lbeauty_test", "Only the dedicated local CI test database is allowed."
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_unit_fixture")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_unit_fixture")
    monkeypatch.setenv("ENABLE_LEGACY_COMMERCE", "1")
    yield
    if db.engine.cache_info().currsize:
        engine = db.engine()
        if os.getenv("TEST_DATABASE_URL"):
            db.metadata.drop_all(engine)
        engine.dispose()
    db.engine.cache_clear()


@pytest.fixture
def client():
    with TestClient(app, headers=ORIGIN) as result:
        yield result


def register(client, email="customer@example.com"):
    result = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert result.status_code == 201, result.text
    return result.json()


def cart(**overrides):
    return {"request_key": str(uuid.uuid4()), "items": [{"id": CATALOGUE[0]["id"], "quantity": 2}], **overrides}


@pytest.fixture
def checkout(client, monkeypatch):
    register(client)
    calls = []
    def create(order, email, base):
        calls.append({"order": dict(order), "email": email, "base": base})
        return {"id": "cs_test_"+order["id"], "url": "https://checkout.stripe.com/c/pay/cs_test_"+order["id"]}
    monkeypatch.setattr(payments, "create_checkout", create)
    return calls


def deliver(client, order_id, event_id="evt_test_one", event_type="checkout.session.completed", **changes):
    with db.transaction() as connection:
        order = connection.execute(select(db.orders).where(db.orders.c.id == order_id)).mappings().one()
    session = {"id": order["stripe_session"], "livemode": False, "metadata": {"order_id": order_id},
               "client_reference_id": order_id, "amount_total": order["amount"], "currency": "zar", "payment_status": "paid", **changes}
    event = {"id": event_id, "object": "event", "livemode": False, "type": event_type, "data": {"object": session}}
    payload = json.dumps(event).encode()
    timestamp = int(time.time())
    signature = hmac.new(b"whsec_unit_fixture", f"{timestamp}.".encode()+payload, hashlib.sha256).hexdigest()
    return client.post("/api/stripe/webhook", content=payload, headers={"Stripe-Signature": f"t={timestamp},v1={signature}", "Content-Type": "application/json"})


def test_register_login_logout_and_private_cookie(client):
    user = register(client, "CUSTOMER@example.com")
    assert user["email"] == "customer@example.com"
    assert client.get("/api/auth/me").json() == user
    raw_token = client.cookies.get(COOKIE)
    with db.transaction() as connection:
        stored = connection.execute(select(db.users.c.password_hash)).scalar_one()
        session_hash = connection.execute(select(db.sessions.c.token_hash)).scalar_one()
    assert PASSWORD not in stored and raw_token != session_hash
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": user["email"], "password": PASSWORD}).status_code == 200
    assert client.cookies.get(COOKIE) != raw_token
    response = client.post("/api/auth/login", json={"email": user["email"], "password": PASSWORD})
    assert "HttpOnly" in response.headers["set-cookie"] and "SameSite=lax" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"


def test_expired_and_revoked_sessions(client):
    register(client)
    token = client.cookies.get(COOKIE)
    client.post("/api/auth/logout")
    client.cookies.set(COOKIE, token)
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()
    register(client, "another@example.com")
    with db.transaction() as connection:
        connection.execute(update(db.sessions).values(expires_at=0))
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("origin", ["https://evil.example", "null", ""])
def test_auth_csrf_rejected(client, origin):
    assert client.post("/api/auth/register", json={"email": "customer@example.com", "password": PASSWORD}, headers={"Origin": origin}).status_code == 403


def test_failed_logins_count_and_passwords_not_echoed(client):
    for _ in range(15):
        assert client.post("/api/auth/login", json={"email": "absent@example.com", "password": PASSWORD}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "absent@example.com", "password": PASSWORD}).status_code == 429
    invalid = client.post("/api/auth/register", json={"email": "invalid", "password": "private"})
    assert invalid.status_code == 422 and "private" not in invalid.text


def test_duplicate_email_case_insensitive(client):
    register(client)
    assert client.post("/api/auth/register", json={"email": "CUSTOMER@example.com", "password": PASSWORD}).status_code == 409


def test_catalogue_and_configuration_fail_closed(client, monkeypatch):
    assert len(client.get("/api/products").json()) == 46
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/readiness").json()["ready"]
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_never_allowed")
    assert client.get("/api/readiness").status_code == 503
    assert client.post("/api/checkout", json=cart()).status_code == 503
    db.engine().dispose()
    db.engine.cache_clear()
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    assert client.get("/api/readiness").json()["database"] is False
    assert client.get("/api/health").status_code == 200


def test_server_totals_and_checkout_retry(client, checkout):
    body = cart()
    result = client.post("/api/checkout", json=body)
    assert result.status_code == 200, result.text
    assert client.post("/api/checkout", json=body).json() == result.json()
    assert len(checkout) == 1
    order = client.get("/api/orders/"+result.json()["order_id"]).json()
    assert order["amount"] == 90000 and order["currency"] == "zar" and order["status"] == "pending"
    body["items"][0]["quantity"] = 3
    assert client.post("/api/checkout", json=body).status_code == 409


@pytest.mark.parametrize("items", [[], [{"id": "unknown", "quantity": 1}], [{"id": CATALOGUE[0]["id"], "quantity": 0}], [{"id": CATALOGUE[0]["id"], "quantity": 1.2}], [{"id": CATALOGUE[0]["id"], "quantity": True}], [{"id": CATALOGUE[0]["id"], "quantity": 100}], [{"id": CATALOGUE[0]["id"], "quantity": 1, "price": 1}], [{"id": CATALOGUE[0]["id"], "quantity": 1}]*2])
def test_invalid_cart_cannot_reach_stripe(client, checkout, items):
    assert client.post("/api/checkout", json=cart(items=items)).status_code == 422
    assert checkout == []


def test_quotes_cannot_be_paid_at_base_price(client, checkout):
    for product in CATALOGUE:
        if product.get("priceFrom"):
            assert client.post("/api/checkout", json=cart(items=[{"id": product["id"], "quantity": 1}])).status_code == 409
    assert checkout == []


def test_order_ownership(client, checkout):
    order_id = client.post("/api/checkout", json=cart()).json()["order_id"]
    client.post("/api/auth/logout")
    assert client.get("/api/orders/"+order_id).status_code == 401
    register(client, "other@example.com")
    assert client.get("/api/orders/"+order_id).status_code == 404
    assert client.get("/api/orders").json() == []


def test_real_signature_verification_and_idempotent_payment(client, checkout):
    order_id = client.post("/api/checkout", json=cart()).json()["order_id"]
    assert client.post("/api/stripe/webhook", content=b'{}', headers={"Stripe-Signature": "invalid"}).status_code == 400
    # An unpaid completion does not confirm payment.
    assert deliver(client, order_id, "evt_unpaid", payment_status="unpaid").status_code == 200
    assert client.get("/api/orders/"+order_id).json()["status"] == "pending"
    for _ in range(2):
        assert deliver(client, order_id).status_code == 200
    # A late expiry event cannot undo a confirmed payment.
    assert deliver(client, order_id, "evt_late", "checkout.session.expired", payment_status="unpaid").status_code == 200
    assert client.get("/api/orders/"+order_id).json()["status"] == "paid"
    with db.transaction() as connection:
        assert len(connection.execute(select(db.events)).all()) == 3


@pytest.mark.parametrize("changes", [{"amount_total": 1}, {"currency": "usd"}, {"id": "cs_test_wrong"}, {"livemode": True}, {"client_reference_id": "wrong"}])
def test_signed_mismatches_rejected(client, checkout, changes):
    order_id = client.post("/api/checkout", json=cart()).json()["order_id"]
    assert deliver(client, order_id, **changes).status_code == 400
    assert client.get("/api/orders/"+order_id).json()["status"] == "pending"


def test_stripe_failure_leaves_retryable_order(client, checkout, monkeypatch):
    create = payments.create_checkout
    from fastapi import HTTPException
    def failure(*args):
        raise HTTPException(502, "Stripe is unavailable.")
    monkeypatch.setattr(payments, "create_checkout", failure)
    body = cart()
    assert client.post("/api/checkout", json=body).status_code == 502
    pending = client.get("/api/orders").json()
    assert len(pending) == 1 and pending[0]["status"] == "pending"
    monkeypatch.setattr(payments, "create_checkout", create)
    assert client.post("/api/checkout", json=body).json()["order_id"] == pending[0]["id"]


def test_unknown_api_route_is_json(client):
    result = client.get("/api/missing")
    assert result.status_code == 404 and "application/json" in result.headers["content-type"]


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Postgres locking integration check runs in CI")
def test_concurrent_checkout_and_event_delivery(client, checkout):
    body = cart()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post("/api/checkout", json=body), range(2)))
    assert all(result.status_code == 200 for result in results)
    assert len(checkout) == 1
    order_id = results[0].json()["order_id"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: deliver(client, order_id), range(2)))
    assert all(result.status_code == 200 for result in results)
    with db.transaction() as connection:
        assert len(connection.execute(select(db.events)).all()) == 1

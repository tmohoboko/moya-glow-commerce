import json
import os
import time
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictInt
from sqlalchemy import delete, select, text, update
from starlette.concurrency import run_in_threadpool

from . import payments
from .db import dialect_insert, events, orders, sessions, transaction, users
from .security import (COOKIE, DUMMY_HASH, check_origin, current_user, digest,
                       issue_session, password_hash, password_matches, throttle)

CATALOGUE = json.loads((Path(__file__).parent / "catalogue.json").read_text())
BY_ID = {item["id"]: item for item in CATALOGUE}
app = FastAPI(title="L Beauty services and appointments", docs_url=None, redoc_url=None, openapi_url=None)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128)


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(max_length=120)
    quantity: Annotated[StrictInt, Field(ge=1, le=99)]


class Checkout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: uuid.UUID
    items: list[Item] = Field(min_length=1, max_length=46)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo submitted credentials or private booking details.
    detail = "Please check your entries. Use a valid email and a password of 12–128 characters." if request.url.path.startswith("/api/auth/") else "Please check the required fields and try again."
    return JSONResponse({"detail": detail}, status_code=422)


@app.middleware("http")
async def protect_api(request, call_next):
    if request.url.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path != "/api/stripe/webhook":
        try:
            check_origin(request)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def rate_limit(request, bucket, limit):
    # Separate transaction: failed logins must still count against the limit.
    with transaction() as connection:
        allowed = throttle(connection, request, bucket, limit)
    if not allowed:
        raise HTTPException(429, "Too many attempts. Please wait five minutes.", headers={"Retry-After": "300"})


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "lbeauty", "payment_mode": "test"}


@app.get("/api/readiness")
def readiness():
    database_ready = False
    try:
        with transaction() as connection:
            database_ready = connection.execute(text("SELECT version FROM lb_schema WHERE version=1")).scalar() == 1
    except HTTPException:
        pass
    stripe_ready = payments.configured()
    return JSONResponse({"ready": database_ready and stripe_ready, "database": database_ready,
                         "stripe": stripe_ready, "payment_mode": "test"}, status_code=200 if database_ready and stripe_ready else 503)


@app.get("/api/products")
def catalogue():
    return CATALOGUE


@app.post("/api/auth/register", status_code=201)
def register(body: Credentials, request: Request, response: Response):
    rate_limit(request, "register", 5)
    email = str(body.email).lower()
    with transaction() as connection:
        user_id = str(uuid.uuid4())
        inserted = connection.execute(dialect_insert(connection, users).values(
            id=user_id, email=email, password_hash=password_hash(body.password), created_at=int(time.time())
        ).on_conflict_do_nothing(index_elements=[users.c.email]).returning(users.c.id)).scalar()
        if not inserted:
            raise HTTPException(409, "Unable to create this account. Try logging in instead.")
        issue_session(connection, response, request, user_id)
    return {"id": user_id, "email": email}


@app.post("/api/auth/login")
def login(body: Credentials, request: Request, response: Response):
    rate_limit(request, "login", 15)
    with transaction() as connection:
        user = connection.execute(select(users).where(users.c.email == str(body.email).lower())).mappings().first()
        valid = password_matches(body.password, user["password_hash"] if user else DUMMY_HASH)
        if not valid or not user:
            raise HTTPException(401, "Email or password is incorrect.")
        connection.execute(delete(sessions).where(sessions.c.token_hash == digest(request.cookies.get(COOKIE, ""))))
        issue_session(connection, response, request, user["id"])
        return {"id": user["id"], "email": user["email"]}


@app.get("/api/auth/me")
def me(request: Request):
    with transaction() as connection:
        return current_user(connection, request)


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response):
    with transaction() as connection:
        connection.execute(delete(sessions).where(sessions.c.token_hash == digest(request.cookies.get(COOKIE, ""))))
    response.delete_cookie(COOKIE, path="/", httponly=True, secure=bool(os.getenv("VERCEL")), samesite="lax")


def order_view(order):
    return {key: order[key] for key in ("id", "items", "amount", "currency", "status", "created_at")}


@app.get("/api/orders")
def my_orders(request: Request):
    with transaction() as connection:
        user = current_user(connection, request)
        result = connection.execute(select(orders).where(orders.c.user_id == user["id"]).order_by(orders.c.created_at.desc()).limit(100)).mappings()
        return [order_view(order) for order in result]


@app.get("/api/orders/{order_id}")
def get_order(order_id: uuid.UUID, request: Request):
    with transaction() as connection:
        user = current_user(connection, request)
        order = connection.execute(select(orders).where(orders.c.id == str(order_id), orders.c.user_id == user["id"])).mappings().first()
        if not order:
            raise HTTPException(404, "Order not found.")
        return order_view(order)


@app.post("/api/checkout")
def checkout(body: Checkout, request: Request):
    if os.getenv("ENABLE_LEGACY_COMMERCE") != "1":
        raise HTTPException(410, "Choose a service and book an appointment before paying its invoice.")
    rate_limit(request, "checkout", 30)
    items, seen = [], set()
    for item in sorted(body.items, key=lambda row: row.id):
        product = BY_ID.get(item.id)
        if not product or item.id in seen:
            raise HTTPException(422, "Please refresh your bag and try again.")
        if product.get("priceFrom"):
            raise HTTPException(409, f"{product['name']} needs a confirmed quote before payment. Please remove it from your test bag.")
        seen.add(item.id)
        items.append({"id": item.id, "name": product["name"], "quantity": item.quantity,
                      "unit_amount": round(product["price"] * 100)})
    if not payments.configured():
        raise HTTPException(503, "Test checkout is not configured yet.")
    with transaction() as connection:
        user = current_user(connection, request)
        connection.execute(dialect_insert(connection, orders).values(
            id=str(uuid.uuid4()), user_id=user["id"], request_key=str(body.request_key), items=items,
            amount=sum(item["quantity"]*item["unit_amount"] for item in items), currency="zar",
            status="pending", created_at=int(time.time())).on_conflict_do_nothing(index_elements=[orders.c.user_id, orders.c.request_key]))
    # Persist before Stripe: retries keep the same Stripe idempotency key.
    with transaction() as connection:
        order = connection.execute(select(orders).where(orders.c.user_id == user["id"], orders.c.request_key == str(body.request_key)).with_for_update()).mappings().one()
        if order["items"] != items:
            raise HTTPException(409, "Your bag changed. Please start a new checkout.")
        if order["status"] != "pending":
            raise HTTPException(409, "This checkout has finished. Please start a new checkout.")
        if order["checkout_url"]:
            return {"order_id": order["id"], "url": order["checkout_url"]}
        base_url = str(request.base_url).rstrip("/")
        if os.getenv("VERCEL"):
            base_url = "https://" + request.url.netloc
        session = payments.create_checkout(order, user["email"], base_url)
        connection.execute(update(orders).where(orders.c.id == order["id"]).values(stripe_session=session["id"], checkout_url=session["url"]))
        return {"order_id": order["id"], "url": session["url"]}


@app.post("/api/stripe/webhook")
async def webhook(request: Request):
    # Signature verification requires the original bytes.
    payload = await request.body()
    if len(payload) > 256000:
        raise HTTPException(413, "Webhook too large.")
    event = payments.verify_event(payload, request.headers.get("stripe-signature", ""))
    return await run_in_threadpool(apply_event, event)


def apply_event(event):
    if event.get("livemode") is not False:
        raise HTTPException(400, "Only sandbox events are accepted.")
    event_type = event["type"]
    if event_type not in ("checkout.session.completed", "checkout.session.expired", "checkout.session.async_payment_succeeded", "checkout.session.async_payment_failed"):
        return {"received": True}
    session = event["data"]["object"]
    order_id = session.get("metadata", {}).get("order_id")
    if not order_id:
        return {"received": True}
    with transaction() as connection:
        order = connection.execute(select(orders).where(orders.c.id == order_id).with_for_update()).mappings().first()
        if not order:
            return {"received": True}
        if connection.execute(select(events.c.id).where(events.c.id == event["id"])).first():
            return {"received": True}
        if session.get("livemode") is not False or session.get("id") != order["stripe_session"] or session.get("amount_total") != order["amount"] or session.get("currency") != order["currency"] or session.get("client_reference_id") != order["id"]:
            raise HTTPException(400, "Webhook does not match this order.")
        status = order["status"]
        if event_type in ("checkout.session.completed", "checkout.session.async_payment_succeeded") and session.get("payment_status") == "paid":
            status = "paid"
        elif status != "paid" and event_type == "checkout.session.expired":
            status = "expired"
        elif status != "paid" and event_type == "checkout.session.async_payment_failed":
            status = "failed"
        connection.execute(update(orders).where(orders.c.id == order["id"]).values(status=status))
        connection.execute(events.insert().values(id=event["id"], order_id=order["id"], created_at=int(time.time())))
    return {"received": True}


from .bookings import router as booking_router
app.include_router(booking_router)

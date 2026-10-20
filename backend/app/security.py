import hashlib
import hmac
import os
import secrets
import time

from fastapi import HTTPException
from sqlalchemy import delete, select

from .db import dialect_insert, limits, sessions, users

COOKIE = "lb_session"
SESSION_SECONDS = 8 * 60 * 60


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    encoded = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"{salt}:{encoded}"


DUMMY_HASH = password_hash("unused-dummy-password")


def password_matches(password, encoded):
    return hmac.compare_digest(password_hash(password, encoded.split(":")[0]), encoded)


def check_origin(request):
    origin = request.headers.get("origin", "")
    expected = str(request.base_url).rstrip("/")
    # TLS terminates at Vercel; never accept an insecure cross-origin request.
    if os.getenv("VERCEL"):
        expected = "https://" + request.url.netloc
    if not origin or origin != expected:
        raise HTTPException(403, "Please submit this request from the L Beauty site.")


def current_user(connection, request):
    token = request.cookies.get(COOKIE, "")
    user = connection.execute(select(users.c.id, users.c.email).join(
        sessions, sessions.c.user_id == users.c.id).where(
        sessions.c.token_hash == digest(token), sessions.c.expires_at > int(time.time()))).mappings().first()
    if not user:
        raise HTTPException(401, "Please log in to continue.")
    return dict(user)


def issue_session(connection, response, request, user_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    connection.execute(delete(sessions).where(sessions.c.expires_at <= now))
    connection.execute(sessions.insert().values(token_hash=digest(token), user_id=user_id, expires_at=now+SESSION_SECONDS))
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=bool(os.getenv("VERCEL")) or request.url.scheme == "https", samesite="lax", path="/")


def throttle(connection, request, bucket, limit=15, identity=""):
    now = int(time.time())
    address = request.client.host if request.client else "unknown"
    if os.getenv("VERCEL"):
        address = request.headers.get("x-vercel-forwarded-for", address).split(",")[0].strip()
    key = digest(f"{bucket}:{address}:{identity}:{now // 300}")
    connection.execute(delete(limits).where(limits.c.expires_at < now))
    count = connection.execute(dialect_insert(connection, limits).values(
        key=key, count=1, expires_at=now+300).on_conflict_do_update(
            index_elements=[limits.c.key], set_={"count": limits.c.count+1}).returning(limits.c.count)).scalar_one()
    # Caller commits this transaction even on a failed login.
    return count <= limit

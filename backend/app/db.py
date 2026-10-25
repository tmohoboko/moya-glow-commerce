"""Durable hosted Postgres; SQLite is available only for local development/tests."""
import os
import threading
from contextlib import contextmanager
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import (JSON, BigInteger, Column, ForeignKey, Integer, MetaData,
                        String, Table, UniqueConstraint, create_engine, event, text)
from sqlalchemy.exc import SQLAlchemyError

metadata = MetaData()
users = Table("lb_users", metadata,
    Column("id", String(36), primary_key=True), Column("email", String(254), unique=True, nullable=False),
    Column("password_hash", String(256), nullable=False), Column("created_at", BigInteger, nullable=False))
sessions = Table("lb_sessions", metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", String(36), ForeignKey("lb_users.id"), nullable=False),
    Column("expires_at", BigInteger, nullable=False, index=True))
orders = Table("lb_orders", metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("lb_users.id"), nullable=False, index=True),
    Column("request_key", String(36), nullable=False), Column("items", JSON, nullable=False),
    Column("amount", Integer, nullable=False), Column("currency", String(3), nullable=False),
    Column("status", String(24), nullable=False), Column("created_at", BigInteger, nullable=False),
    Column("stripe_session", String(255), unique=True), Column("checkout_url", String(2048)),
    UniqueConstraint("user_id", "request_key"))
events = Table("lb_payment_events", metadata,
    Column("id", String(255), primary_key=True),
    Column("order_id", String(36), ForeignKey("lb_orders.id"), nullable=False),
    Column("created_at", BigInteger, nullable=False))
limits = Table("lb_rate_limits", metadata,
    Column("key", String(64), primary_key=True), Column("count", Integer, nullable=False),
    Column("expires_at", BigInteger, nullable=False, index=True))
schema = Table("lb_schema", metadata, Column("version", Integer, primary_key=True))
staff = Table("lb_staff", metadata,
    Column("user_id", String(36), ForeignKey("lb_users.id"), primary_key=True),
    Column("created_at", BigInteger, nullable=False))
calendar_settings = Table("lb_calendar_settings", metadata,
    Column("id", String(20), primary_key=True), Column("value", JSON, nullable=False))
quotes = Table("lb_quotes", metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("lb_users.id"), index=True),
    Column("request_key", String(36), nullable=False),
    Column("service_id", String(120), nullable=False), Column("service_name", String(200), nullable=False),
    Column("contact_name", String(100), nullable=False), Column("phone", String(40), nullable=False),
    Column("notes", String(2000), nullable=False), Column("source", String(20), nullable=False),
    Column("amount", Integer), Column("duration", Integer), Column("buffer", Integer),
    Column("terms", String(2000)), Column("status", String(20), nullable=False),
    Column("revision", Integer, nullable=False), Column("created_at", BigInteger, nullable=False),
    Column("expires_at", BigInteger), UniqueConstraint("user_id", "request_key"))
bookings = Table("lb_bookings", metadata,
    Column("id", String(36), primary_key=True),
    Column("quote_id", String(36), ForeignKey("lb_quotes.id"), unique=True, nullable=False),
    Column("user_id", String(36), ForeignKey("lb_users.id"), index=True),
    Column("starts_at", BigInteger, nullable=False, index=True), Column("ends_at", BigInteger, nullable=False),
    Column("blocked_until", BigInteger, nullable=False), Column("status", String(20), nullable=False),
    Column("created_at", BigInteger, nullable=False))
invoices = Table("lb_invoices", metadata,
    Column("id", String(36), primary_key=True), Column("number", String(40), unique=True, nullable=False),
    Column("booking_id", String(36), ForeignKey("lb_bookings.id"), unique=True, nullable=False),
    Column("user_id", String(36), ForeignKey("lb_users.id"), index=True),
    Column("order_id", String(36), ForeignKey("lb_orders.id"), unique=True),
    Column("amount", Integer, nullable=False), Column("currency", String(3), nullable=False),
    Column("status", String(20), nullable=False), Column("created_at", BigInteger, nullable=False))
calendar_blocks = Table("lb_calendar_blocks", metadata,
    Column("id", String(36), primary_key=True), Column("starts_at", BigInteger, nullable=False),
    Column("ends_at", BigInteger, nullable=False), Column("label", String(100), nullable=False),
    Column("status", String(20), nullable=False))
booking_audit = Table("lb_booking_audit", metadata,
    Column("id", String(36), primary_key=True), Column("actor_id", String(36), ForeignKey("lb_users.id"), nullable=False),
    Column("entity_id", String(36), nullable=False), Column("action", String(40), nullable=False),
    Column("created_at", BigInteger, nullable=False))
_lock = threading.Lock()


@lru_cache(maxsize=1)
def engine():
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not url:
        if os.getenv("VERCEL"):
            raise HTTPException(503, "Account setup is not ready. Please try again later.")
        url = "sqlite:///./lbeauty.sqlite3"
    if url.startswith(("postgres://", "postgresql://")):
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    if os.getenv("VERCEL") and not url.startswith("postgresql+psycopg://"):
        raise HTTPException(503, "A persistent Postgres database is required.")
    options = {"connect_args": {"check_same_thread": False, "timeout": 15}} if url.startswith("sqlite:") else {
        "connect_args": {"connect_timeout": 10}, "pool_size": 2, "max_overflow": 1, "pool_pre_ping": True}
    result = create_engine(url, **options)
    if result.dialect.name == "sqlite":
        @event.listens_for(result, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")
    # Additive bootstrap for local development. Hosted changes are also shipped
    # as explicit versioned migrations and applied before the new release.
    with _lock, result.begin() as connection:
        if result.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(69020261020)"))
        metadata.create_all(connection)
        insert = dialect_insert(connection, schema).values(version=1).on_conflict_do_nothing()
        connection.execute(insert)
        connection.execute(dialect_insert(connection, calendar_settings).values(
            id="salon", value={"enabled": True, "week": [[540, 1020] for _ in range(7)]}
        ).on_conflict_do_nothing())
        connection.execute(dialect_insert(connection, schema).values(version=2).on_conflict_do_nothing())
        # One-time activation of the owner-approved 09:00–17:00 daily schedule.
        # Preserve any calendar settings that were already customized.
        version_three = connection.execute(select(schema.c.version).where(schema.c.version == 3)).first()
        if not version_three:
            current_hours = connection.execute(select(calendar_settings.c.value).where(
                calendar_settings.c.id == "salon"
            )).scalar_one_or_none()
            if current_hours == {"enabled": False, "week": [None] * 7}:
                connection.execute(update(calendar_settings).where(
                    calendar_settings.c.id == "salon"
                ).values(value={"enabled": True, "week": [[540, 1020] for _ in range(7)]}))
            connection.execute(dialect_insert(connection, schema).values(version=3).on_conflict_do_nothing())
    return result


def dialect_insert(connection, table):
    if connection.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    return insert(table)


@contextmanager
def transaction():
    try:
        with engine().begin() as connection:
            yield connection
    except SQLAlchemyError:
        # Never include connection URLs or SQL parameters in responses/logs.
        raise HTTPException(503, "Our account service is temporarily unavailable.") from None

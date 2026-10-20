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
    # Version 1 is additive and serialized across serverless instances. Future
    # schema changes need explicit versioned migrations, never drop/recreate.
    with _lock, result.begin() as connection:
        if result.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(69020261020)"))
        metadata.create_all(connection)
        insert = dialect_insert(connection, schema).values(version=1).on_conflict_do_nothing()
        connection.execute(insert)
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

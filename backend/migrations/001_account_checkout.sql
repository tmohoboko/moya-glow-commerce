-- Generated from backend/app/db.py for initial Postgres schema v1.
-- Apply as one transaction using a direct/admin connection. Non-destructive.
BEGIN;

SELECT pg_advisory_xact_lock(69020261020);

CREATE TABLE IF NOT EXISTS lb_rate_limits (
	key VARCHAR(64) NOT NULL, 
	count INTEGER NOT NULL, 
	expires_at BIGINT NOT NULL, 
	PRIMARY KEY (key)
);

CREATE INDEX IF NOT EXISTS ix_lb_rate_limits_expires_at ON lb_rate_limits (expires_at);

CREATE TABLE IF NOT EXISTS lb_schema (
	version SERIAL NOT NULL, 
	PRIMARY KEY (version)
);

CREATE TABLE IF NOT EXISTS lb_users (
	id VARCHAR(36) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS lb_orders (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	request_key VARCHAR(36) NOT NULL, 
	items JSON NOT NULL, 
	amount INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	created_at BIGINT NOT NULL, 
	stripe_session VARCHAR(255), 
	checkout_url VARCHAR(2048), 
	PRIMARY KEY (id), 
	UNIQUE (user_id, request_key), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id), 
	UNIQUE (stripe_session)
);

CREATE INDEX IF NOT EXISTS ix_lb_orders_user_id ON lb_orders (user_id);

CREATE TABLE IF NOT EXISTS lb_sessions (
	token_hash VARCHAR(64) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	expires_at BIGINT NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id)
);

CREATE INDEX IF NOT EXISTS ix_lb_sessions_expires_at ON lb_sessions (expires_at);

CREATE TABLE IF NOT EXISTS lb_payment_events (
	id VARCHAR(255) NOT NULL, 
	order_id VARCHAR(36) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES lb_orders (id)
);

INSERT INTO lb_schema(version) VALUES (1) ON CONFLICT (version) DO NOTHING;

COMMIT;

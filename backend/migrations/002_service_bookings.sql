-- Additive only: preserve every existing account, order and payment event.
BEGIN;
SELECT pg_advisory_xact_lock(69020261020);

CREATE TABLE IF NOT EXISTS lb_calendar_blocks (
	id VARCHAR(36) NOT NULL, 
	starts_at BIGINT NOT NULL, 
	ends_at BIGINT NOT NULL, 
	label VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS lb_calendar_settings (
	id VARCHAR(20) NOT NULL, 
	value JSON NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS lb_booking_audit (
	id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	entity_id VARCHAR(36) NOT NULL, 
	action VARCHAR(40) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES lb_users (id)
);

CREATE TABLE IF NOT EXISTS lb_quotes (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	request_key VARCHAR(36) NOT NULL, 
	service_id VARCHAR(120) NOT NULL, 
	service_name VARCHAR(200) NOT NULL, 
	contact_name VARCHAR(100) NOT NULL, 
	phone VARCHAR(40) NOT NULL, 
	notes VARCHAR(2000) NOT NULL, 
	source VARCHAR(20) NOT NULL, 
	amount INTEGER, 
	duration INTEGER, 
	buffer INTEGER, 
	terms VARCHAR(2000), 
	status VARCHAR(20) NOT NULL, 
	revision INTEGER NOT NULL, 
	created_at BIGINT NOT NULL, 
	expires_at BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, request_key), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id)
);

CREATE INDEX IF NOT EXISTS ix_lb_quotes_user_id ON lb_quotes (user_id);

CREATE TABLE IF NOT EXISTS lb_staff (
	user_id VARCHAR(36) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id)
);

CREATE TABLE IF NOT EXISTS lb_bookings (
	id VARCHAR(36) NOT NULL, 
	quote_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	starts_at BIGINT NOT NULL, 
	ends_at BIGINT NOT NULL, 
	blocked_until BIGINT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (quote_id), 
	FOREIGN KEY(quote_id) REFERENCES lb_quotes (id), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id)
);

CREATE INDEX IF NOT EXISTS ix_lb_bookings_user_id ON lb_bookings (user_id);

CREATE INDEX IF NOT EXISTS ix_lb_bookings_starts_at ON lb_bookings (starts_at);

CREATE TABLE IF NOT EXISTS lb_invoices (
	id VARCHAR(36) NOT NULL, 
	number VARCHAR(40) NOT NULL, 
	booking_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	order_id VARCHAR(36), 
	amount INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at BIGINT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (number), 
	UNIQUE (booking_id), 
	FOREIGN KEY(booking_id) REFERENCES lb_bookings (id), 
	FOREIGN KEY(user_id) REFERENCES lb_users (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES lb_orders (id)
);

CREATE INDEX IF NOT EXISTS ix_lb_invoices_user_id ON lb_invoices (user_id);

INSERT INTO lb_calendar_settings (id,value) VALUES ('salon','{"enabled":false,"week":[null,null,null,null,null,null,null]}'::json) ON CONFLICT DO NOTHING;

INSERT INTO lb_schema (version) VALUES (2) ON CONFLICT DO NOTHING;
COMMIT;

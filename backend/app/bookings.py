"""Quote-led, single-calendar salon booking. All money is integer ZAR cents."""
import time
import uuid
from typing import Literal
from contextlib import contextmanager
from datetime import date, datetime, time as day_time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt
from sqlalchemy import select, update, text

from . import db, payments
from .security import current_user

router = APIRouter(prefix="/api")
TZ = ZoneInfo("Africa/Johannesburg")


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuoteRequest(Input):
    request_key: uuid.UUID
    service_id: str = Field(min_length=1, max_length=120)
    contact_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=40)
    notes: str = Field(default="", max_length=2000)


class IssueQuote(Input):
    amount: StrictInt = Field(ge=0, le=10000000)
    duration: StrictInt = Field(ge=15, le=480)
    buffer: StrictInt = Field(ge=0, le=120)
    terms: str = Field(min_length=1, max_length=2000)
    revision: StrictInt = Field(ge=0)


class Revision(Input):
    revision: StrictInt = Field(ge=1)


class Reserve(Input):
    quote_id: uuid.UUID
    starts_at: StrictInt
    revision: StrictInt = Field(ge=1)


class Move(Input):
    starts_at: StrictInt


class Settings(Input):
    enabled: StrictBool
    # Monday=0 ... Sunday=6, null means closed; integer minutes since midnight.
    week: list[list[StrictInt] | None] = Field(min_length=7, max_length=7)


class Block(Input):
    starts_at: StrictInt
    ends_at: StrictInt
    label: str = Field(min_length=1, max_length=100)


class WalkIn(QuoteRequest, IssueQuote):
    starts_at: StrictInt


@contextmanager
def calendar_transaction():
    with db.transaction() as connection:
        # SQLite has no SELECT FOR UPDATE. Acquire its write lock before reads.
        if connection.dialect.name == "sqlite":
            connection.execute(text("BEGIN IMMEDIATE"))
        connection.execute(select(db.calendar_settings).where(
            db.calendar_settings.c.id == "salon").with_for_update()).one()
        yield connection


def require_staff(connection, request):
    user = current_user(connection, request)
    if not connection.execute(select(db.staff).where(db.staff.c.user_id == user["id"])).first():
        raise HTTPException(403, "Salon staff access is required.")
    return user


def owned(connection, table, entity_id, user_id):
    row = connection.execute(select(table).where(table.c.id == str(entity_id), table.c.user_id == user_id)).mappings().first()
    if not row:
        raise HTTPException(404, "Record not found.")
    return row


def audit(connection, actor, entity_id, action):
    connection.execute(db.booking_audit.insert().values(id=str(uuid.uuid4()), actor_id=actor,
        entity_id=entity_id, action=action, created_at=int(time.time())))


def quote_view(row):
    result = dict(row)
    result["number"] = "LBQ-" + row["id"].upper()
    result["expired"] = bool(row["expires_at"] and row["expires_at"] <= int(time.time()))
    return result


def invoice_view(connection, row):
    result = dict(row)
    order = connection.execute(select(db.orders).where(db.orders.c.id == row["order_id"])).mappings().first() if row["order_id"] else None
    paid = bool(order and order["status"] == "paid")
    result["payment_status"] = "refund_required" if paid and row["status"] == "void" else "paid" if paid else "not_due" if row["amount"] == 0 else order["status"] if order else "unpaid"
    result["receipt_number"] = "LBR-" + row["id"].upper() if paid else None
    result["payment_mode"] = "test"
    return result


def booking_view(connection, row):
    result = dict(row)
    quote = connection.execute(select(db.quotes).where(db.quotes.c.id == row["quote_id"])).mappings().one()
    result["quote"] = quote_view(quote)
    invoice = connection.execute(select(db.invoices).where(db.invoices.c.booking_id == row["id"])).mappings().one()
    result["invoice"] = invoice_view(connection, invoice)
    result["timezone"] = str(TZ)
    return result


def settings_view(connection):
    return connection.execute(select(db.calendar_settings.c.value).where(db.calendar_settings.c.id == "salon")).scalar_one()


def validate_date(day):
    today = datetime.now(TZ).date()
    if day < today or day > today + timedelta(days=90):
        raise HTTPException(422, "Choose a date within the next 90 days.")


def hours(connection, day):
    validate_date(day)
    settings = settings_view(connection)
    window = settings["week"][day.weekday()] if settings["enabled"] else None
    if not window:
        return None
    midnight = datetime.combine(day, day_time(), TZ)
    return tuple(int((midnight + timedelta(minutes=minute)).timestamp()) for minute in window)


def overlaps(connection, start, end, exclude=None):
    active = select(db.bookings.c.id).where(db.bookings.c.status.in_(["confirmed", "completed"]),
        db.bookings.c.starts_at < end, db.bookings.c.blocked_until > start)
    if exclude:
        active = active.where(db.bookings.c.id != exclude)
    return bool(connection.execute(active).first() or connection.execute(select(db.calendar_blocks.c.id).where(
        db.calendar_blocks.c.status == "active", db.calendar_blocks.c.starts_at < end,
        db.calendar_blocks.c.ends_at > start)).first())


def check_slot(connection, quote, start, exclude=None):
    try:
        local = datetime.fromtimestamp(start, TZ)
    except (ValueError, OverflowError, OSError):
        raise HTTPException(422, "Choose a valid appointment time.") from None
    window = hours(connection, local.date())
    end = start + quote["duration"] * 60
    blocked = end + quote["buffer"] * 60
    if not window or start <= int(time.time()) or local.minute % 15 or local.second or start < window[0] or blocked > window[1]:
        raise HTTPException(409, "This time is outside available salon hours. Choose another slot.")
    if overlaps(connection, start, blocked, exclude):
        raise HTTPException(409, "This time has just been taken. Choose another available slot.")
    return end, blocked


def active_quote(quote):
    if quote["status"] != "accepted" or quote["expires_at"] <= int(time.time()):
        raise HTTPException(409, "Accept a current quotation before choosing your appointment.")


def make_booking(connection, quote, start, actor):
    active_quote(quote)
    existing = connection.execute(select(db.bookings).where(db.bookings.c.quote_id == quote["id"])).mappings().first()
    if existing:
        if existing["starts_at"] == start and existing["status"] == "confirmed":
            return booking_view(connection, existing)
        raise HTTPException(409, "This quotation already has a booking. Use reschedule or request a new quotation.")
    end, blocked = check_slot(connection, quote, start)
    booking_id, invoice_id, now = str(uuid.uuid4()), str(uuid.uuid4()), int(time.time())
    connection.execute(db.bookings.insert().values(id=booking_id, quote_id=quote["id"], user_id=quote["user_id"],
        starts_at=start, ends_at=end, blocked_until=blocked, status="confirmed", created_at=now))
    connection.execute(db.invoices.insert().values(id=invoice_id, number="LBI-"+invoice_id.upper(), booking_id=booking_id,
        user_id=quote["user_id"], amount=quote["amount"], currency="zar", status="issued", created_at=now))
    audit(connection, actor, booking_id, "booking_confirmed")
    return booking_view(connection, connection.execute(select(db.bookings).where(db.bookings.c.id == booking_id)).mappings().one())


@router.get("/booking/config")
def public_config():
    with db.transaction() as connection:
        return {**settings_view(connection), "timezone": str(TZ), "workflow": "quotation_then_booking", "payment_mode": "test"}


@router.get("/staff/access")
def staff_access(request: Request):
    with db.transaction() as connection:
        require_staff(connection, request)
    return {"staff": True}


@router.post("/quotes", status_code=201)
def request_quote(body: QuoteRequest, request: Request):
    from .main import BY_ID, rate_limit
    rate_limit(request, "quotation", 20)
    service = BY_ID.get(body.service_id)
    if not service:
        raise HTTPException(422, "Choose a service from the catalogue.")
    with db.transaction() as connection:
        user = current_user(connection, request)
        values = dict(user_id=user["id"], request_key=str(body.request_key), service_id=service["id"],
            service_name=service["name"], contact_name=body.contact_name.strip(), phone=body.phone.strip(), notes=body.notes.strip())
        if len(values["contact_name"]) < 2 or len(values["phone"]) < 7:
            raise HTTPException(422, "Enter your name and contact number.")
        connection.execute(db.dialect_insert(connection, db.quotes).values(id=str(uuid.uuid4()), **values,
            source="online", status="requested", revision=0, created_at=int(time.time())
        ).on_conflict_do_nothing(index_elements=[db.quotes.c.user_id, db.quotes.c.request_key]))
        quote = connection.execute(select(db.quotes).where(db.quotes.c.user_id == user["id"], db.quotes.c.request_key == str(body.request_key))).mappings().one()
        if any(quote[key] != value for key, value in values.items()):
            raise HTTPException(409, "Your request changed. Start a new quotation request.")
        return quote_view(quote)


@router.get("/quotes")
def my_quotes(request: Request):
    with db.transaction() as connection:
        user = current_user(connection, request)
        return [quote_view(row) for row in connection.execute(select(db.quotes).where(db.quotes.c.user_id == user["id"]).order_by(db.quotes.c.created_at.desc()).limit(200)).mappings()]


@router.post("/staff/quotes/{quote_id}/issue")
def issue_quote(quote_id: uuid.UUID, body: IssueQuote, request: Request):
    with calendar_transaction() as connection:
        user = require_staff(connection, request)
        quote = connection.execute(select(db.quotes).where(db.quotes.c.id == str(quote_id))).mappings().first()
        if not quote:
            raise HTTPException(404, "Quotation not found.")
        if quote["status"] not in ("requested", "issued") or quote["revision"] != body.revision:
            raise HTTPException(409, "This quotation changed. Refresh before editing.")
        connection.execute(update(db.quotes).where(db.quotes.c.id == str(quote_id)).values(
            **body.model_dump(exclude={"revision"}), revision=body.revision+1,
            status="issued", expires_at=int(time.time())+7*86400))
        audit(connection, user["id"], str(quote_id), "quote_issued")
        return quote_view(connection.execute(select(db.quotes).where(db.quotes.c.id == str(quote_id))).mappings().one())


@router.post("/quotes/{quote_id}/accept")
def accept_quote(quote_id: uuid.UUID, body: Revision, request: Request):
    with calendar_transaction() as connection:
        user = current_user(connection, request)
        quote = owned(connection, db.quotes, quote_id, user["id"])
        if quote["status"] not in ("issued", "accepted") or quote["revision"] != body.revision or quote["expires_at"] <= int(time.time()):
            raise HTTPException(409, "This quotation changed or expired. Ask the salon for a new quotation.")
        connection.execute(update(db.quotes).where(db.quotes.c.id == str(quote_id)).values(status="accepted"))
        audit(connection, user["id"], str(quote_id), "quote_accepted")
        return {"accepted": True}


@router.post("/quotes/{quote_id}/decline")
def decline_quote(quote_id: uuid.UUID, request: Request):
    with calendar_transaction() as connection:
        user = current_user(connection, request)
        quote = owned(connection, db.quotes, quote_id, user["id"])
        if quote["status"] not in ("requested", "issued"):
            raise HTTPException(409, "This quotation can no longer be declined.")
        connection.execute(update(db.quotes).where(db.quotes.c.id == str(quote_id)).values(status="declined"))
        audit(connection, user["id"], str(quote_id), "quote_declined")
    return {"declined": True}


@router.get("/availability")
def availability(quote_id: uuid.UUID, day: date, request: Request, view: Literal["day", "week"] = "day"):
    with db.transaction() as connection:
        user = current_user(connection, request)
        quote = owned(connection, db.quotes, quote_id, user["id"])
        existing = connection.execute(select(db.bookings).where(db.bookings.c.quote_id == str(quote_id))).mappings().first()
        if not existing:
            active_quote(quote)
        elif existing["status"] != "confirmed":
            raise HTTPException(409, "This appointment cannot be rescheduled.")
        validate_date(day)
        result = calendar_availability(connection, day, view, (quote["duration"]+quote["buffer"])*60, existing["id"] if existing else None)
        return {**result, "duration":quote["duration"], "buffer":quote["buffer"]}


def calendar_availability(connection, day, view, duration, exclude_booking=None):
    first = day-timedelta(days=day.weekday()) if view == "week" else day
    days = [first+timedelta(days=i) for i in range(7 if view == "week" else 1)]
    range_start = int(datetime.combine(first, day_time(), TZ).timestamp())
    range_end = range_start+len(days)*86400
    # Fetch busy intervals once for the whole range rather than querying for
    # every candidate slot; only times, never customer details, are returned.
    query = select(db.bookings.c.starts_at, db.bookings.c.blocked_until).where(
        db.bookings.c.status.in_(["confirmed", "completed"]),
        db.bookings.c.starts_at < range_end, db.bookings.c.blocked_until > range_start)
    if exclude_booking:
        query = query.where(db.bookings.c.id != exclude_booking)
    busy = [tuple(row) for row in connection.execute(query)]
    busy += [tuple(row) for row in connection.execute(select(db.calendar_blocks.c.starts_at, db.calendar_blocks.c.ends_at).where(
        db.calendar_blocks.c.status == "active", db.calendar_blocks.c.starts_at < range_end, db.calendar_blocks.c.ends_at > range_start))]
    today = datetime.now(TZ).date()
    result = []
    now = time.time()
    for date_value in days:
        window = hours(connection,date_value) if today <= date_value <= today+timedelta(days=90) else None
        available, unavailable = [], []
        if window:
            for start in range(window[0],window[1]-duration+1,15*60):
                occupied = start <= now or any(a < start+duration and b > start for a,b in busy)
                (unavailable if occupied else available).append(start)
        result.append({"day":date_value.isoformat(),"slots":available,"unavailable":unavailable,"closed":window is None})
    selected = next(row for row in result if row["day"] == day.isoformat())
    return {"day":day.isoformat(),"view":view,"timezone":str(TZ),"slots":selected["slots"],
            "days":result}


@router.get("/calendar/availability")
def public_calendar_availability(day: date, response: Response, view: Literal["day", "week"] = "day"):
    today = datetime.now(TZ).date()
    if day < today-timedelta(days=365) or day > today+timedelta(days=90):
        raise HTTPException(422, "Choose a calendar date within the last year or next 90 days.")
    response.headers["Cache-Control"] = "no-store"
    with db.transaction() as connection:
        # Publish time availability only. Never return names, booking IDs or notes.
        return calendar_availability(connection, day, view, 15*60)



@router.post("/bookings", status_code=201)
def reserve(body: Reserve, request: Request):
    with calendar_transaction() as connection:
        user = current_user(connection, request)
        quote = owned(connection, db.quotes, body.quote_id, user["id"])
        if quote["revision"] != body.revision:
            raise HTTPException(409, "Your quotation changed. Refresh before booking.")
        return make_booking(connection, quote, body.starts_at, user["id"])


@router.get("/bookings")
def my_bookings(request: Request):
    with db.transaction() as connection:
        user = current_user(connection, request)
        return [booking_view(connection, row) for row in connection.execute(select(db.bookings).where(
            db.bookings.c.user_id == user["id"]).order_by(db.bookings.c.starts_at.desc()).limit(200)).mappings()]


def change_booking(booking_id, request, action, starts_at=None, staff_action=False):
    with calendar_transaction() as connection:
        user = require_staff(connection, request) if staff_action else current_user(connection, request)
        booking = connection.execute(select(db.bookings).where(db.bookings.c.id == str(booking_id))).mappings().first() if staff_action else owned(connection, db.bookings, booking_id, user["id"])
        if not booking:
            raise HTTPException(404, "Booking not found.")
        if booking["status"] != "confirmed":
            raise HTTPException(409, "This appointment has already been closed.")
        if not staff_action and booking["starts_at"] <= time.time():
            raise HTTPException(409, "Contact the salon to change an appointment that has already started.")
        if action in ("completed", "no_show") and booking["starts_at"] > time.time():
            raise HTTPException(409, "This appointment has not started yet.")
        if action == "reschedule":
            quote = connection.execute(select(db.quotes).where(db.quotes.c.id == booking["quote_id"])).mappings().one()
            end, blocked = check_slot(connection, quote, starts_at, booking["id"])
            values = {"starts_at": starts_at, "ends_at": end, "blocked_until": blocked}
        else:
            values = {"status": action}
        connection.execute(update(db.bookings).where(db.bookings.c.id == booking["id"]).values(**values))
        if action == "cancelled":
            connection.execute(update(db.invoices).where(db.invoices.c.booking_id == booking["id"]).values(status="void"))
        audit(connection, user["id"], booking["id"], "booking_"+action)
        return booking_view(connection, connection.execute(select(db.bookings).where(db.bookings.c.id == booking["id"])).mappings().one())


@router.post("/bookings/{booking_id}/cancel")
def cancel(booking_id: uuid.UUID, request: Request):
    return change_booking(booking_id, request, "cancelled")


@router.post("/bookings/{booking_id}/reschedule")
def reschedule(booking_id: uuid.UUID, body: Move, request: Request):
    return change_booking(booking_id, request, "reschedule", body.starts_at)


@router.post("/staff/bookings/{booking_id}/{action}")
def staff_change(booking_id: uuid.UUID, action: str, request: Request):
    if action not in ("cancelled", "completed", "no_show"):
        raise HTTPException(404, "Action not found.")
    return change_booking(booking_id, request, action, staff_action=True)


@router.put("/staff/calendar")
def configure_calendar(body: Settings, request: Request):
    for window in body.week:
        if window is not None and (len(window) != 2 or not 0 <= window[0] < window[1] <= 1440 or any(minute % 15 for minute in window)):
            raise HTTPException(422, "Opening hours must use 15-minute intervals and end after they start.")
    with calendar_transaction() as connection:
        user = require_staff(connection, request)
        connection.execute(update(db.calendar_settings).where(db.calendar_settings.c.id == "salon").values(value=body.model_dump()))
        audit(connection, user["id"], "salon", "calendar_updated")
    return body


@router.get("/staff/calendar")
def staff_calendar(day: date, request: Request, view: Literal["day", "week"] = "day"):
    with db.transaction() as connection:
        require_staff(connection, request)
        first = day-timedelta(days=day.weekday()) if view == "week" else day
        start = int(datetime.combine(first, day_time(), TZ).timestamp())
        end = start + (7 if view == "week" else 1)*86400
        appointments = [booking_view(connection, row) for row in connection.execute(select(db.bookings).where(
            db.bookings.c.starts_at < end, db.bookings.c.blocked_until > start).order_by(db.bookings.c.starts_at)).mappings()]
        blocks = [dict(row) for row in connection.execute(select(db.calendar_blocks).where(
            db.calendar_blocks.c.starts_at < end, db.calendar_blocks.c.ends_at > start, db.calendar_blocks.c.status == "active")).mappings()]
        pending = [quote_view(row) for row in connection.execute(select(db.quotes).where(
            db.quotes.c.status.in_(["requested", "issued"])).order_by(db.quotes.c.created_at).limit(200)).mappings()]
        return {"settings": settings_view(connection), "bookings": appointments, "blocks": blocks, "quotes": pending, "timezone": str(TZ), "view": view, "first_day": first.isoformat()}


@router.post("/staff/blocks", status_code=201)
def block_calendar(body: Block, request: Request):
    if body.ends_at <= body.starts_at or body.ends_at-body.starts_at > 7*86400:
        raise HTTPException(422, "Choose a block of up to seven days, ending after it starts.")
    with calendar_transaction() as connection:
        user = require_staff(connection, request)
        if overlaps(connection, body.starts_at, body.ends_at):
            raise HTTPException(409, "This block overlaps an existing appointment or block.")
        block_id = str(uuid.uuid4())
        connection.execute(db.calendar_blocks.insert().values(id=block_id, **body.model_dump(), status="active"))
        audit(connection, user["id"], block_id, "calendar_blocked")
    return {"id": block_id}


@router.post("/staff/blocks/{block_id}/release")
def release_block(block_id: uuid.UUID, request: Request):
    with calendar_transaction() as connection:
        user = require_staff(connection, request)
        result = connection.execute(update(db.calendar_blocks).where(db.calendar_blocks.c.id == str(block_id)).values(status="released"))
        if not result.rowcount:
            raise HTTPException(404, "Block not found.")
        audit(connection, user["id"], str(block_id), "block_released")
    return {"released": True}


@router.post("/staff/walk-ins", status_code=201)
def walk_in(body: WalkIn, request: Request):
    from .main import BY_ID
    service = BY_ID.get(body.service_id)
    if not service:
        raise HTTPException(422, "Choose a service from the catalogue.")
    with calendar_transaction() as connection:
        user = require_staff(connection, request)
        # The staff member owns this guest record; guests never receive another
        # customer's account. The request key makes a repeated submission safe.
        existing = connection.execute(select(db.quotes).where(db.quotes.c.user_id == user["id"], db.quotes.c.request_key == str(body.request_key))).mappings().first()
        if existing:
            if existing["source"] != "walk_in" or any(existing[k] != getattr(body, k) for k in ("service_id", "contact_name", "phone", "amount", "duration", "buffer", "terms")):
                raise HTTPException(409, "This walk-in request changed. Start a new request.")
            return make_booking(connection, existing, body.starts_at, user["id"])
        quote_id, now = str(uuid.uuid4()), int(time.time())
        connection.execute(db.quotes.insert().values(id=quote_id, user_id=user["id"], request_key=str(body.request_key),
            service_id=body.service_id, service_name=service["name"], contact_name=body.contact_name, phone=body.phone,
            notes=body.notes, source="walk_in", amount=body.amount, duration=body.duration, buffer=body.buffer,
            terms=body.terms, status="accepted", revision=1, created_at=now, expires_at=now+7*86400))
        audit(connection, user["id"], quote_id, "walk_in_quote_accepted")
        quote = connection.execute(select(db.quotes).where(db.quotes.c.id == quote_id)).mappings().one()
        return make_booking(connection, quote, body.starts_at, user["id"])


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: uuid.UUID, request: Request):
    with db.transaction() as connection:
        user = current_user(connection, request)
        invoice = connection.execute(select(db.invoices).where(db.invoices.c.id == str(invoice_id))).mappings().first()
        if not invoice:
            raise HTTPException(404, "Record not found.")
        if invoice["user_id"] != user["id"]:
            if not connection.execute(select(db.staff).where(db.staff.c.user_id == user["id"])).first():
                raise HTTPException(404, "Record not found.")
        result = invoice_view(connection, invoice)
        result["can_pay"] = invoice["user_id"] == user["id"]
        booking = connection.execute(select(db.bookings).where(db.bookings.c.id == invoice["booking_id"])).mappings().one()
        result["booking"] = booking_view(connection, booking)
        return result


@router.post("/invoices/{invoice_id}/checkout")
def invoice_checkout(invoice_id: uuid.UUID, request: Request):
    if not payments.configured():
        raise HTTPException(503, "Online test payments are unavailable. Your appointment remains saved.")
    with calendar_transaction() as connection:
        user = current_user(connection, request)
        invoice = owned(connection, db.invoices, invoice_id, user["id"])
        if invoice["status"] != "issued" or invoice["amount"] <= 0:
            raise HTTPException(409, "This invoice is not payable.")
        order = connection.execute(select(db.orders).where(db.orders.c.id == invoice["order_id"])).mappings().first() if invoice["order_id"] else None
        if not order:
            quote = connection.execute(select(db.quotes).join(db.bookings, db.bookings.c.quote_id == db.quotes.c.id).where(db.bookings.c.id == invoice["booking_id"])).mappings().one()
            order_id = str(uuid.uuid4())
            connection.execute(db.orders.insert().values(id=order_id, user_id=user["id"], request_key=invoice["id"],
                items=[{"id": quote["service_id"], "name": quote["service_name"]+" · "+invoice["number"], "quantity": 1, "unit_amount": invoice["amount"]}],
                amount=invoice["amount"], currency="zar", status="pending", created_at=int(time.time())))
            connection.execute(update(db.invoices).where(db.invoices.c.id == invoice["id"]).values(order_id=order_id))
            order = connection.execute(select(db.orders).where(db.orders.c.id == order_id)).mappings().one()
        if order["status"] != "pending":
            raise HTTPException(409, "This payment has already finished. Contact the salon if you need assistance.")
        if order["checkout_url"]:
            return {"order_id": order["id"], "url": order["checkout_url"]}
        # Commit the durable association before calling Stripe, so a provider
        # timeout cannot leave a payment detached from its invoice.
        order_id = order["id"]
    with db.transaction() as connection:
        current_user(connection, request)
        order = connection.execute(select(db.orders).where(db.orders.c.id == order_id).with_for_update()).mappings().one()
        invoice = connection.execute(select(db.invoices).where(db.invoices.c.id == str(invoice_id))).mappings().one()
        if invoice["status"] != "issued":
            raise HTTPException(409, "This invoice was cancelled.")
        if order["status"] != "pending":
            raise HTTPException(409, "This payment has already finished.")
        if order["checkout_url"]:
            return {"order_id": order["id"], "url": order["checkout_url"]}
        base_url = str(request.base_url).rstrip("/")
        import os
        if os.getenv("VERCEL"):
            base_url = "https://" + request.url.netloc
        checkout = payments.create_checkout(order, user["email"], base_url)
        connection.execute(update(db.orders).where(db.orders.c.id == order_id).values(stripe_session=checkout["id"], checkout_url=checkout["url"]))
        return {"order_id": order_id, "url": checkout["url"]}


@router.get("/bookings/{booking_id}/calendar.ics")
def calendar_export(booking_id: uuid.UUID, request: Request):
    with db.transaction() as connection:
        user = current_user(connection, request)
        booking = owned(connection, db.bookings, booking_id, user["id"])
        quote = connection.execute(select(db.quotes).where(db.quotes.c.id == booking["quote_id"])).mappings().one()
    def stamp(value):
        return datetime.fromtimestamp(value, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    def escape(value):
        return value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "").replace(",", "\\,").replace(";", "\\;")
    content = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//L Beauty//Appointments//EN", "BEGIN:VEVENT",
        f"UID:{booking['id']}@lbeauty", f"DTSTAMP:{stamp(time.time())}", f"DTSTART:{stamp(booking['starts_at'])}",
        f"DTEND:{stamp(booking['ends_at'])}", "SUMMARY:"+escape("L Beauty — "+quote["service_name"]),
        "STATUS:"+("CANCELLED" if booking["status"] == "cancelled" else "CONFIRMED"), "END:VEVENT", "END:VCALENDAR", ""])
    return Response(content, media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="lbeauty-{booking_id}.ics"'})

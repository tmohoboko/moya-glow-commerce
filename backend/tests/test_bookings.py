"""Booking acceptance: real persistence, role isolation, capacity and invoice integrity."""
import concurrent.futures
import time
import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select, update

from backend.app import db, payments
from backend.app.bookings import TZ
from backend.app.main import CATALOGUE, app
from backend.tests.test_api import ORIGIN, PASSWORD, database, client, register  # noqa: F401

SERVICE = CATALOGUE[0]['id']


def setup_staff():
    owner = TestClient(app, headers=ORIGIN)
    user = register(owner, 'owner@example.com')
    with db.transaction() as connection:
        connection.execute(db.staff.insert().values(user_id=user['id'], created_at=int(time.time())))
    response = owner.put('/api/staff/calendar', json={'enabled':True,'week':[[540,1020]]*7})
    assert response.status_code == 200, response.text
    return owner


def requested(customer, **changes):
    body = dict(request_key=str(uuid.uuid4()), service_id=SERVICE, contact_name='Test Customer', phone='0800000000', notes='Removal and nail design to discuss')
    body.update(changes)
    response = customer.post('/api/quotes', json=body)
    assert response.status_code == 201, response.text
    return response.json()


def quoted(customer, staff, **changes):
    quote = requested(customer)
    body = dict(amount=45000,duration=60,buffer=15,terms='Agreed treatment. Pay at visit; optional sandbox payment for review.',revision=0)
    body.update(changes)
    response = staff.post(f"/api/staff/quotes/{quote['id']}/issue", json=body)
    assert response.status_code == 200, response.text
    quote = response.json()
    assert customer.post(f"/api/quotes/{quote['id']}/accept", json={'revision':quote['revision']}).status_code == 200
    return quote


def tomorrow():
    return (datetime.now(TZ).date()+timedelta(days=1)).isoformat()


def slots(customer, quote):
    response = customer.get('/api/availability', params={'quote_id':quote['id'],'day':tomorrow()})
    assert response.status_code == 200, response.text
    return response.json()['slots']


def reserve(customer, quote, start):
    return customer.post('/api/bookings', json={'quote_id':quote['id'],'starts_at':start,'revision':quote['revision']})


def fake_provider(monkeypatch):
    monkeypatch.setattr(payments, 'create_checkout', lambda order,email,base: {'id':'cs_test_'+order['id'], 'url':'https://checkout.stripe.com/c/pay/cs_test_'+order['id']})


def paid_event(order, identifier='evt_test_booking_paid'):
    return {'id':identifier,'type':'checkout.session.completed','livemode':False,'data':{'object':{'id':order['stripe_session'],'livemode':False,'metadata':{'order_id':order['id']},'client_reference_id':order['id'],'amount_total':order['amount'],'currency':'zar','payment_status':'paid'}}}


def test_full_quote_booking_invoice_and_calendar_journey(client):
    register(client); staff = setup_staff()
    quote = quoted(client, staff)
    choices = slots(client, quote)
    assert choices and datetime.fromtimestamp(choices[0], TZ).hour == 9
    response = reserve(client, quote, choices[0]); assert response.status_code == 201, response.text
    booking = response.json()
    assert booking['status'] == 'confirmed'
    assert booking['ends_at']-booking['starts_at'] == 3600
    assert booking['blocked_until']-booking['ends_at'] == 900
    invoice = client.get('/api/invoices/'+booking['invoice']['id']).json()
    assert invoice['amount'] == 45000 and invoice['currency'] == 'zar'
    assert invoice['payment_status'] == 'unpaid' and invoice['receipt_number'] is None
    assert reserve(client,quote,choices[0]).json()['id'] == booking['id']
    assert len(client.get('/api/bookings').json()) == 1
    ics = client.get(f"/api/bookings/{booking['id']}/calendar.ics")
    assert ics.status_code == 200 and 'BEGIN:VEVENT' in ics.text and 'DTSTART:' in ics.text
    assert 'contact_name' not in ics.text and '0800000000' not in ics.text
    assert staff.get('/api/staff/calendar',params={'day':tomorrow()}).json()['bookings'][0]['id'] == booking['id']


def test_customers_cannot_issue_quotes_configure_calendar_or_view_staff(client):
    register(client)
    quote = requested(client)
    assert client.get('/api/staff/access').status_code == 403
    assert client.get('/api/staff/calendar',params={'day':tomorrow()}).status_code == 403
    assert client.put('/api/staff/calendar',json={'enabled':True,'week':[[540,1020]]*7}).status_code == 403
    assert client.post(f"/api/staff/quotes/{quote['id']}/issue",json={'amount':1,'duration':60,'buffer':15,'terms':'x','revision':0}).status_code == 403


def test_quota_request_idempotency_and_tamper_rejection(client):
    register(client)
    key = str(uuid.uuid4())
    first = requested(client, request_key=key)
    assert requested(client, request_key=key)['id'] == first['id']
    assert client.post('/api/quotes',json={'request_key':key,'service_id':SERVICE,'contact_name':'Changed Customer','phone':'0800000000'}).status_code == 409
    assert client.post('/api/quotes',json={'request_key':str(uuid.uuid4()),'service_id':SERVICE,'contact_name':'Test Customer','phone':'0800000000','amount':1}).status_code == 422


def test_quotation_requires_acceptance_revision_and_expiry(client):
    register(client); staff = setup_staff(); quote = requested(client)
    assert client.get('/api/availability',params={'quote_id':quote['id'],'day':tomorrow()}).status_code == 409
    body = {'amount':45000,'duration':60,'buffer':15,'terms':'Treatment confirmed','revision':0}
    assert staff.post(f"/api/staff/quotes/{quote['id']}/issue",json=body).status_code == 200
    body['revision'] = 1; body['amount'] = 47000
    assert staff.post(f"/api/staff/quotes/{quote['id']}/issue",json=body).status_code == 200
    assert client.post(f"/api/quotes/{quote['id']}/accept",json={'revision':1}).status_code == 409
    assert client.post(f"/api/quotes/{quote['id']}/accept",json={'revision':2}).status_code == 200
    with db.transaction() as connection:
        connection.execute(update(db.quotes).where(db.quotes.c.id == quote['id']).values(expires_at=int(time.time())-1))
    assert client.get('/api/availability',params={'quote_id':quote['id'],'day':tomorrow()}).status_code == 409


def test_slot_conflict_buffer_and_cancellation_release(client):
    register(client); staff = setup_staff()
    first = quoted(client,staff); start = slots(client,first)[0]
    booking = reserve(client,first,start).json()
    other = quoted(client,staff)
    remaining = slots(client,other)
    assert start not in remaining and start+3600 not in remaining and start+4500 in remaining
    assert reserve(client,other,start).status_code == 409
    assert reserve(client,other,start+3600).status_code == 409
    result = client.post(f"/api/bookings/{booking['id']}/cancel")
    assert result.status_code == 200 and result.json()['invoice']['status'] == 'void'
    assert start in slots(client,other)
    assert reserve(client,other,start).status_code == 201


def test_reschedule_preserves_invoice_and_checks_conflicts(client):
    register(client); staff = setup_staff(); quote = quoted(client,staff); start = slots(client,quote)[0]
    booking = reserve(client,quote,start).json(); other = quoted(client,staff)
    assert client.post(f"/api/bookings/{booking['id']}/reschedule",json={'starts_at':start+900}).status_code == 200
    moved = client.get('/api/bookings').json()[0]
    assert moved['invoice']['id'] == booking['invoice']['id']
    assert start not in slots(client,other)
    assert client.post(f"/api/bookings/{booking['id']}/reschedule",json={'starts_at':start+86400*100}).status_code == 422


def test_other_customer_cannot_read_or_change_booking_quote_invoice(client):
    register(client); staff = setup_staff(); quote = quoted(client,staff); booking = reserve(client,quote,slots(client,quote)[0]).json()
    with TestClient(app,headers=ORIGIN) as stranger:
        register(stranger,'stranger@example.com')
        assert stranger.get('/api/quotes').json() == []
        assert stranger.get('/api/bookings').json() == []
        assert stranger.get('/api/invoices/'+booking['invoice']['id']).status_code == 404
        assert stranger.get(f"/api/bookings/{booking['id']}/calendar.ics").status_code == 404
        assert stranger.post(f"/api/quotes/{quote['id']}/accept",json={'revision':1}).status_code == 404
        assert stranger.post(f"/api/bookings/{booking['id']}/cancel").status_code == 404
        assert stranger.post(f"/api/invoices/{booking['invoice']['id']}/checkout").status_code == 404


def test_default_calendar_is_open_daily_from_09_to_17(client):
    config = client.get('/api/booking/config')
    assert config.status_code == 200
    assert config.json()['enabled'] is True
    assert config.json()['week'] == [[540,1020]]*7
    assert config.json()['timezone'] == 'Africa/Johannesburg'
    result = client.get('/api/calendar/availability', params={'day':tomorrow()})
    assert result.status_code == 200
    assert datetime.fromtimestamp(result.json()['slots'][0], TZ).strftime('%H:%M') == '09:00'
    assert datetime.fromtimestamp(result.json()['slots'][-1], TZ).strftime('%H:%M') == '16:45'


def test_closed_calendar_never_invents_availability(client):
    register(client)
    staff = setup_staff(); quote = quoted(client,staff)
    assert staff.put('/api/staff/calendar',json={'enabled':False,'week':[None]*7}).status_code == 200
    assert slots(client,quote) == []


def test_blocks_and_walkins_share_online_capacity(client):
    register(client); staff = setup_staff(); quote = quoted(client,staff); start = slots(client,quote)[0]
    block = staff.post('/api/staff/blocks',json={'starts_at':start,'ends_at':start+3600,'label':'Lunch break'})
    assert block.status_code == 201
    assert reserve(client,quote,start).status_code == 409
    assert staff.post('/api/staff/blocks/'+block.json()['id']+'/release').status_code == 200
    body = dict(request_key=str(uuid.uuid4()),service_id=SERVICE,contact_name='Walk-in Guest',phone='0800000001',notes='',amount=45000,duration=60,buffer=15,terms='Guest agreed treatment and pay at visit.',revision=0,starts_at=start)
    walk = staff.post('/api/staff/walk-ins',json=body)
    assert walk.status_code == 201, walk.text
    assert staff.post('/api/staff/walk-ins',json=body).json()['id'] == walk.json()['id']
    assert walk.json()['quote']['source'] == 'walk_in'
    assert reserve(client,quote,start).status_code == 409
    assert staff.post('/api/staff/blocks',json={'starts_at':start,'ends_at':start+3600,'label':'Conflict'}).status_code == 409


def test_invoice_payment_uses_quote_amount_and_only_webhook_creates_receipt(client,monkeypatch):
    from backend.app.main import apply_event
    register(client); staff = setup_staff(); quote = quoted(client,staff,amount=52500)
    booking = reserve(client,quote,slots(client,quote)[0]).json(); invoice_id = booking['invoice']['id']
    fake_provider(monkeypatch)
    checkout = client.post(f'/api/invoices/{invoice_id}/checkout')
    assert checkout.status_code == 200, checkout.text
    assert client.post(f'/api/invoices/{invoice_id}/checkout').json()['order_id'] == checkout.json()['order_id']
    with db.transaction() as connection:
        order = connection.execute(select(db.orders).where(db.orders.c.id == checkout.json()['order_id'])).mappings().one()
    assert order['amount'] == 52500 and order['items'][0]['unit_amount'] == 52500
    assert client.get('/api/invoices/'+invoice_id).json()['receipt_number'] is None
    apply_event(paid_event(order))
    invoice = client.get('/api/invoices/'+invoice_id).json()
    assert invoice['payment_status'] == 'paid' and invoice['receipt_number'].startswith('LBR-')
    assert client.post(f'/api/invoices/{invoice_id}/checkout').status_code == 409
    assert client.get('/api/bookings').json()[0]['status'] == 'confirmed'
    client.post(f"/api/bookings/{booking['id']}/cancel")
    assert client.get('/api/invoices/'+invoice_id).json()['payment_status'] == 'refund_required'


def test_cancelled_invoice_blocks_checkout_and_late_payment_requires_refund(client,monkeypatch):
    from backend.app.main import apply_event
    register(client); staff = setup_staff(); quote = quoted(client,staff)
    booking = reserve(client,quote,slots(client,quote)[0]).json(); invoice_id = booking['invoice']['id']
    fake_provider(monkeypatch)
    checkout = client.post(f'/api/invoices/{invoice_id}/checkout').json()
    client.post(f"/api/bookings/{booking['id']}/cancel")
    assert client.post(f'/api/invoices/{invoice_id}/checkout').status_code == 409
    with db.transaction() as connection:
        order = connection.execute(select(db.orders).where(db.orders.c.id == checkout['order_id'])).mappings().one()
    apply_event(paid_event(order))
    assert client.get('/api/invoices/'+invoice_id).json()['payment_status'] == 'refund_required'
    assert client.get('/api/bookings').json()[0]['status'] == 'cancelled'


def test_parallel_reservations_have_one_winner(client):
    register(client); staff = setup_staff()
    with TestClient(app,headers=ORIGIN) as second:
        register(second, 'second-booker@example.com')
        first_quote, second_quote = quoted(client,staff), quoted(second,staff)
        start = slots(client,first_quote)[0]
        attempts = [(first_quote,client.cookies.get('lb_session')),(second_quote,second.cookies.get('lb_session'))]
        def attempt(value):
            quote,token = value
            with TestClient(app,headers=ORIGIN) as other:
                other.cookies.set('lb_session',token)
                return reserve(other,quote,start).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt,attempts))
        assert sorted(results) == [201,409]


def test_invalid_hours_and_client_price_are_rejected(client):
    register(client); staff = setup_staff()
    assert staff.put('/api/staff/calendar',json={'enabled':True,'week':[[600,540]]*7}).status_code == 422
    assert staff.put('/api/staff/calendar',json={'enabled':True,'week':[[541,1020]]*7}).status_code == 422
    quote = quoted(client,staff)
    assert client.post('/api/bookings',json={'quote_id':quote['id'],'starts_at':slots(client,quote)[0],'revision':1,'amount':1}).status_code == 422


def test_legacy_unlinked_checkout_is_parked(client,monkeypatch):
    monkeypatch.delenv('ENABLE_LEGACY_COMMERCE')
    assert client.post('/api/checkout',json={'request_key':str(uuid.uuid4()),'items':[{'id':SERVICE,'quantity':1}]}).status_code == 410


def test_booking_and_invoice_survive_fresh_api_process(client):
    import json
    import os
    import subprocess
    import sys
    register(client); staff = setup_staff(); quote = quoted(client,staff)
    booking = reserve(client,quote,slots(client,quote)[0]).json()
    code = """
import json,sys
from fastapi.testclient import TestClient
from backend.app.main import app
state=json.load(sys.stdin)
with TestClient(app,headers={'Origin':'http://testserver'}) as client:
    client.cookies.set('lb_session',state['token'])
    bookings=client.get('/api/bookings').json()
    assert len(bookings)==1 and bookings[0]['id']==state['booking_id']
    invoice=client.get('/api/invoices/'+state['invoice_id'])
    assert invoice.status_code==200 and invoice.json()['amount']==45000
"""
    result = subprocess.run([sys.executable,'-c',code],input=json.dumps({'token':client.cookies.get('lb_session'),'booking_id':booking['id'],'invoice_id':booking['invoice']['id']}),capture_output=True,text=True,timeout=25,env=os.environ.copy())
    assert result.returncode == 0, result.stderr


def test_week_availability_returns_seven_days_without_customer_details(client):
    register(client); staff=setup_staff(); quote=quoted(client,staff)
    day=tomorrow()
    response=client.get('/api/availability',params={'quote_id':quote['id'],'day':day,'view':'week'})
    assert response.status_code==200, response.text
    body=response.json()
    assert body['view']=='week' and len(body['days'])==7
    assert datetime.fromisoformat(body['days'][0]['day']).weekday()==0
    assert body['slots']==next(d['slots'] for d in body['days'] if d['day']==day)
    assert all(set(d)=={'day','slots','unavailable','booked','closed'} for d in body['days'])
    assert 'phone' not in response.text and 'contact_name' not in response.text


def test_week_slots_mark_occupied_intervals_and_keep_free_slots(client):
    register(client); staff=setup_staff(); first=quoted(client,staff)
    start=slots(client,first)[0]
    assert reserve(client,first,start).status_code==201
    second=quoted(client,staff)
    response=client.get('/api/availability',params={'quote_id':second['id'],'day':tomorrow(),'view':'week'})
    selected=next(d for d in response.json()['days'] if d['day']==tomorrow())
    assert start in selected['unavailable'] and start not in selected['slots']
    assert start+3600 in selected['unavailable']
    assert start+4500 in selected['slots']


def test_staff_week_calendar_uses_monday_boundary_and_contains_bookings(client):
    register(client); staff=setup_staff(); quote=quoted(client,staff)
    booking=reserve(client,quote,slots(client,quote)[0]).json()
    result=staff.get('/api/staff/calendar',params={'day':tomorrow(),'view':'week'})
    assert result.status_code==200
    body=result.json()
    assert body['view']=='week' and datetime.fromisoformat(body['first_day']).weekday()==0
    assert booking['id'] in [b['id'] for b in body['bookings']]
    assert client.get('/api/staff/calendar',params={'day':tomorrow(),'view':'week'}).status_code==403


def test_calendar_view_is_validated(client):
    register(client); staff=setup_staff(); quote=quoted(client,staff)
    assert client.get('/api/availability',params={'quote_id':quote['id'],'day':tomorrow(),'view':'year'}).status_code==422
    assert staff.get('/api/staff/calendar',params={'day':tomorrow(),'view':'year'}).status_code==422


def test_public_day_slots_publish_times_only_and_remove_booked_buffer(client):
    register(client); staff=setup_staff(); quote=quoted(client,staff)
    start=slots(client,quote)[0]
    assert reserve(client,quote,start).status_code==201
    client.cookies.clear()
    response=client.get('/api/calendar/availability',params={'day':tomorrow()})
    assert response.status_code==200
    assert response.headers['cache-control']=='no-store'
    body=response.json()
    assert body['view']=='day' and len(body['days'])==1
    assert start in body['days'][0]['unavailable'] and start not in body['slots']
    assert start+3600 in body['days'][0]['unavailable']
    assert start+4500 in body['slots']
    assert datetime.fromtimestamp(body['slots'][-1],TZ).strftime('%H:%M')=='16:45'
    for private in ['Test Customer','0800000000',quote['id'],'user_id','contact_name','notes']:
        assert private not in response.text


def test_public_closed_day_has_no_available_times_and_validates_view(client):
    result=client.get('/api/calendar/availability',params={'day':tomorrow()})
    assert result.status_code==200
    assert result.json()['slots']==[] and result.json()['days'][0]['closed'] is True
    assert client.get('/api/calendar/availability',params={'day':tomorrow(),'view':'month'}).status_code==422


def test_day_boundaries_respect_configured_hours_duration_and_buffer(client):
    register(client); staff = setup_staff()
    quote = quoted(client, staff, duration=60, buffer=15)
    for window, first, last in [([480,1080], '09:00', '15:45'), ([600,960], '10:00', '14:45')]:
        assert staff.put('/api/staff/calendar', json={'enabled':True,'week':[window]*7}).status_code == 200
        choices = slots(client, quote)
        assert datetime.fromtimestamp(choices[0], TZ).strftime('%H:%M') == first
        assert datetime.fromtimestamp(choices[-1], TZ).strftime('%H:%M') == last
        assert reserve(client, quote, choices[-1]+900).status_code == 409
        assert reserve(client, quote, choices[0]-900).status_code == 409
    assert reserve(client, quote, choices[-1]).status_code == 201


def test_public_booked_state_survives_new_session_and_blocks_stay_unavailable(client):
    register(client); staff = setup_staff(); quote = quoted(client, staff)
    start = slots(client, quote)[0]
    assert reserve(client, quote, start).status_code == 201
    assert staff.post('/api/staff/blocks', json={'starts_at':start+4500,'ends_at':start+5400,'label':'Private reason'}).status_code == 201
    with TestClient(app, headers=ORIGIN) as anonymous:
        result = anonymous.get('/api/calendar/availability', params={'day':tomorrow()})
        day = result.json()['days'][0]
        assert day['booked'] == [start+i*900 for i in range(5)]
        assert start+4500 in day['unavailable'] and start+4500 not in day['booked']
        assert 'Private reason' not in result.text
        assert anonymous.get('/api/availability', params={'quote_id':quote['id'],'day':tomorrow()}).status_code == 401
        assert reserve(anonymous, quote, start+5400).status_code == 401
        assert anonymous.get('/api/bookings').status_code == 401

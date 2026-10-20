"""Bounded acceptance against the authorised public L Beauty sandbox deployment.
Creates one artificial customer and one clearly labelled quotation. No staff
privileges, booking hours, payments or real customer records are changed.
"""
import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = 'https://moya-glow-commerce.vercel.app'
REPORT = Path('qa/booking-hosted-results.json')
checks = []


def check(name, condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:
        raise RuntimeError(name)


def run():
    with httpx.Client(base_url=BASE,headers={'Origin':BASE},timeout=30) as client:
        for path in ['/', '/services', '/gallery', '/contact', '/book?service=massage-full-body-450', '/salon']:
            check('Public route '+path,client.get(path).status_code == 200)
        check('Health',client.get('/api/health').status_code == 200)
        check('Readiness',client.get('/api/readiness').status_code == 200)
        config = client.get('/api/booking/config').json()
        check('South African booking configuration',config['timezone'] == 'Africa/Johannesburg' and config['workflow'] == 'quotation_then_booking')
        check('Unconfigured calendar stays closed',config['enabled'] is False)
        catalogue = client.get('/api/products').json()
        check('46 services and 11 categories preserved',len(catalogue) == 46 and len({row['category'] for row in catalogue}) == 11)
        check('Anonymous quotations private',client.get('/api/quotes').status_code == 401)
        check('Anonymous appointments private',client.get('/api/bookings').status_code == 401)
        check('Unlinked commerce checkout parked',client.post('/api/checkout',json={'request_key':str(uuid.uuid4()),'items':[{'id':catalogue[0]['id'],'quantity':1}]}).status_code == 410)
        email = 'booking-hosted-'+uuid.uuid4().hex+'@example.com'
        password = secrets.token_urlsafe(24)
        created = client.post('/api/auth/register',json={'email':email,'password':password})
        check('Registration',created.status_code == 201)
        cookie = created.headers.get('set-cookie','').lower()
        check('Private secure cookie',all(flag in cookie for flag in ['httponly','secure','samesite=lax']))
        body = {'request_key':str(uuid.uuid4()),'service_id':catalogue[0]['id'],'contact_name':'Hosted QA — artificial customer','phone':'0800000000','notes':'Automated release verification only. No real appointment requested.'}
        response = client.post('/api/quotes',json=body)
        check('Quotation request saved',response.status_code == 201 and response.json()['status'] == 'requested')
        quote = response.json()
        check('Published price is not invented into a final quote',quote['amount'] is None and quote['duration'] is None)
        check('Duplicate request creates one quotation',client.post('/api/quotes',json=body).json()['id'] == quote['id'])
        check('Client cannot inject price',client.post('/api/quotes',json={**body,'amount':1}).status_code == 422)
        check('Customer cannot access staff calendar',client.get('/api/staff/calendar',params={'day':datetime.now(timezone.utc).date().isoformat()}).status_code == 403)
        check('Unissued quote cannot be booked',client.post('/api/bookings',json={'quote_id':quote['id'],'starts_at':2000000000,'revision':1}).status_code == 409)
        check('Foreign origin cannot mutate request',client.post(f"/api/quotes/{quote['id']}/decline",headers={'Origin':'https://other.example'}).status_code == 403)
        check('Quotation still present',client.get('/api/quotes').json()[0]['id'] == quote['id'])
        check('Logout',client.post('/api/auth/logout').status_code == 204)
        check('Session revoked',client.get('/api/bookings').status_code == 401)
        check('Login again',client.post('/api/auth/login',json={'email':email,'password':password}).status_code == 200)
        check('Quotation persists after login',client.get('/api/quotes').json()[0]['id'] == quote['id'])
        check('No fabricated appointment',client.get('/api/bookings').json() == [])
        check('Final logout',client.post('/api/auth/logout').status_code == 204)
        return quote['id']


if __name__ == '__main__':
    record = {'base_url':BASE,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks}
    try:
        record['artificial_quote_id'] = run()
        record['passed'] = True
    except Exception as exc:
        record['passed'] = False
        record['failure'] = str(exc)[:160]
        raise
    finally:
        REPORT.write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps({'passed':record['passed'],'checks':len(checks),'report':str(REPORT)}))

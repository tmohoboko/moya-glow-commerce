"""Exercise the public sandbox API; keep artificial test credentials outside Git.

Run with the backend development dependencies installed. --inspect refreshes
order states after completing the generated Stripe test checkouts in a browser.
"""
import argparse
import json
import os
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import httpx

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', default='https://moya-glow-commerce.vercel.app')
parser.add_argument('--state-file', required=True)
parser.add_argument('--report-file', required=True)
parser.add_argument('--inspect', action='store_true')
args = parser.parse_args()
base = args.base_url.rstrip('/')
assert base == 'https://moya-glow-commerce.vercel.app', 'Use the authorized public sandbox target.'
state_path, report_path = Path(args.state_file), Path(args.report_file)
assert not state_path.resolve().is_relative_to(Path(__file__).resolve().parents[1]), 'Keep credentials outside the repository.'
report = {'base_url': base, 'payment_mode': 'test', 'checked_at': int(time.time()), 'checks': []}


def check(name, condition):
    report['checks'].append({'name': name, 'passed': bool(condition)})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    assert condition, name
    print('PASS', name)


def client():
    return httpx.Client(base_url=base, headers={'Origin': base}, timeout=45)


with client() as api:
    if args.inspect:
        state = json.loads(state_path.read_text())
        response = api.post('/api/auth/login', json=state['credentials'])
        check('account can log in again', response.status_code == 200)
        response = api.get('/api/orders')
        check('order history remains available', response.status_code == 200)
        report['orders'] = response.json()
        report['cases'] = state['orders']
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'order_states': {o['id']: o['status'] for o in report['orders']}}))
        raise SystemExit(0)

    health = api.get('/api/health')
    ready = api.get('/api/readiness')
    check('HTTPS health and sandbox readiness', health.status_code == ready.status_code == 200 and ready.json() == {
        'ready': True, 'database': True, 'stripe': True, 'payment_mode': 'test'})
    products = api.get('/api/products').json()
    check('46 services and 11 categories preserved', len(products) == 46 and len({p['category'] for p in products}) == 11)
    product = next(p for p in products if p['name'] == 'Full Body')
    check('Full Body costs R450', product['price'] == 450)
    check('anonymous orders rejected', api.get('/api/orders').status_code == 401)
    credentials = {'email': f'hosted-qa-{uuid.uuid4().hex}@example.com', 'password': secrets.token_urlsafe(24)}
    created = api.post('/api/auth/register', json=credentials)
    check('registration creates persistent customer', created.status_code == 201)
    identity = created.json()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(state_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump({'credentials': credentials, 'orders': {}}, stream)
    cookie = next(c for c in api.cookies.jar if c.name == 'lb_session')
    flags = {k.lower(): v for k, v in cookie._rest.items()}
    check('session cookie is Secure HttpOnly SameSite Lax', cookie.secure and 'httponly' in flags and flags.get('samesite', '').lower() == 'lax')
    check('API responses are not cached', created.headers.get('cache-control') == 'no-store')
    with client() as restored:
        restored.cookies.update(api.cookies)
        check('fresh client restores the database session', restored.get('/api/auth/me').json() == identity)
    revoked = httpx.Cookies(api.cookies)
    check('hostile origin cannot log out customer', api.post('/api/auth/logout', headers={'Origin': 'https://untrusted.example'}).status_code == 403)
    check('blocked origin preserves session', api.get('/api/auth/me').json() == identity)
    preflight = api.options('/api/orders', headers={'Origin': 'https://untrusted.example', 'Access-Control-Request-Method': 'GET'})
    check('foreign origin receives no credentialed CORS grant', 'access-control-allow-origin' not in preflight.headers and 'access-control-allow-credentials' not in preflight.headers)
    check('logout succeeds', api.post('/api/auth/logout').status_code == 204)
    with client() as old_session:
        old_session.cookies.update(revoked)
        check('logout revokes the old database session', old_session.get('/api/auth/me').status_code == 401)
    check('incorrect password is rejected', api.post('/api/auth/login', json={**credentials, 'password': 'incorrect-qa-password'}).status_code == 401)
    check('registered account can log in', api.post('/api/auth/login', json=credentials).json() == identity)
    forged = api.post('/api/stripe/webhook', content=b'{}', headers={'stripe-signature': 'invalid'})
    check('unsigned webhook is rejected', forged.status_code == 400)
    items = [{'id': product['id'], 'quantity': 1}]
    check('client cannot inject a checkout price', api.post('/api/checkout', json={'request_key': str(uuid.uuid4()), 'items': items, 'amount': 1}).status_code == 422)
    cases = {}
    for name in ('success', 'cancel', 'decline', 'three_d_secure'):
        body = {'request_key': str(uuid.uuid4()), 'items': items}
        result = api.post('/api/checkout', json=body)
        check(f'{name} opens genuine Stripe sandbox checkout', result.status_code == 200 and urlsplit(result.json().get('url', '')).hostname == 'checkout.stripe.com' and 'cs_test_' in result.json().get('url', ''))
        checkout = result.json()
        order = api.get('/api/orders/' + checkout['order_id'])
        check(f'{name} order is server-priced and pending', order.status_code == 200 and order.json()['amount'] == 45000 and order.json()['currency'] == 'zar' and order.json()['status'] == 'pending')
        cases[name] = checkout
        if name == 'success':
            retry = api.post('/api/checkout', json=body)
            check('checkout retry reuses the same order and Stripe session', retry.status_code == 200 and retry.json() == checkout)
            api.get('/checkout/return', params={'order': checkout['order_id']})
            check('success-page visit cannot mark payment paid', api.get('/api/orders/' + checkout['order_id']).json()['status'] == 'pending')
    with client() as other:
        stranger = {'email': f'ownership-qa-{uuid.uuid4().hex}@example.com', 'password': secrets.token_urlsafe(24)}
        check('second customer registers', other.post('/api/auth/register', json=stranger).status_code == 201)
        check('customer cannot read another customer order', other.get('/api/orders/' + cases['success']['order_id']).status_code == 404)
        other.post('/api/auth/logout')
    state = {'credentials': credentials, 'orders': cases}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(state_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(state, stream)
    report['cases'] = {name: {'order_id': value['order_id']} for name, value in cases.items()}
    report['orders'] = api.get('/api/orders').json()
    api.post('/api/auth/logout')
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('Saved sanitized evidence; checkout links and artificial credentials remain in the private state file.')

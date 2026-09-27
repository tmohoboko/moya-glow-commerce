import secrets
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from authlib.integrations.httpx_client import OAuth2Client
from authlib.jose import JsonWebKey, JsonWebToken

from backend.tests.test_api import client  # reuse isolated database fixture
from backend.app import google_auth as google
from backend.app.db import connection

@pytest.fixture(autouse=True)
def disabled(monkeypatch):
    for key in ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI'):
        monkeypatch.delenv(key, raising=False)

@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', secrets.token_urlsafe(32))
    # Use the permitted localhost origin in real config; TestClient keeps cookies at testserver.
    monkeypatch.setenv('GOOGLE_REDIRECT_URI', 'http://localhost/api/auth/google/callback')

def start(client):
    response = client.get('/api/auth/google/start', follow_redirects=False)
    assert response.status_code == 302
    params = parse_qs(urlsplit(response.headers['location']).query)
    assert params['code_challenge_method'] == ['S256']
    assert params['scope'] == ['openid email']
    assert 'httponly' in response.headers['set-cookie'].lower()
    return params['state'][0]

def callback(client, state):
    return client.get('/api/auth/google/callback', params={'state':state,'code':secrets.token_urlsafe(24)}, follow_redirects=False)

def mock_identity(monkeypatch, email='new@example.test', subject='google-subject', **extra):
    monkeypatch.setattr(google, 'verify_google', lambda *args: {'email':email,'sub':subject,'email_verified':True,**extra})

def redeem(client):
    return client.post('/api/auth/google/session', headers={'X-Moya-OAuth':'1'})

def test_provider_disabled(client):
    assert client.get('/api/auth/providers').json() == {'providers':['password']}
    for path in ('start','callback'):
        assert client.get('/api/auth/google/'+path).status_code == 503
    assert redeem(client).status_code == 503

@pytest.mark.parametrize('uri', ['http://example.com/api/auth/google/callback','https://example.com/wrong','https://example.com/api/auth/google/callback?next=evil','https://user:pass@example.com/api/auth/google/callback'])
def test_bad_redirect_disables_provider(client, configured, monkeypatch, uri):
    monkeypatch.setenv('GOOGLE_REDIRECT_URI', uri)
    assert client.get('/api/auth/providers').json() == {'providers':['password']}

def test_capabilities_no_secrets(client, configured):
    assert client.get('/api/auth/providers').json() == {'providers':['password','google']}

def test_invalid_expired_and_cross_browser_state(client, configured, monkeypatch):
    monkeypatch.setattr(google,'verify_google',lambda *args: pytest.fail('Network verification must not run'))
    assert callback(client,'invalid').status_code == 400
    state = start(client)
    saved = client.cookies.get(google.STATE_COOKIE)
    client.cookies.clear()
    assert callback(client,state).status_code == 400
    client.cookies.set(google.STATE_COOKIE, saved, path=google.COOKIE_PATH)
    with connection() as db: db.execute('UPDATE oauth_states SET expires_at=0')
    assert callback(client,state).status_code == 400
    with connection() as db: assert db.execute('SELECT count(*) FROM oauth_states').fetchone()[0] == 0

@pytest.mark.parametrize('claims', [{'email_verified':False},{'email_verified':'true'},{'email':None},{'sub':''}])
def test_unverified_identity_rejected(client, configured, monkeypatch, claims):
    mock_identity(monkeypatch, **claims)
    state = start(client)
    assert callback(client,state).status_code == 401
    assert callback(client,state).status_code == 400
    with connection() as db: assert db.execute('SELECT count(*) FROM oauth_handoffs').fetchone()[0] == 0

@pytest.mark.parametrize('role', ['customer','admin','catalogue_manager','support_agent','analyst'])
def test_existing_mapping_unchanged_roles_session_and_logout(client, configured, monkeypatch, role):
    mock_identity(monkeypatch,email=f'  {role.upper()}@EXAMPLE.TEST ',role='admin')
    state = start(client)
    response = callback(client,state)
    assert response.status_code == 303
    assert response.headers['location'] == '/account?google=complete'
    assert 'access_token' not in response.text
    assert client.post('/api/auth/google/session').status_code == 403
    issued = redeem(client)
    assert issued.status_code == 200
    headers = {'Authorization':'Bearer '+issued.json()['access_token']}
    assert client.get('/api/auth/me',headers=headers).json()['role'] == role
    assert redeem(client).status_code == 401
    assert callback(client,state).status_code == 400
    assert client.post('/api/auth/logout',headers=headers).status_code == 204
    assert client.get('/api/auth/me',headers=headers).status_code == 401


def test_new_customer_and_subject_binding(client, configured, monkeypatch):
    mock_identity(monkeypatch,role='admin')
    assert callback(client,start(client)).status_code == 303
    result = redeem(client)
    user = client.get('/api/auth/me', headers={'Authorization':'Bearer '+result.json()['access_token']}).json()
    assert user['role'] == 'customer'
    # A changed email must not relink the already-bound subject to a staff account.
    mock_identity(monkeypatch,email='admin@example.test')
    assert callback(client,start(client)).status_code == 303
    result = redeem(client)
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer '+result.json()['access_token']}).json()['id'] == user['id']


def test_inactive_account_and_handoff_expiry(client, configured, monkeypatch):
    mock_identity(monkeypatch,email='customer@example.test')
    with connection() as db: db.execute("UPDATE users SET active=0 WHERE id='customer'")
    assert callback(client,start(client)).status_code == 401
    mock_identity(monkeypatch)
    assert callback(client,start(client)).status_code == 303
    with connection() as db: db.execute('UPDATE oauth_handoffs SET expires_at=0')
    assert redeem(client).status_code == 401


def test_cancellation_and_provider_error_consume_state(client, configured, monkeypatch):
    state=start(client)
    assert client.get('/api/auth/google/callback',params={'state':state,'error':'access_denied'}).status_code==400
    assert callback(client,state).status_code==400
    marker=secrets.token_urlsafe(32)
    def fail(*args): raise RuntimeError(marker)
    monkeypatch.setattr(google,'verify_google',fail)
    state=start(client)
    result=callback(client,state)
    assert result.status_code==401 and marker not in result.text
    assert callback(client,state).status_code==400

@pytest.mark.parametrize('invalid', [None,'signature','issuer','audience','nonce','expired','algorithm'])
def test_real_oidc_verification_with_mock_network(client, configured, monkeypatch, invalid):
    state = start(client)
    with connection() as db: record=dict(db.execute('SELECT * FROM oauth_states').fetchone())
    key=JsonWebKey.generate_key('RSA',2048,is_private=True)
    signing_key=JsonWebKey.generate_key('RSA',2048,is_private=True) if invalid=='signature' else key
    claims={'iss':'https://accounts.google.com','sub':'signed-sub','aud':google.configuration()['client_id'],
            'iat':int(time.time()),'exp':int(time.time())+300,'nonce':record['nonce'],
            'email':'signed@example.test','email_verified':True}
    if invalid=='issuer':claims['iss']='https://attacker.invalid'
    if invalid=='audience':claims['aud']='another-client'
    if invalid=='nonce':claims['nonce']='different'
    if invalid=='expired':claims['exp']=int(time.time())-300
    algorithm='RS512' if invalid=='algorithm' else 'RS256'
    encoded=JsonWebToken([algorithm]).encode({'alg':algorithm},claims,signing_key).decode()
    def transport(request):
        if str(request.url)==google.TOKEN_URL:
            body=parse_qs(request.content.decode())
            assert body['code_verifier']==[record['verifier']]
            assert body['redirect_uri']==[google.configuration()['redirect_uri']]
            return httpx.Response(200,json={'id_token':encoded,'access_token':secrets.token_urlsafe(32),'token_type':'Bearer'})
        assert str(request.url)==google.JWKS_URL
        return httpx.Response(200,json={'keys':[key.as_dict(is_private=False)]})
    mocked=httpx.MockTransport(transport)
    original_client=httpx.Client
    monkeypatch.setattr(google,'oauth_client',lambda config: OAuth2Client(**config,token_endpoint_auth_method='client_secret_post',transport=mocked))
    monkeypatch.setattr(google,'HTTPClient',lambda **kwargs: original_client(transport=mocked,**kwargs))
    response=callback(client,state)
    assert response.status_code==(401 if invalid else 303)

def test_replay_with_original_cookies_is_rejected(client, configured, monkeypatch):
    mock_identity(monkeypatch)
    state=start(client)
    browser=client.cookies.get(google.STATE_COOKIE)
    assert callback(client,state).status_code==303
    handoff=client.cookies.get(google.HANDOFF_COOKIE)
    assert redeem(client).status_code==200
    client.cookies.set(google.STATE_COOKIE,browser,path=google.COOKIE_PATH)
    assert callback(client,state).status_code==400
    client.cookies.set(google.HANDOFF_COOKIE,handoff,path=google.COOKIE_PATH)
    assert redeem(client).status_code==401


def test_conflicting_subject_cannot_relink_account(client, configured, monkeypatch):
    mock_identity(monkeypatch,email='customer@example.test',subject='first')
    assert callback(client,start(client)).status_code==303
    mock_identity(monkeypatch,email='customer@example.test',subject='second')
    assert callback(client,start(client)).status_code==401


def test_inactive_after_callback_cannot_redeem(client, configured, monkeypatch):
    mock_identity(monkeypatch,email='customer@example.test')
    assert callback(client,start(client)).status_code==303
    with connection() as db: db.execute("UPDATE users SET active=0 WHERE id='customer'")
    assert redeem(client).status_code==401


def test_https_cookie_and_safe_callback_logs(client, configured, monkeypatch, caplog):
    import logging
    monkeypatch.setenv('GOOGLE_REDIRECT_URI','https://shop.example.test/api/auth/google/callback')
    response=client.get('/api/auth/google/start',follow_redirects=False)
    assert 'Secure' in response.headers['set-cookie']
    assert response.headers['referrer-policy']=='no-referrer'
    assert logging.getLogger('uvicorn.access').disabled
    with caplog.at_level(logging.INFO,logger='moya'):
        marker=secrets.token_urlsafe(32)
        response=client.get('/api/auth/google/callback',params={'code':marker,'state':marker})
    assert marker not in caplog.text and marker not in response.text

"""Google authorization-code OIDC; server-held state, PKCE and cookie handoff."""
import hmac
import os
import secrets
import time
import uuid
from urllib.parse import urlsplit

from httpx import Client as HTTPClient
from authlib.integrations.httpx_client import OAuth2Client
from authlib.jose import JsonWebToken
from authlib.oidc.core import CodeIDToken
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .db import connection
from .security import issue_session, password_hash, token_hash

router = APIRouter()
COOKIE_PATH = '/api/auth/google'
STATE_COOKIE = 'moya_google_state'
HANDOFF_COOKIE = 'moya_google_handoff'
AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
JWKS_URL = 'https://www.googleapis.com/oauth2/v3/certs'

# OAuth code/token HTTP client logging must never include credentials or codes.
# Uvicorn access logging is disabled separately; safe application logs remain.
def configuration():
    values = [os.getenv(name, '').strip() for name in
              ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI')]
    if not all(values):
        return None
    try:
        uri = urlsplit(values[2])
        valid = (uri.scheme == 'https' or (uri.scheme == 'http' and uri.hostname in ('localhost', '127.0.0.1')))
        if not valid or not uri.hostname or uri.username or uri.password or uri.query or uri.fragment or uri.path != COOKIE_PATH + '/callback':
            return None
        _ = uri.port
    except ValueError:
        return None
    return {'client_id': values[0], 'client_secret': values[1], 'redirect_uri': values[2]}

def require_config():
    config = configuration()
    if not config:
        raise HTTPException(503, 'Google sign-in is not configured')
    return config

def oauth_client(config):
    return OAuth2Client(**config, scope='openid email', code_challenge_method='S256',
                        token_endpoint_auth_method='client_secret_post', timeout=10)

def verify_google(config, code, state):
    """Provider tokens exist only within this function and are never persisted."""
    with oauth_client(config) as client:
        token = client.fetch_token(TOKEN_URL, code=code, code_verifier=state['verifier'])
    with HTTPClient(timeout=10) as client:
        response = client.get(JWKS_URL)
        response.raise_for_status()
        keys = response.json()
    claims = JsonWebToken(['RS256']).decode(
        token['id_token'], keys, claims_cls=CodeIDToken,
        claims_options={'iss': {'values': ['https://accounts.google.com', 'accounts.google.com']},
                        'aud': {'value': config['client_id']}},
        claims_params={'nonce': state['nonce'], 'client_id': config['client_id'],
                       'access_token': token.get('access_token')})
    claims.validate(leeway=30)
    return dict(claims)

def map_identity(claims):
    email = claims.get('email')
    subject = claims.get('sub')
    if claims.get('email_verified') is not True or not isinstance(email, str) or not isinstance(subject, str):
        raise HTTPException(401, 'Google identity could not be verified')
    email = email.strip().lower()
    if not subject or len(subject) > 255 or len(email) > 254 or email.count('@') != 1 or any(c.isspace() for c in email) or not all(email.split('@')):
        raise HTTPException(401, 'Google identity could not be verified')
    handoff = secrets.token_urlsafe(32)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        identity = db.execute("SELECT u.* FROM users u JOIN social_identities s ON s.user_id=u.id WHERE s.provider='google' AND s.subject=?", (subject,)).fetchone()
        if identity:
            user = identity
        else:
            # Email links only an initial verified identity. Future logins use sub.
            user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
            if not user:
                user_id = uuid.uuid4().hex
                db.execute('INSERT INTO users(id,email,password_hash,role) VALUES (?,?,?,?)',
                           (user_id, email, password_hash(secrets.token_urlsafe(48)), 'customer'))
                user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not user['active']:
                raise HTTPException(401, 'Google sign-in is unavailable for this account')
            existing = db.execute("SELECT 1 FROM social_identities WHERE provider='google' AND user_id=?", (user['id'],)).fetchone()
            if existing:
                raise HTTPException(401, 'Google identity could not be linked')
            db.execute("INSERT INTO social_identities VALUES ('google',?,?)", (subject, user['id']))
        if not user['active']:
            raise HTTPException(401, 'Google sign-in is unavailable for this account')
        db.execute('DELETE FROM oauth_handoffs WHERE expires_at<=?', (int(time.time()),))
        db.execute('INSERT INTO oauth_handoffs VALUES (?,?,?)', (token_hash(handoff), user['id'], int(time.time()) + 60))
    return handoff

@router.get('/api/auth/providers')
def providers():
    return {'providers': ['password', 'google'] if configuration() else ['password']}

@router.get('/api/auth/google/start')
def start(request: Request):
    from .main import throttle
    config = require_config()
    throttle(request, 'google-login', 15)
    state, browser, nonce, verifier = [secrets.token_urlsafe(32) for _ in range(4)]
    with oauth_client(config) as client:
        url, _ = client.create_authorization_url(AUTHORIZATION_URL, state=state, nonce=nonce,
                                                  code_verifier=verifier, prompt='select_account')
    with connection() as db:
        db.execute('DELETE FROM oauth_states WHERE expires_at<=?', (int(time.time()),))
        db.execute('INSERT INTO oauth_states VALUES (?,?,?,?,?)',
                   (token_hash(state), token_hash(browser), nonce, verifier, int(time.time()) + 300))
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(STATE_COOKIE, browser, max_age=300, httponly=True,
                        secure=config['redirect_uri'].startswith('https://'), samesite='lax', path=COOKIE_PATH)
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@router.get('/api/auth/google/callback')
def callback(request: Request):
    try:
        config = require_config()
        state_value = request.query_params.get('state', '')
        browser = request.cookies.get(STATE_COOKIE, '')
        if not state_value or len(state_value) > 128 or not browser or len(browser) > 128:
            raise HTTPException(400, 'Invalid or expired Google sign-in state')
        # Consume before any provider I/O, including errors. Commit even on expiry.
        with connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM oauth_states WHERE state_hash=?', (token_hash(state_value),)).fetchone()
            matched = row is not None and hmac.compare_digest(row['browser_hash'], token_hash(browser))
            if matched:
                db.execute('DELETE FROM oauth_states WHERE state_hash=?', (token_hash(state_value),))
        if not matched or row['expires_at'] <= int(time.time()):
            raise HTTPException(400, 'Invalid or expired Google sign-in state')
        code = request.query_params.get('code', '')
        if request.query_params.get('error') or not code or len(code) > 4096:
            raise HTTPException(400, 'Google sign-in was cancelled or failed')
        try:
            claims = verify_google(config, code, dict(row))
        except Exception:
            # Provider exception strings may contain codes/tokens; never echo/log them.
            raise HTTPException(401, 'Google identity could not be verified') from None
        handoff = map_identity(claims)
        response = RedirectResponse('/account?google=complete', status_code=303)
        response.set_cookie(HANDOFF_COOKIE, handoff, max_age=60, httponly=True,
                            secure=config['redirect_uri'].startswith('https://'), samesite='strict', path=COOKIE_PATH)
    except HTTPException as exc:
        response = JSONResponse({'detail': exc.detail, 'request_id': request.state.request_id}, status_code=exc.status_code)
    response.delete_cookie(STATE_COOKIE, path=COOKIE_PATH)
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@router.post('/api/auth/google/session')
def exchange(request: Request):
    require_config()
    # Same-origin JS must supply a custom header; cross-origin forms cannot redeem.
    if request.headers.get('X-Moya-OAuth') != '1':
        raise HTTPException(403, 'Google session exchange requires the account page')
    handoff = request.cookies.get(HANDOFF_COOKIE, '')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('DELETE FROM oauth_handoffs WHERE token_hash=? RETURNING user_id,expires_at',
                         (token_hash(handoff),)).fetchone()
        active = row and row['expires_at'] > int(time.time()) and db.execute('SELECT 1 FROM users WHERE id=? AND active=1', (row['user_id'],)).fetchone()
        result = issue_session(db, row['user_id']) if active else None
    response = JSONResponse(result if result else {'detail': 'Google sign-in expired; please try again', 'request_id': request.state.request_id}, status_code=200 if result else 401)
    response.delete_cookie(HANDOFF_COOKIE, path=COOKIE_PATH)
    return response

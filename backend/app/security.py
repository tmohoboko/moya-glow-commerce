import hashlib
import hmac
import secrets
import time
from fastapi import Depends, HTTPException, Request
from .db import connection

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def password_matches(password, stored):
    return hmac.compare_digest(password_hash(password, stored.split(':')[0]), stored)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def current_user(request: Request):
    token = request.headers.get('Authorization', '')
    if not token.startswith('Bearer '):
        raise HTTPException(401, 'Authentication required')
    with connection() as db:
        row = db.execute('SELECT u.id,u.email,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>? AND u.active=1',
                         (token_hash(token[7:]), int(time.time()))).fetchone()
        if not row:
            raise HTTPException(401, 'Session expired or invalid')
        user = dict(row)
        user['permissions'] = [r[0] for r in db.execute('SELECT resource FROM permissions WHERE role=?', (user['role'],))]
        return user

def require(resource):
    def check(user=Depends(current_user)):
        if resource not in user['permissions']:
            raise HTTPException(403, 'Permission denied')
        return user
    return check

def audit(db, user, request, action, resource, resource_id):
    db.execute('INSERT INTO audit_events(actor_id,action,resource,resource_id,request_id) VALUES (?,?,?,?,?)',
               (user['id'], action, resource, resource_id, request.state.request_id))


def issue_session(db, user_id):
    token = secrets.token_urlsafe(32)
    db.execute('DELETE FROM sessions WHERE expires_at<=?', (int(time.time()),))
    db.execute('INSERT INTO sessions VALUES (?,?,?)', (token_hash(token), user_id, int(time.time())+28800))
    return {'access_token': token, 'token_type': 'bearer', 'expires_in': 28800}

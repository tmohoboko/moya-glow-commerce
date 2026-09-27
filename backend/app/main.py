import json
import logging
import os
import re
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from .db import connection, migrate
from .security import audit, current_user, password_hash, password_matches, require, token_hash, issue_session

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('moya')
DUMMY_HASH = password_hash('unused-password-for-timing')

@asynccontextmanager
async def lifespan(app):
    migrate()
    yield

# Avoid provider HTTP request logging; correlation logs never include query strings.
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').disabled = True

app = FastAPI(title='Moya Glow Enterprise Prototype', version='0.1.0', lifespan=lifespan)

@app.middleware('http')
async def observability(request: Request, call_next):
    supplied = request.headers.get('X-Request-ID', '')
    request.state.request_id = supplied if re.fullmatch(r'[A-Za-z0-9_-]{1,64}', supplied) else uuid.uuid4().hex
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(json.dumps({'event': 'unhandled_error', 'type': type(exc).__name__, 'request_id': request.state.request_id}))
        response = JSONResponse({'detail': 'Internal server error', 'request_id': request.state.request_id}, status_code=500)
    response.headers['X-Request-ID'] = request.state.request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    logger.info(json.dumps({'event':'request', 'method':request.method, 'status':response.status_code, 'request_id':request.state.request_id, 'duration_ms':round((time.monotonic()-start)*1000)}))
    return response

@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return JSONResponse({'detail': exc.detail, 'request_id': request.state.request_id}, status_code=exc.status_code, headers=exc.headers)

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo passwords or submitted personal information into error payloads.
    errors = [{'field': '.'.join(str(x) for x in e['loc']), 'message': e['msg']} for e in exc.errors()]
    return JSONResponse({'detail': errors, 'request_id':request.state.request_id}, status_code=422)

@app.exception_handler(sqlite3.IntegrityError)
async def conflict(request, exc):
    return JSONResponse({'detail':'Duplicate or referenced resource', 'request_id':request.state.request_id}, status_code=409)

def throttle(request, bucket, limit):
    now = int(time.time())
    # Trust the socket peer only; forwarded headers cannot bypass the limiter.
    key = bucket + ':' + (request.client.host if request.client else 'unknown')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM rate_limits WHERE started_at<?', (now-300,))
        row = db.execute('SELECT * FROM rate_limits WHERE key=?', (key,)).fetchone()
        if row and row['count'] >= limit:
            raise HTTPException(429, 'Too many requests; retry later', headers={'Retry-After':'300'})
        db.execute('INSERT INTO rate_limits VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET count=count+1', (key, now))

def public_available():
    with connection() as db:
        if db.execute("SELECT value FROM app_settings WHERE key='maintenance'").fetchone()[0] == 'true':
            raise HTTPException(503, 'Moya Glow is temporarily under maintenance', headers={'Retry-After':'300'})

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)

@app.post('/api/auth/login')
def login(body: Login, request: Request):
    throttle(request, 'login', 15)
    with connection() as db:
        row = db.execute('SELECT * FROM users WHERE email=? AND active=1', (body.email.strip().lower(),)).fetchone()
        valid = password_matches(body.password, row['password_hash'] if row else DUMMY_HASH)
        if not row or not valid:
            raise HTTPException(401, 'Invalid email or password')
        return issue_session(db, row['id'])

@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return user

@app.post('/api/auth/logout', status_code=204)
def logout(request: Request, user=Depends(current_user)):
    with connection() as db:
        db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(request.headers['Authorization'][7:]),))

@app.get('/api/health')
def health():
    return {'status':'ok', 'service':'moya-glow', 'payments':'disabled'}

@app.get('/api/readiness')
def readiness():
    try:
        with connection() as db:
            db.execute('SELECT version FROM schema_migrations').fetchall()
            db.execute('SELECT id FROM products LIMIT 1').fetchall()
    except sqlite3.Error:
        raise HTTPException(503, 'Database unavailable')
    return {'status':'ready'}

PRODUCT_QUERY = 'SELECT p.*,c.name AS category FROM products p JOIN categories c ON c.id=p.category_id'
PUBLIC_FIELDS = ('id','name','price','category','image','description')

@app.get('/api/products', dependencies=[Depends(public_available)])
def products():
    with connection() as db:
        return [{key:row[key] for key in PUBLIC_FIELDS} for row in db.execute(PRODUCT_QUERY+' WHERE published=1 ORDER BY p.rowid')]

@app.get('/api/products/{product_id}', dependencies=[Depends(public_available)])
def product_detail(product_id: str):
    with connection() as db:
        row = db.execute(PRODUCT_QUERY+' WHERE p.id=? AND published=1', (product_id,)).fetchone()
        if not row: raise HTTPException(404, 'Product not found')
        return {key:row[key] for key in PUBLIC_FIELDS}

class Category(Input):
    name: str = Field(min_length=1, max_length=100)

class Product(Input):
    name: str = Field(min_length=1, max_length=150)
    price: float = Field(ge=0, le=1000000, allow_inf_nan=False)
    category_id: str = Field(min_length=1, max_length=100)
    image: str = Field(default='/product.svg', max_length=1000)
    description: str = Field(default='', max_length=5000)
    stock: int = Field(default=0, ge=0, le=1000000, strict=True)
    published: bool = False
    @field_validator('image')
    @classmethod
    def safe_image(cls, value):
        if not (value.startswith('/') and not value.startswith('//')) and not value.startswith('https://'):
            raise ValueError('Use a local path or HTTPS image URL')
        return value

@app.get('/api/admin/categories')
def categories(user=Depends(require('categories'))):
    with connection() as db: return [dict(r) for r in db.execute('SELECT * FROM categories ORDER BY name')]

@app.post('/api/admin/categories', status_code=201)
def create_category(body: Category, request: Request, user=Depends(require('categories'))):
    resource_id = uuid.uuid4().hex
    with connection() as db:
        db.execute('INSERT INTO categories VALUES (?,?)', (resource_id, body.name))
        audit(db,user,request,'create','categories',resource_id)
    return {'id':resource_id, **body.model_dump()}

@app.put('/api/admin/categories/{resource_id}')
def update_category(resource_id: str, body: Category, request: Request, user=Depends(require('categories'))):
    with connection() as db:
        if not db.execute('UPDATE categories SET name=? WHERE id=?', (body.name,resource_id)).rowcount: raise HTTPException(404,'Category not found')
        audit(db,user,request,'update','categories',resource_id)
    return {'id':resource_id, **body.model_dump()}

@app.delete('/api/admin/categories/{resource_id}', status_code=204)
def delete_category(resource_id: str, request: Request, user=Depends(require('categories'))):
    with connection() as db:
        if not db.execute('DELETE FROM categories WHERE id=?',(resource_id,)).rowcount: raise HTTPException(404,'Category not found')
        audit(db,user,request,'delete','categories',resource_id)

@app.get('/api/admin/products')
def admin_products(user=Depends(require('products'))):
    with connection() as db: return [dict(r) for r in db.execute(PRODUCT_QUERY+' ORDER BY p.rowid')]

@app.post('/api/admin/products', status_code=201)
def create_product(body: Product, request: Request, user=Depends(require('products'))):
    resource_id = uuid.uuid4().hex
    with connection() as db:
        db.execute('INSERT INTO products VALUES (?,?,?,?,?,?,?,?)',(resource_id,*body.model_dump().values()))
        audit(db,user,request,'create','products',resource_id)
    return {'id':resource_id, **body.model_dump()}

@app.put('/api/admin/products/{resource_id}')
def update_product(resource_id: str, body: Product, request: Request, user=Depends(require('products'))):
    with connection() as db:
        if not db.execute('UPDATE products SET name=?,price=?,category_id=?,image=?,description=?,stock=?,published=? WHERE id=?',(*body.model_dump().values(),resource_id)).rowcount: raise HTTPException(404,'Product not found')
        audit(db,user,request,'update','products',resource_id)
    return {'id':resource_id, **body.model_dump()}

@app.delete('/api/admin/products/{resource_id}', status_code=204)
def delete_product(resource_id: str, request: Request, user=Depends(require('products'))):
    with connection() as db:
        if not db.execute('DELETE FROM products WHERE id=?',(resource_id,)).rowcount: raise HTTPException(404,'Product not found')
        audit(db,user,request,'delete','products',resource_id)

@app.get('/api/admin/orders')
def orders(user=Depends(require('orders'))):
    with connection() as db: return [dict(r) for r in db.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 200')]

@app.get('/api/admin/orders/{resource_id}')
def order_detail(resource_id: str, user=Depends(require('orders'))):
    with connection() as db:
        row = db.execute('SELECT * FROM orders WHERE id=?',(resource_id,)).fetchone()
        if not row: raise HTTPException(404,'Order not found')
        return {**dict(row), 'items':[dict(r) for r in db.execute('SELECT * FROM order_items WHERE order_id=?',(resource_id,))], 'payments':[dict(r) for r in db.execute('SELECT id,provider,transaction_reference,status FROM payments WHERE order_id=?',(resource_id,))]}

class OrderStatus(Input):
    status: Literal['pending','processing','shipped','completed','cancelled']

@app.patch('/api/admin/orders/{resource_id}/status')
def order_status(resource_id: str, body: OrderStatus, request: Request, user=Depends(require('orders'))):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT status FROM orders WHERE id=?',(resource_id,)).fetchone()
        if not row: raise HTTPException(404,'Order not found')
        allowed = {'pending':['processing','cancelled'],'processing':['shipped','cancelled'],'shipped':['completed'],'completed':[],'cancelled':[]}
        if body.status not in allowed[row['status']]: raise HTTPException(409,'Invalid order status transition')
        db.execute('UPDATE orders SET status=? WHERE id=?',(body.status,resource_id))
        audit(db,user,request,'status:'+body.status,'orders',resource_id)
    return {'id':resource_id,'status':body.status}

class Ticket(Input):
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=5000)
class Message(Input):
    message: str = Field(min_length=1, max_length=5000)
class TicketStatus(Input):
    status: Literal['open','closed']

def ticket_access(db, resource_id, user):
    row = db.execute('SELECT * FROM support_tickets WHERE id=?',(resource_id,)).fetchone()
    if not row or (row['user_id'] != user['id'] and 'support' not in user['permissions']): raise HTTPException(404,'Ticket not found')
    return dict(row)

@app.post('/api/support/tickets', status_code=201)
def create_ticket(body: Ticket, request: Request, user=Depends(current_user)):
    throttle(request,'support',30)
    resource_id = uuid.uuid4().hex
    with connection() as db:
        db.execute('INSERT INTO support_tickets(id,user_id,subject) VALUES (?,?,?)',(resource_id,user['id'],body.subject))
        db.execute('INSERT INTO support_messages(ticket_id,user_id,body) VALUES (?,?,?)',(resource_id,user['id'],body.message))
        audit(db,user,request,'create','support',resource_id)
    return {'id':resource_id,'subject':body.subject,'status':'open'}

@app.get('/api/support/tickets')
def tickets(user=Depends(current_user)):
    with connection() as db:
        if 'support' in user['permissions']: rows = db.execute('SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 200')
        else: rows = db.execute('SELECT * FROM support_tickets WHERE user_id=? ORDER BY created_at DESC LIMIT 200',(user['id'],))
        return [dict(r) for r in rows]

@app.get('/api/support/tickets/{resource_id}')
def ticket_detail(resource_id: str, user=Depends(current_user)):
    with connection() as db:
        ticket = ticket_access(db,resource_id,user)
        return {**ticket, 'messages':[dict(r) for r in db.execute('SELECT * FROM support_messages WHERE ticket_id=? ORDER BY id',(resource_id,))]}

@app.post('/api/support/tickets/{resource_id}/messages', status_code=201)
def ticket_message(resource_id: str, body: Message, request: Request, user=Depends(current_user)):
    throttle(request,'support',30)
    with connection() as db:
        ticket = ticket_access(db,resource_id,user)
        if ticket['status']=='closed': raise HTTPException(409,'Ticket is closed')
        db.execute('INSERT INTO support_messages(ticket_id,user_id,body) VALUES (?,?,?)',(resource_id,user['id'],body.message))
        audit(db,user,request,'message','support',resource_id)
    return {'status':'created'}

@app.patch('/api/support/tickets/{resource_id}/status')
def ticket_status(resource_id: str, body: TicketStatus, request: Request, user=Depends(require('support'))):
    with connection() as db:
        ticket_access(db,resource_id,user)
        db.execute('UPDATE support_tickets SET status=? WHERE id=?',(body.status,resource_id))
        audit(db,user,request,'status:'+body.status,'support',resource_id)
    return {'status':body.status}

@app.get('/api/admin/audit')
def audits(user=Depends(require('audit'))):
    with connection() as db: return [dict(r) for r in db.execute('SELECT * FROM audit_events ORDER BY id DESC LIMIT 200')]

@app.get('/api/admin/dashboard')
def dashboard(user=Depends(require('dashboard'))):
    with connection() as db:
        return {'products':db.execute('SELECT count(*) FROM products').fetchone()[0], 'published':db.execute('SELECT count(*) FROM products WHERE published=1').fetchone()[0], 'orders':db.execute('SELECT count(*) FROM orders').fetchone()[0], 'open_tickets':db.execute("SELECT count(*) FROM support_tickets WHERE status='open'").fetchone()[0], 'low_stock':db.execute('SELECT count(*) FROM products WHERE stock<5').fetchone()[0], 'payments_enabled':False}

class Settings(Input):
    maintenance: bool

@app.get('/api/admin/settings')
def settings(user=Depends(require('settings'))):
    with connection() as db: return {'maintenance':db.execute("SELECT value FROM app_settings WHERE key='maintenance'").fetchone()[0]=='true'}

@app.put('/api/admin/settings')
def update_settings(body: Settings, request: Request, user=Depends(require('settings'))):
    with connection() as db:
        db.execute("UPDATE app_settings SET value=? WHERE key='maintenance'",(json.dumps(body.maintenance),))
        audit(db,user,request,'update','settings','maintenance')
    return body.model_dump()

from .google_auth import router as google_auth_router
app.include_router(google_auth_router)

# Same-origin production hosting; API misses must never become HTML successes.
DIST = Path(os.getenv('MOYA_DIST', 'dist')).resolve()
@app.get('/{path:path}', include_in_schema=False)
def frontend(path: str):
    if path.startswith('api/') or path == 'api': raise HTTPException(404,'Endpoint not found')
    candidate = (DIST / path).resolve()
    if candidate.is_relative_to(DIST) and candidate.is_file(): return FileResponse(candidate)
    if (DIST / 'index.html').exists(): return FileResponse(DIST / 'index.html')
    raise HTTPException(404,'Frontend not built')

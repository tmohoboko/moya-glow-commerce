import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import connection, ROOT
from backend.app.security import password_hash

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('MOYA_DATABASE',str(tmp_path/'test.sqlite3'))
    monkeypatch.setenv('MOYA_SEED_DEMO','true')
    with TestClient(app) as client:
        with connection() as db:
            for role in ['admin','catalogue_manager','support_agent','analyst','customer','other']:
                db.execute('INSERT INTO users VALUES (?,?,?,?,1)',(role,role+'@example.test',password_hash('test-password-123'), 'customer' if role=='other' else role))
            db.execute("INSERT INTO orders(id,user_id,total) VALUES ('demo-order','customer',149)")
            db.execute("INSERT INTO order_items(order_id,product_id,name,quantity,unit_price) VALUES ('demo-order','gentle-cream-cleanser','Gentle Cream Cleanser',1,149)")
        yield client

def headers(client, role='admin'):
    response=client.post('/api/auth/login',json={'email':role+'@example.test','password':'test-password-123'})
    assert response.status_code==200
    return {'Authorization':'Bearer '+response.json()['access_token']}

def test_catalogue_contract_and_health(client):
    assert client.get('/api/products').json()==json.loads((ROOT/'seed-products.json').read_text())
    assert client.get('/api/health').json()['payments']=='disabled'
    assert client.get('/api/readiness').status_code==200
    assert client.get('/api/products/gentle-cream-cleanser').status_code==200
    assert client.get('/api/missing').status_code==404

def test_auth_revocation_and_no_enumeration(client):
    for email in ['admin@example.test','unknown@example.test']:
        response=client.post('/api/auth/login',json={'email':email,'password':'wrong'})
        assert response.status_code==401
        assert response.json()['detail']=='Invalid email or password'
    h=headers(client)
    assert client.get('/api/auth/me',headers=h).json()['role']=='admin'
    assert client.post('/api/auth/logout',headers=h).status_code==204
    assert client.get('/api/auth/me',headers=h).status_code==401

@pytest.mark.parametrize('role,allowed',[
    ('admin',['products','categories','orders','audit','settings','dashboard']),
    ('catalogue_manager',['products','categories']),('support_agent',['orders']),
    ('analyst',['dashboard']),('customer',[])])
def test_rbac_matrix(client,role,allowed):
    h=headers(client,role)
    for resource in ['products','categories','orders','audit','settings','dashboard']:
        assert client.get('/api/admin/'+resource,headers=h).status_code==(200 if resource in allowed else 403)
        assert client.get('/api/admin/'+resource).status_code==401
    if role not in ['admin','catalogue_manager']:
        assert client.post('/api/admin/categories',headers=h,json={'name':'Forbidden'}).status_code==403
    if role!='admin':
        assert client.put('/api/admin/settings',headers=h,json={'maintenance':True}).status_code==403

def test_catalogue_crud_publish_audit_and_foreign_keys(client):
    h=headers(client,'catalogue_manager')
    cat=client.post('/api/admin/categories',headers=h,json={'name':'Temporary'}).json()
    assert client.put('/api/admin/categories/'+cat['id'],headers=h,json={'name':'Changed'}).status_code==200
    body={'name':'Temporary product','price':12.5,'category_id':cat['id'],'stock':4,'published':False}
    p=client.post('/api/admin/products',headers=h,json=body)
    assert p.status_code==201
    pid=p.json()['id']
    assert client.get('/api/products/'+pid).status_code==404
    body['published']=True
    assert client.put('/api/admin/products/'+pid,headers=h,json=body).status_code==200
    assert client.get('/api/products/'+pid).json()['category']=='Changed'
    assert client.delete('/api/admin/categories/'+cat['id'],headers=h).status_code==409
    assert client.delete('/api/admin/products/'+pid,headers=h).status_code==204
    assert client.delete('/api/admin/categories/'+cat['id'],headers=h).status_code==204
    events=client.get('/api/admin/audit',headers=headers(client)).json()
    assert len(events)==6
    assert all(event['request_id'] for event in events)

def test_validation_and_transaction_rollback(client):
    h=headers(client)
    for patch in [{'stock':-1},{'price':-1},{'stock':1.2},{'name':''},{'image':'javascript:alert(1)'},{'role':'admin'}]:
        assert client.post('/api/admin/products',headers=h,json={'name':'Test','price':10,'category_id':'skincare',**patch}).status_code==422
    assert client.post('/api/admin/products',headers=h,json={'name':'Test','price':10,'category_id':'missing'}).status_code==409
    assert client.get('/api/admin/audit',headers=h).json()==[]

def test_support_ownership_reply_close(client):
    customer=headers(client,'customer'); other=headers(client,'other'); support=headers(client,'support_agent')
    result=client.post('/api/support/tickets',headers=customer,json={'subject':'Help','message':'Hello'})
    assert result.status_code==201
    url='/api/support/tickets/'+result.json()['id']
    assert client.get(url,headers=other).status_code==404
    assert client.get('/api/support/tickets',headers=other).json()==[]
    assert client.post(url+'/messages',headers=other,json={'message':'Intrusion'}).status_code==404
    assert client.post(url+'/messages',headers=support,json={'message':'How can we help?'}).status_code==201
    assert len(client.get(url,headers=customer).json()['messages'])==2
    assert client.patch(url+'/status',headers=customer,json={'status':'closed'}).status_code==403
    assert client.patch(url+'/status',headers=support,json={'status':'closed'}).status_code==200
    assert client.post(url+'/messages',headers=customer,json={'message':'Again'}).status_code==409

def test_order_transitions_and_audit(client):
    h=headers(client,'support_agent'); url='/api/admin/orders/demo-order'
    assert len(client.get('/api/admin/orders',headers=h).json())==1
    assert len(client.get(url,headers=h).json()['items'])==1
    assert client.patch(url+'/status',headers=h,json={'status':'completed'}).status_code==409
    for status in ['processing','shipped','completed']:
        assert client.patch(url+'/status',headers=h,json={'status':status}).status_code==200
    assert client.patch(url+'/status',headers=h,json={'status':'pending'}).status_code==409
    assert client.patch(url+'/status',headers=headers(client,'analyst'),json={'status':'cancelled'}).status_code==403

def test_maintenance_and_request_id(client):
    h=headers(client)
    assert client.put('/api/admin/settings',headers={**h,'X-Request-ID':'qa-maintenance'},json={'maintenance':True}).status_code==200
    r=client.get('/api/products',headers={'X-Request-ID':'qa-read'})
    assert r.status_code==503 and r.headers['X-Request-ID']=='qa-read'
    assert r.json()['request_id']=='qa-read'
    assert client.get('/api/health').status_code==200
    assert client.get('/api/admin/products',headers=h).status_code==200
    assert client.put('/api/admin/settings',headers=h,json={'maintenance':False}).status_code==200
    assert client.get('/api/products').status_code==200

def test_login_rate_limit(client):
    for _ in range(15):
        assert client.post('/api/auth/login',json={'email':'no@example.test','password':'bad'}).status_code==401
    response=client.post('/api/auth/login',json={'email':'no@example.test','password':'bad'},headers={'X-Forwarded-For':'different'})
    assert response.status_code==429 and response.headers['Retry-After']=='300'

def test_session_expiry_and_inactive_user(client):
    h=headers(client)
    with connection() as db: db.execute('UPDATE sessions SET expires_at=0')
    assert client.get('/api/auth/me',headers=h).status_code==401
    h=headers(client)
    with connection() as db: db.execute("UPDATE users SET active=0 WHERE id='admin'")
    assert client.get('/api/auth/me',headers=h).status_code==401

def test_import_dry_run_atomic_apply_and_unpublish(client):
    from backend.app.import_catalogue import import_catalogue
    items=[{'id':'replacement','name':'Operator product','price':25,'category':'Operator category'}]
    assert import_catalogue(items)=={'validated':1,'applied':False}
    assert len(client.get('/api/products').json())==30
    with pytest.raises(ValueError): import_catalogue(items+items,True,'admin@example.test')
    assert len(client.get('/api/products').json())==30
    with pytest.raises(ValueError): import_catalogue(items,True,'customer@example.test')
    assert import_catalogue(items,True,'admin@example.test',True)['applied']
    assert [p['id'] for p in client.get('/api/products').json()]==['replacement']
    assert client.get('/api/admin/audit',headers=headers(client)).json()[0]['action']=='import:1'

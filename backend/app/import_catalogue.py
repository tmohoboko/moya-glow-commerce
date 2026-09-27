"""Validate/upsert a public-contract JSON catalogue. Dry run unless --apply."""
import argparse
import json
import re
import uuid
from .db import connection, migrate
from .main import Product

def import_catalogue(items, apply=False, actor_email=None, unpublish_missing=False):
    if not isinstance(items,list) or not items:
        raise ValueError('Expected a nonempty JSON array; empty catalogue replacement is refused')
    normalized=[]; seen=set()
    for item in items:
        if not isinstance(item,dict): raise ValueError('Each product must be an object')
        if set(item)-{'id','name','price','category','image','description','stock','published'}:
            raise ValueError('Unexpected product fields')
        product_id=item.get('id','')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',product_id) or product_id in seen:
            raise ValueError('Product IDs must be unique URL-safe identifiers')
        seen.add(product_id)
        category=item.get('category','').strip()
        if not category or len(category)>100: raise ValueError('Category name required (maximum 100 characters)')
        body=Product(name=item.get('name',''),price=item.get('price'),category_id='validated-later',image=item.get('image','/product.svg'),description=item.get('description',''),stock=item.get('stock',0),published=item.get('published',True))
        normalized.append((product_id,category,body))
    if not apply: return {'validated':len(normalized),'applied':False}
    migrate()
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        actor=db.execute("SELECT id FROM users WHERE email=? AND role='admin' AND active=1",(actor_email,)).fetchone()
        if not actor: raise ValueError('An active admin --actor-email is required')
        for product_id,category,body in normalized:
            existing=db.execute('SELECT id FROM categories WHERE name=?',(category,)).fetchone()
            category_id=existing[0] if existing else uuid.uuid4().hex
            if not existing: db.execute('INSERT INTO categories VALUES (?,?)',(category_id,category))
            body.category_id=category_id
            db.execute('INSERT INTO products VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,price=excluded.price,category_id=excluded.category_id,image=excluded.image,description=excluded.description,stock=excluded.stock,published=excluded.published', (product_id,*body.model_dump().values()))
        if unpublish_missing:
            for row in db.execute('SELECT id FROM products').fetchall():
                if row[0] not in seen: db.execute('UPDATE products SET published=0 WHERE id=?',(row[0],))
        db.execute('INSERT INTO audit_events(actor_id,action,resource,resource_id,request_id) VALUES (?,?,?,?,?)',(actor[0],'import:'+str(len(normalized)),'catalogue','batch',uuid.uuid4().hex))
    return {'validated':len(normalized),'applied':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file');parser.add_argument('--apply',action='store_true');parser.add_argument('--actor-email');parser.add_argument('--unpublish-missing',action='store_true')
    args=parser.parse_args()
    with open(args.file) as source: items=json.load(source)
    print(json.dumps(import_catalogue(items,args.apply,args.actor_email,args.unpublish_missing)))

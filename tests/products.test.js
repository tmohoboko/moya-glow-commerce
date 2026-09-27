import {test} from 'node:test';
import assert from 'node:assert/strict';
import {products, money} from '../src/products.js';
test('original demo catalogue preserves unique product IDs and valid prices',()=>{
  assert.equal(products.length,30);
  assert.equal(new Set(products.map(p=>p.id)).size,30);
  for(const p of products){assert.ok(p.price>0);assert.deepEqual(Object.keys(p),['id','name','price','category','image','description']);}
});
test('ZAR formatting retains amount',()=>{assert.match(money(149),/149/);assert.match(money(298),/298/);});

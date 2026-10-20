import {writeFileSync,readFileSync} from 'node:fs';
import {products} from '../src/products.js';
const target=new URL('../backend/app/catalogue.json',import.meta.url);
const data=JSON.stringify(products,null,2)+'\n';
if(process.argv.includes('--check')){
 if(readFileSync(target,'utf8')!==data) throw new Error('Backend catalogue is out of date: run node scripts/sync-catalogue.mjs');
}else writeFileSync(target,data);

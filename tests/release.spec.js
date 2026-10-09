import {test,expect} from '@playwright/test';
import {products} from '../src/products.js';

test('RELEASE-001 page titles follow navigation, refresh and browser history',async({page})=>{
 await page.goto('/');
 await expect(page).toHaveTitle('L Beauty | Home');
 await page.getByRole('link',{name:'Shop',exact:true}).click();
 await expect(page).toHaveTitle('L Beauty | Services');
 await page.getByRole('heading',{name:'Full Body',exact:true}).click();
 await expect(page).toHaveTitle('Full Body | L Beauty');
 await page.reload();
 await expect(page).toHaveTitle('Full Body | L Beauty');
 await page.getByRole('link',{name:'Bag (0)',exact:true}).click();
 await expect(page).toHaveTitle('L Beauty | Your bag');
 await page.goBack();
 await expect(page).toHaveTitle('Full Body | L Beauty');
 await page.goForward();
 await expect(page).toHaveTitle('L Beauty | Your bag');
 for(const route of ['/missing','/product/missing']){
  await page.goto(route);
  await expect(page).toHaveTitle('Page not found | L Beauty');
 }
});

test('RELEASE-002 narrow layouts keep navigation, service details and bag within viewport',async({page})=>{
 const longest=products.reduce((a,b)=>a.name.length>b.name.length?a:b);
 for(const width of [320,375,768]){
  await page.setViewportSize({width,height:812});
  for(const route of ['/','/shop',`/product/${longest.id}`]){
   await page.goto(route);
   await expect(page.getByRole('link',{name:'Shop',exact:true})).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${route} at ${width}px`).toBe(true);
  }
  await page.getByRole('button',{name:`Add ${longest.name} to bag`,exact:true}).click();
  await page.goto('/cart');
  await expect(page.getByRole('button',{name:`Increase ${longest.name}`,exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`bag at ${width}px`).toBe(true);
  await page.getByRole('button',{name:'Remove',exact:true}).click();
 }
});

test('RELEASE-003 vector branding assets load on home and bag',async({page,request})=>{
 const response=await request.get('/brand/lbeauty-wordmark.svg');
 expect(response.ok()).toBe(true);
 expect(response.headers()['content-type']).toContain('image/svg+xml');
 for(const route of ['/','/cart']){
  await page.goto(route);
  await expect(page.locator('header .brand img')).toHaveAttribute('src','/brand/lbeauty-wordmark.svg');
  await expect(page.locator('footer .brand img')).toHaveAttribute('src','/brand/lbeauty-wordmark.svg');
  await expect.poll(()=>page.locator('.brand img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
 }
});

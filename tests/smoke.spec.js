import {test,expect} from '@playwright/test';
const name='Full Body';
async function add(page){await page.goto('/shop');await page.getByRole('button',{name:`Add ${name} to bag`,exact:true}).click();await page.getByRole('link',{name:'Bag (1)'}).click();}
test('SMOKE-001 homepage loads without fatal JavaScript errors',async({page})=>{const errors=[];page.on('pageerror',error=>errors.push(error.message));await page.goto('/');await expect(page.getByRole('heading',{name:'Feel good. Glow your way.'})).toBeVisible();expect(errors).toEqual([]);});
test('SMOKE-002 catalogue renders 46 services and detail',async({page})=>{await page.goto('/shop');await expect(page.locator('.product')).toHaveCount(46);await page.getByRole('heading',{name,exact:true}).click();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();await expect(page.getByText(/L Beauty · Massage/)).toBeVisible();});
test('SMOKE-003 search locates product and handles no results',async({page})=>{await page.goto('/shop');await page.getByRole('searchbox').fill('Aromatherapy');await expect(page.locator('.product')).toHaveCount(1);await expect(page.getByRole('heading',{name:'Aromatherapy Massage'})).toBeVisible();await page.getByRole('searchbox').fill('nonexistent');await expect(page.getByText(/No services match/)).toBeVisible();});
test('SMOKE-004 category filters products',async({page})=>{await page.goto('/shop');await page.getByLabel('Category',{exact:true}).selectOption('Makeup Looks');await expect(page.locator('.product')).toHaveCount(4);await expect(page.locator('.product .category')).toHaveText(Array(4).fill('Makeup Looks'));});
test('SMOKE-005 add to cart persists on refresh',async({page})=>{await add(page);await expect(page.locator('.cart-item')).toHaveCount(1);await page.reload();await expect(page.locator('.cart-item')).toHaveCount(1);});
test('SMOKE-006 quantity increases and decreases',async({page})=>{await add(page);await page.getByRole('button',{name:`Increase ${name}`}).click();await expect(page.getByLabel('Quantity',{exact:true})).toHaveText('2');await page.getByRole('button',{name:`Decrease ${name}`}).click();await expect(page.getByLabel('Quantity',{exact:true})).toHaveText('1');});
test('SMOKE-007 removal shows empty cart',async({page})=>{await add(page);await page.getByRole('button',{name:'Remove',exact:true}).click();await expect(page.getByRole('heading',{name:'Your bag is empty'})).toBeVisible();await expect(page.getByRole('link',{name:'Bag (0)'})).toBeVisible();});
test('SMOKE-008 subtotal reflects quantity and multiple items',async({page})=>{await add(page);await expect(page.getByTestId('subtotal')).toContainText('450');await page.getByRole('button',{name:`Increase ${name}`}).click();await expect(page.getByTestId('subtotal')).toContainText('900');await page.getByRole('link',{name:'Shop',exact:true}).click();await page.getByRole('button',{name:'Add Back and Neck to bag',exact:true}).click();await page.getByRole('link',{name:'Bag (3)'}).click();await expect(page.getByTestId('subtotal')).toContainText(/1[\s,]?150/);});
test('SMOKE-009 mobile layout and cart remain usable',async({page})=>{await page.setViewportSize({width:375,height:812});await page.goto('/');await expect(page.locator('.product')).toHaveCount(46);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'qa/mobile-home.png',fullPage:true});await add(page);await expect(page.getByRole('button',{name:`Increase ${name}`})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);});
test('SMOKE-010 unknown route and product fail gracefully',async({page})=>{for(const path of ['/missing','/product/missing']){await page.goto(path);await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();await page.getByRole('link',{name:'Back to home'}).click();await expect(page.getByRole('heading',{name:'Feel good. Glow your way.'})).toBeVisible();}await page.screenshot({path:'qa/desktop-home.png',fullPage:true});});
test('SMOKE-011 L Beauty artwork resolves and all categories filter',async({page,request})=>{
 const {products}=await import('../src/products.js');
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 expect(new Set(products.map(p=>p.id)).size).toBe(46);
 await page.goto('/shop');
 for(const category of new Set(products.map(p=>p.category))){
  await page.getByLabel('Category',{exact:true}).selectOption(category);
  await expect(page.locator('.product')).toHaveCount(products.filter(p=>p.category===category).length);
 }
 await page.getByLabel('Category',{exact:true}).selectOption('All');
 await expect.poll(()=>page.locator('.product img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
 for(const name of ['cover','massage-hand-foot','wax','lash-brow','nails','makeup','contact','closing-cover']){
  const response=await request.get(`/catalogue/lbeauty/${name}.jpg`);
  expect(response.ok()).toBe(true);expect(response.headers()['content-type']).toContain('image/jpeg');
 }
 expect(errors).toEqual([]);
});
test('SMOKE-012 starting prices remain visible through detail and cart',async({page})=>{
 const {money}=await import('../src/products.js');
 for(const [name,price] of [['Special Effects',600],['Bridal',1000]]){
  await page.goto('/shop');
  const card=page.locator('.product').filter({has:page.getByRole('heading',{name,exact:true})});
  await expect(card.locator('strong')).toHaveText(`From ${money(price)}`);
  await card.getByRole('heading',{name,exact:true}).click();
  await expect(page.locator('.detail h2')).toHaveText(`From ${money(price)}`);
  await page.getByRole('button',{name:`Add ${name} to bag`,exact:true}).click();
  await page.getByRole('link',{name:'Bag (1)'}).click();
  await expect(page.locator('.cart-item p')).toHaveText(`From ${money(price)} each`);
  await expect(page.getByTestId('subtotal')).toHaveText(`From ${money(price)}`);
  await page.getByRole('button',{name:`Increase ${name}`}).click();
  await expect(page.getByTestId('subtotal')).toHaveText(`From ${money(price*2)}`);
  await page.getByRole('button',{name:'Remove',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your bag is empty'})).toBeVisible();
 }
});

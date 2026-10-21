import {test,expect} from '@playwright/test';
const name='Full Body';
test('SMOKE-001 homepage loads without fatal JavaScript errors',async({page})=>{const errors=[];page.on('pageerror',error=>errors.push(error.message));await page.goto('/');await expect(page.getByRole('heading',{name:'Feel good. Glow your way.'})).toBeVisible();expect(errors).toEqual([]);});
test('SMOKE-002 catalogue renders 46 services and detail',async({page})=>{await page.goto('/shop');await expect(page.locator('.product')).toHaveCount(46);await page.getByRole('heading',{name,exact:true}).click();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();await expect(page.getByText(/L Beauty · Massage/)).toBeVisible();});
test('SMOKE-003 search locates product and handles no results',async({page})=>{await page.goto('/shop');await page.getByRole('searchbox').fill('Aromatherapy');await expect(page.locator('.product')).toHaveCount(1);await expect(page.getByRole('heading',{name:'Aromatherapy Massage'})).toBeVisible();await page.getByRole('searchbox').fill('nonexistent');await expect(page.getByText(/No services match/)).toBeVisible();});
test('SMOKE-004 category filters products',async({page})=>{await page.goto('/shop');await page.getByLabel('Category',{exact:true}).selectOption('Makeup');await expect(page.locator('.product')).toHaveCount(4);await expect(page.locator('.product .category')).toHaveText(Array(4).fill('Makeup · Makeup Looks'));});
test('SMOKE-010 unknown route and product fail gracefully',async({page})=>{for(const path of ['/missing','/product/missing']){await page.goto(path);await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();await page.getByRole('link',{name:'Back to home'}).click();await expect(page.getByRole('heading',{name:'Feel good. Glow your way.'})).toBeVisible();}await page.screenshot({path:`${process.env.QA_SCREENSHOT_DIR||'qa'}/desktop-home.png`,fullPage:true});});
test('SMOKE-011 L Beauty artwork resolves and all categories filter',async({page,request})=>{
 const {products}=await import('../src/products.js');
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 expect(new Set(products.map(p=>p.id)).size).toBe(46);
 await page.goto('/shop');
 const {GROUPS,inGroup}=await import('../src/service-groups.js');
 for(const category of Object.keys(GROUPS)){
  await page.getByLabel('Category',{exact:true}).selectOption(category);
  await expect(page.locator('.product')).toHaveCount(products.filter(p=>inGroup(p.category,category)).length);
 }
 await page.getByLabel('Category',{exact:true}).selectOption('All');
 await expect.poll(()=>page.locator('.product img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
 for(const name of ['cover','massage-hand-foot','wax','lash-brow','nails','makeup','contact','closing-cover']){
  const response=await request.get(`/catalogue/lbeauty/${name}.jpg`);
  expect(response.ok()).toBe(true);expect(response.headers()['content-type']).toContain('image/jpeg');
 }
 expect(errors).toEqual([]);
});
test('SMOKE-012 starting prices remain visible through detail and quotation request',async({page})=>{
 const {money}=await import('../src/products.js');
 for(const [name,price] of [['Special Effects',600],['Bridal',1000]]){
  await page.goto('/services');
  const card=page.locator('.product').filter({has:page.getByRole('heading',{name,exact:true})});
  await expect(card.locator('strong')).toHaveText(`From ${money(price)}`);
  await card.getByRole('heading',{name,exact:true}).click();
  await expect(page.locator('.detail h2')).toHaveText(`From ${money(price)}`);
  await page.getByRole('button',{name:`Request ${name} appointment`,exact:true}).click();
  await expect(page.locator('.booking-service strong')).toHaveText(`From ${money(price)}`);
 }
});
test('SMOKE-013 all 46 service images and prices are preserved without cart controls',async({page,request})=>{
 const {products,money}=await import('../src/products.js');
 expect(products).toHaveLength(46);
 expect(new Set(products.map(p=>p.image)).size).toBe(46);
 expect(new Set(products.map(p=>p.category)).size).toBe(12);
 await page.goto('/services');
 for(const product of products){
  const card=page.locator(`.product[data-service-id="${product.id}"]`);
  await expect(card.locator('img')).toHaveAttribute('src',product.image);
  await expect(card.locator('strong')).toHaveText(`${product.priceFrom?'From ':''}${money(product.price)}`);
  await expect(card.getByRole('button')).toHaveAccessibleName(`Request ${product.name} appointment`);
  expect((await request.get(product.image)).ok()).toBe(true);
 }
 await expect(page.getByRole('button',{name:/Add .* to bag/})).toHaveCount(0);
 await expect.poll(()=>page.locator('.product img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
});

test('SMOKE-014 gallery follows the same grouped categories and focused treatment framing',async({page,request})=>{
 const {products}=await import('../src/products.js');
 const {serviceGallery}=await import('../src/service-gallery.js');
 const {groupStats,inGroup}=await import('../src/service-groups.js');
 const photos=serviceGallery(products), groups=groupStats(products,photos);
 await page.goto('/services#photos');
 await expect(page.locator('.portfolio figure')).toHaveCount(photos.length);
 await expect(page.locator('body')).not.toContainText(/AI[ -]?generated/i);
 expect(new Set(photos.map(p=>p.src)).size).toBe(photos.length);
 for(const group of groups){
  await page.getByLabel('Category',{exact:true}).selectOption(group.name);
  await expect(page.locator('.portfolio figure')).toHaveCount(photos.filter(p=>p.categories.some(c=>inGroup(c,group.name))).length);
 }
 await page.getByLabel('Category',{exact:true}).selectOption('Lashes & Brows');
 await expect(page.locator('.product .treatment-photo[data-focused="true"]')).toHaveCount(9);
 for(const photo of photos)expect((await request.get(photo.src)).ok()).toBe(true);
});

test('SMOKE-015 photo interactions support hover, keyboard and reduced motion',async({page})=>{
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.goto('/shop');
 const card=page.locator('.product').first();
 const image=card.locator('.photo-frame img');
 const cue=card.locator('.photo-action');
 await expect(cue).toHaveCSS('opacity','0');
 await card.hover();
 await expect(cue).toHaveCSS('opacity','1');
 await expect.poll(()=>image.evaluate(img=>getComputedStyle(img).transform)).not.toBe('none');
 await page.emulateMedia({reducedMotion:'reduce'});
 await expect(image).toHaveCSS('transform','none');
 await expect(image).toHaveCSS('transition-duration','0s');
 await page.mouse.move(0,0);
 await card.locator('a').focus();
 await expect(cue).toHaveCSS('opacity','1');
 await expect(image).toHaveCSS('transform','none');
});

test('SMOKE-005 service selection opens its quotation request',async({page})=>{
 await page.goto('/services');
 await page.getByRole('button',{name:'Request Full Body appointment',exact:true}).click();
 await expect(page).toHaveURL(/service=massage-full-body-450/);
 await expect(page.locator('.booking-service h2')).toHaveText('Full Body');
});
test('SMOKE-006 gallery and contact are first-class navigation',async({page})=>{
 await page.goto('/');
 await page.getByRole('link',{name:'Gallery',exact:true}).click();
 const {products}=await import('../src/products.js');
 const {serviceGallery}=await import('../src/service-gallery.js');
 await expect(page.locator('.portfolio figure')).toHaveCount(serviceGallery(products).length);
 await page.getByRole('link',{name:'Contact',exact:true}).click();
 await expect(page.getByRole('link',{name:'Enquire on WhatsApp'})).toHaveAttribute('href','https://wa.me/27847477711');
});
test('SMOKE-007 legacy bag links lead to appointment guidance',async({page})=>{
 await page.goto('/cart');
 await expect(page.getByRole('heading',{name:'Plan an appointment'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Choose a service'})).toBeVisible();
});
test('SMOKE-008 protected staff calendar rejects customer access',async({page})=>{
 await page.goto('/salon');
 await expect(page.getByText('Log in with your authorised salon account.')).toBeVisible();
});
test('SMOKE-009 mobile layout and booking request remain usable',async({page})=>{
 await page.setViewportSize({width:375,height:812});
 for(const route of ['/','/services','/book?service=massage-full-body-450','/contact']){
  await page.goto(route);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route).toBe(true);
 }
 await page.goto('/');
 await page.screenshot({path:`${process.env.QA_SCREENSHOT_DIR||'qa'}/mobile-home.png`,fullPage:true});
});

import {test,expect} from '@playwright/test';
import {products} from '../src/products.js';
import {serviceGallery} from '../src/service-gallery.js';
import {groupStats,serviceGroup,inGroup} from '../src/service-groups.js';

test('PATCH-001 groups are ranked by distinct photos with waxing always last',async({page})=>{
 const groups=groupStats(products,serviceGallery(products));
 expect(groups.map(g=>g.name)).toEqual(['Lashes & Brows','Nails','Makeup','Hands & Feet','Massage','Waxing']);
 expect(groups[0].pictures).toBeGreaterThan(groups[1].pictures);
 expect(groups.find(g=>g.name==='Waxing').services).toBe(13);
 await page.goto('/services');
 await expect(page.locator('.category-nav button')).toHaveCount(6);
 await expect(page.locator('.category-nav button').first()).toContainText('Lashes & Brows');
 await expect(page.locator('.category-nav button').last()).toContainText('Waxing');
 const ids=await page.locator('.product').evaluateAll(cards=>cards.map(card=>card.dataset.serviceId));
 const ranks=ids.map(id=>groups.findIndex(group=>group.name===serviceGroup(products.find(p=>p.id===id).category)));
 expect(ranks).toEqual([...ranks].sort((a,b)=>a-b));
 await page.getByLabel('Category',{exact:true}).selectOption('Waxing');
 await expect(page.locator('.product')).toHaveCount(13);
 expect(new Set(products.filter(p=>inGroup(p.category,'Waxing')).map(p=>p.category)).size).toBe(3);
});

test('PATCH-002 lash detail and request reuse the treatment crop without exposing full portraits',async({page})=>{
 const service=products.find(p=>p.name==='Classic'&&p.category==='Lash Extensions');
 await page.goto('/services');
 await page.getByLabel('Category',{exact:true}).selectOption('Lashes & Brows');
 await expect(page.locator('.product .treatment-photo[data-focused="true"]')).toHaveCount(9);
 await page.locator(`.product[data-service-id="${service.id}"]`).getByRole('heading').click();
 await expect(page.locator('.detail .treatment-photo[data-focused="true"]')).toHaveCount(1);
 await expect.poll(()=>page.locator('.detail img').evaluate(img=>img.complete&&img.naturalWidth>0)).toBe(true);
 await page.getByRole('button',{name:`Request ${service.name} appointment`,exact:true}).click();
 await expect(page.locator('.booking-service .treatment-photo[data-focused="true"]')).toHaveCount(1);
});

test('PATCH-003 public calendar switches day/week and keeps dates consistent without leaking appointments',async({page})=>{
 await page.goto('/calendar');
 await expect(page).toHaveTitle('L Beauty | Appointment calendar');
 await expect(page.getByRole('button',{name:'Week',exact:true})).toHaveAttribute('aria-pressed','true');
 const input=page.getByLabel('Calendar date',{exact:true});
 const before=await input.getAttribute('value');
 await page.getByRole('button',{name:'Next week'}).click();
 const after=await input.getAttribute('value');
 expect(new Date(after+'T12:00:00Z')-new Date(before+'T12:00:00Z')).toBe(7*86400000);
 await page.getByRole('button',{name:'Day',exact:true}).click();
 await expect(page.getByRole('button',{name:'Day',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(page.getByRole('group',{name:'Calendar dates'}).getByRole('button')).toHaveCount(1);
 await expect(page.getByRole('region',{name:'Day appointment calendar'}).locator('.calendar-column')).toHaveCount(1);
 await page.reload();
 await expect(page.getByRole('button',{name:'Day',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(input).toHaveValue(after);
 await page.getByRole('button',{name:'Week',exact:true}).click();
 await expect(page.getByRole('region',{name:'Week appointment calendar'}).locator('.calendar-column')).toHaveCount(7);
 await expect(page.getByText('Choose a treatment and accept your quotation to see available appointment slots.')).toBeVisible();
 for(const width of [320,375,768]){
  await page.setViewportSize({width,height:812});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px`).toBe(true);
 }
 await page.screenshot({path:`${process.env.QA_SCREENSHOT_DIR||'qa'}/patch-calendar.png`,fullPage:true});
});

test('PATCH-004 focused lash pictures remain sharp within their frames at mobile size',async({page})=>{
 await page.setViewportSize({width:375,height:812});
 await page.goto('/services');
 await page.getByLabel('Category',{exact:true}).selectOption('Lashes & Brows');
 await expect.poll(()=>page.locator('.product img').evaluateAll(images=>images.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
 const frames=await page.locator('.product .treatment-photo').evaluateAll(frames=>frames.map(frame=>{const image=frame.querySelector('img');return {frame:frame.getBoundingClientRect().width,image:image.getBoundingClientRect().width,source:image.naturalWidth,top:getComputedStyle(image).top}}));
 expect(frames.every(frame=>frame.image>frame.frame&&frame.source>=1000)).toBe(true);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:`${process.env.QA_SCREENSHOT_DIR||'qa'}/patch-lashes-mobile.png`,fullPage:true});
});

test('PATCH-005 booking form disables occupied slots and recovers from a last-moment conflict',async({page})=>{
 const quoteId='123e4567-e89b-42d3-a456-426614174001';
 const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Johannesburg',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+86400000));
 const occupied=Math.floor(new Date(day+'T09:00:00+02:00').getTime()/1000),available=occupied+900;
 const quote={id:quoteId,number:'LBQ-QA',service_name:'Full Body',notes:'Test quotation',amount:45000,duration:60,buffer:15,status:'accepted',revision:1,expired:false,expires_at:available+86400,terms:'Agreed treatment.'};
 await page.route('**/api/auth/me',route=>route.fulfill({json:{id:'qa-customer',email:'qa@example.com'}}));
 await page.route('**/api/quotes?*',route=>route.fulfill({json:[quote]}));
 let submitted=null;
 await page.route('**/api/bookings**',route=>route.request().method()==='GET'?route.fulfill({json:[]}):(submitted=route.request().postDataJSON(),route.fulfill({status:409,json:{detail:'This time has just been taken. Choose another available slot.'}})));
 await page.route('**/api/availability?*',route=>{const url=new URL(route.request().url()),selected=url.searchParams.get('day');return route.fulfill({json:{day:selected,view:'day',duration:60,buffer:15,slots:[available],days:[{day:selected,closed:false,slots:[available],unavailable:[occupied]}]}})});
 await page.goto('/appointments');
 await page.getByLabel('Appointment date',{exact:true}).fill(day);
 const form=page.getByRole('form',{name:'Appointment booking form'});
 await expect(form.getByRole('button',{name:'09:00 unavailable',exact:true})).toBeDisabled();
 await expect(form.getByRole('button',{name:'Confirm appointment',exact:true})).toBeDisabled();
 await expect(form.getByLabel('Available time',{exact:true}).locator('option')).toHaveCount(2);
 await form.getByLabel('Available time',{exact:true}).selectOption(String(available));
 await expect(form.getByRole('button',{name:'09:15',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(form.getByRole('button',{name:'09:15',exact:true})).toHaveCSS('background-color','rgb(225, 227, 225)');
 await page.reload();
 await expect(form.getByLabel('Available time',{exact:true})).toHaveValue(String(available));
 await expect(form.getByRole('button',{name:'09:15',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(form.getByRole('button',{name:'09:15',exact:true})).toHaveCSS('background-color','rgb(225, 227, 225)');
 await form.getByRole('button',{name:'Refresh available times',exact:true}).click();
 await expect(form.getByRole('button',{name:'Confirm appointment',exact:true})).toBeDisabled();
 await form.getByLabel('Available time',{exact:true}).selectOption(String(available));
 await form.getByRole('button',{name:'Confirm appointment',exact:true}).click();
 await expect(form.getByRole('alert')).toHaveText('This time has just been taken. Choose another available slot.');
 expect(submitted).toEqual({quote_id:quoteId,starts_at:available,revision:1});
 await expect(form.getByRole('button',{name:'Confirm appointment',exact:true})).toBeDisabled();
 await expect(form.getByLabel('Available time',{exact:true})).toHaveValue('');
 await expect(page.getByText('Confirmed',{exact:true})).toHaveCount(0);
 await page.setViewportSize({width:320,height:812});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:`${process.env.QA_SCREENSHOT_DIR||'qa'}/available-time-picker.png`,fullPage:true});
});


test('PATCH-006 supplied photos, natural nails and cat-eye finish are correctly separated',async({page,request})=>{
 const overlay=products.find(p=>p.id==='gel-acrylic-nail-enhancements-acrylic-overlay-1-any-colour-150');
 expect(overlay.category).toBe('Natural Nails');
 expect(overlay.price).toBe(150);
 expect(overlay.image).toContain('natural-acrylic');
 expect(products.filter(p=>serviceGroup(p.category)==='Waxing').every(p=>/refresh-wax|focus-body-wax|focus-intimate-wax/.test(p.image))).toBe(true);
 await page.goto('/gallery');
 await page.getByRole('button',{name:'Cat eye',exact:true}).click();
 await expect(page.locator('.portfolio figure')).toHaveCount(1);
 await expect(page.locator('.portfolio figure')).toContainText('Cat eye nail finish');
 await page.getByRole('button',{name:'Before & after',exact:true}).click();
 await expect(page.locator('.portfolio figure')).toHaveCount(3);
 await expect(page.locator('.portfolio img')).toHaveCount(3);
 const photos=serviceGallery(products).filter(p=>p.src.includes('/client-oct21/'));
 expect(photos).toHaveLength(11);
 for(const photo of photos) expect((await request.get(photo.src)).ok()).toBe(true);
 expect(serviceGallery(products).some(p=>p.src.includes('20261021-03'))).toBe(false);
});

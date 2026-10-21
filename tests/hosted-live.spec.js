import {test,expect} from '@playwright/test';
import fs from 'node:fs';

test('HOSTED-001 real customer registration, quotation, session persistence and private live calendar',async({page,browser,request})=>{
 test.setTimeout(120000);
 test.skip(!process.env.BASE_URL,'Runs against the deployed frontend and its real API only.');
 const base=process.env.BASE_URL;
 const ready=await request.get('/api/readiness');expect(ready.ok()).toBe(true);
 expect(await ready.json()).toMatchObject({ready:true,database:true,stripe:true,payment_mode:'test'});
 const config=await (await request.get('/api/booking/config')).json();expect(config.timezone).toBe('Africa/Johannesburg');
 const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Johannesburg',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+86400000));
 const response=await request.get(`/api/calendar/availability?day=${day}`);expect(response.ok()).toBe(true);expect(response.headers()['cache-control']).toBe('no-store');
 const availability=await response.json();expect(availability.timezone).toBe('Africa/Johannesburg');
 expect(Object.keys(availability.days[0]).sort()).toEqual(['booked','closed','day','slots','unavailable']);
 expect((await request.get('/api/bookings')).status()).toBe(401);
 expect((await request.get('/api/quotes')).status()).toBe(401);
 await page.goto('/calendar');await page.getByLabel('Calendar date',{exact:true}).fill(day);await page.getByRole('button',{name:'Day',exact:true}).click();
 const grid=page.getByRole('group',{name:'Day time slots'});await expect(grid.getByRole('button')).toHaveCount(33);
 await expect(grid.getByRole('button',{name:'17:00 unavailable',exact:true})).toBeDisabled();
 await page.screenshot({path:'qa/evidence/2026-10-22/hosted-calendar.png',fullPage:true});
 const email=`release-qa-${crypto.randomUUID()}@example.com`,password=crypto.randomUUID()+'-QA';
 await page.goto('/book?service=massage-full-body-450');await page.getByRole('button',{name:'Log in to request a quotation'}).click();
 await page.getByRole('button',{name:'New here? Create an account'}).click();await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page).toHaveURL(/\/book\?service=massage-full-body-450$/);
 await page.getByLabel('Your name',{exact:true}).fill('Release QA — artificial customer');await page.getByLabel('Contact number',{exact:true}).fill('0800000000');await page.getByLabel('Treatment details',{exact:true}).fill('Automated software delivery test only. No real visit requested; do not contact.');await page.getByRole('button',{name:'Request quotation',exact:true}).click();
 await expect(page.getByText('Awaiting quotation',{exact:true})).toBeVisible();await page.reload();await expect(page.getByText('Awaiting quotation',{exact:true})).toBeVisible();
 const quotes=await page.request.get(base+'/api/quotes');expect(quotes.ok()).toBe(true);const quote=(await quotes.json())[0];expect(quote.amount).toBeNull();
 expect((await page.request.get(base+'/api/staff/calendar?day='+day)).status()).toBe(403);
 expect((await page.request.post(base+'/api/bookings',{headers:{Origin:base},data:{quote_id:quote.id,starts_at:2000000000,revision:1}})).status()).toBe(409);
 await page.goto('/account');await page.getByRole('button',{name:'Log out',exact:true}).click();await expect(page.getByRole('heading',{name:'Welcome back'})).toBeVisible();
 const fresh=await browser.newContext();const freshPage=await fresh.newPage();
 try{await freshPage.goto(base+'/account');await freshPage.getByLabel('Email',{exact:true}).fill(email);await freshPage.getByLabel('Password',{exact:true}).fill(password);await freshPage.getByRole('button',{name:'Log in',exact:true}).click();await expect(freshPage.getByRole('heading',{name:'My account',exact:true})).toBeVisible();await freshPage.goto(base+'/appointments');await expect(freshPage.getByText('Awaiting quotation',{exact:true})).toBeVisible();await freshPage.screenshot({path:'qa/evidence/2026-10-22/hosted-quotation.png',fullPage:true});await freshPage.goto(base+'/account');await freshPage.getByRole('button',{name:'Log out',exact:true}).click();await expect(freshPage.getByRole('heading',{name:'Welcome back'})).toBeVisible();}finally{await fresh.close()}
 fs.writeFileSync('qa/evidence/2026-10-22/hosted-journey.json',JSON.stringify({base_url:base,checked_at:new Date().toISOString(),quote_id:quote.id,passed:true,calendar_enabled:config.enabled,availability_slots:availability.slots.length,scope:'Real browser + production HTTPS API + durable database; no staff fixture, no mocked route, no payment claim.'},null,2));
});

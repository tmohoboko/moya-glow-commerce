import {test,expect} from '@playwright/test';

test('ACCOUNT-004 session lookup has an explicit loading state',async({page})=>{
 let release;
 const gate=new Promise(resolve=>{release=resolve});
 await page.route('**/api/auth/me',async route=>{await gate;await route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'Please log in to continue.'})})});
 await page.goto('/account');
 await expect(page.getByText('Checking your session…',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeDisabled();
 release();
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeEnabled();
});

test('ACCOUNT-005 service unavailability is distinct from logged out and can recover',async({page})=>{
 let available=false;
 await page.route('**/api/auth/me',route=>route.fulfill({status:available?401:503,contentType:'application/json',body:JSON.stringify({detail:available?'Please log in to continue.':'Account service temporarily unavailable.'})}));
 await page.goto('/account');
 await expect(page.getByRole('alert')).toHaveText('Account service temporarily unavailable.');
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeDisabled();
 available=true;
 await page.getByRole('button',{name:'Retry connection',exact:true}).click();
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeEnabled();
 await expect(page.getByRole('alert')).toHaveCount(0);
});

test.beforeEach(async({request})=>{
 await expect.poll(async()=>{try{return(await request.get('/api/health')).status()}catch{return 0}}).toBe(200);
});

test('ACCOUNT-001 register, refresh, logout and login use a private server session',async({page,context})=>{
 const email=`customer-${crypto.randomUUID()}@example.com`,password='local-browser-test-password';
 await page.goto('/account');
 await page.getByRole('button',{name:'New here? Create an account'}).click();
 await page.getByLabel('Email',{exact:true}).fill(email);
 await page.getByLabel('Password',{exact:true}).fill(password);
 await page.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page.getByText(`Signed in as ${email}`)).toBeVisible();
 await expect(page.getByText('No appointments yet.',{exact:false})).toBeVisible();
 const cookie=(await context.cookies()).find(item=>item.name==='lb_session');
 expect(cookie.httpOnly).toBe(true);
 expect(cookie.sameSite).toBe('Lax');
 expect(await page.evaluate(()=>JSON.stringify(localStorage))).not.toContain(cookie.value);
 await page.reload();
 await expect(page.getByRole('heading',{name:'My account',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Log out',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Welcome back'})).toBeVisible();
 await page.getByLabel('Email',{exact:true}).fill(email);
 await page.getByLabel('Password',{exact:true}).fill('incorrect-test-password');
 await page.getByRole('button',{name:'Log in',exact:true}).click();
 await expect(page.getByRole('alert')).toHaveText('Email or password is incorrect.');
 await page.getByLabel('Password',{exact:true}).fill(password);
 await page.getByRole('button',{name:'Log in',exact:true}).click();
 await expect(page.getByText(`Signed in as ${email}`)).toBeVisible();
});

test('ACCOUNT-002 quotation selection survives login and registration',async({page})=>{
 await page.goto('/book?service=massage-full-body-450');
 await page.getByRole('button',{name:'Log in to request a quotation'}).click();
 await page.getByRole('button',{name:'New here? Create an account'}).click();
 await page.getByLabel('Email',{exact:true}).fill(`booking-${crypto.randomUUID()}@example.com`);
 await page.getByLabel('Password',{exact:true}).fill('local-browser-test-password');
 await page.getByRole('button',{name:'Create account',exact:true}).click();
 await expect(page).toHaveURL(/\/book\?service=massage-full-body-450$/);
 await expect(page.getByRole('heading',{name:'Full Body',exact:true})).toBeVisible();
 await page.getByLabel('Your name',{exact:true}).fill('Browser Customer');
 await page.getByLabel('Contact number',{exact:true}).fill('0800000000');
 await page.getByLabel('Treatment details',{exact:true}).fill('Please confirm the full body treatment.');
 await page.getByRole('button',{name:'Request quotation',exact:true}).click();
 await expect(page).toHaveURL(/\/appointments$/);
 await expect(page.getByText('Awaiting quotation',{exact:true})).toBeVisible();
 await page.reload();
 await expect(page.getByRole('heading',{name:'Full Body',exact:true})).toBeVisible();
});

test('ACCOUNT-003 payment return never invents a receipt or loses the appointment route',async({page})=>{
 await page.goto('/checkout/return?order=123e4567-e89b-42d3-a456-426614174000');
 await expect(page.getByRole('alert')).toHaveText('Please log in to continue.');
 await expect(page.getByRole('heading',{name:'Test payment confirmed'})).toHaveCount(0);
 await page.getByRole('button',{name:'View appointments',exact:true}).click();
 await expect(page).toHaveURL(/\/appointments$/);
});

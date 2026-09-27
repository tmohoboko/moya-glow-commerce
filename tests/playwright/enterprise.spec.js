import {test,expect} from '@playwright/test';
async function login(page,role='admin') {
  await page.goto('/admin');
  await page.getByLabel('Email',{exact:true}).fill(`${role}@example.test`);
  await page.getByLabel('Password',{exact:true}).fill('browser-test-only-pass');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('button',{name:'Sign out'})).toBeVisible();
}
test('login rejects bad credentials and admin is protected',async({page})=>{
  await page.goto('/admin/products');
  await expect(page.getByRole('heading',{name:'Welcome back'})).toBeVisible();
  await page.getByLabel('Email',{exact:true}).fill('admin@example.test');
  await page.getByLabel('Password',{exact:true}).fill('incorrect');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Invalid email or password');
});
test('admin category and product create edit publish delete; audit written',async({page})=>{
  await login(page);
  await page.getByRole('link',{name:'Categories',exact:true}).click();
  await page.getByRole('button',{name:'New category'}).click();
  await page.getByLabel('Name',{exact:true}).fill('QA category');
  await page.getByRole('button',{name:'Save',exact:true}).click();
  await expect(page.getByRole('cell',{name:'QA category',exact:true})).toBeVisible();
  await page.getByRole('link',{name:'Products',exact:true}).click();
  await page.getByRole('button',{name:'New product'}).click();
  await page.getByLabel('Name',{exact:true}).fill('QA cream');
  await page.getByLabel('Price (ZAR)').fill('42');
  await page.getByLabel('Product category').selectOption({label:'QA category'});
  await page.getByLabel('Stock',{exact:true}).fill('8');
  await page.getByLabel('Published',{exact:true}).check();
  await page.getByRole('button',{name:'Save',exact:true}).click();
  const row=page.getByRole('row').filter({hasText:'QA cream'});
  await expect(row).toContainText('Yes');
  const catalogue=await page.request.get('/api/products');
  expect((await catalogue.json()).some(p=>p.name==='QA cream')).toBe(true);
  await row.getByRole('button',{name:'Edit'}).click();
  await page.getByLabel('Stock',{exact:true}).fill('9');
  await page.getByLabel('Published',{exact:true}).uncheck();
  await page.getByRole('button',{name:'Save',exact:true}).click();
  await expect(row).toContainText('No');
  page.on('dialog',dialog=>dialog.accept());
  await row.getByRole('button',{name:'Delete'}).click();
  await expect(row).toHaveCount(0);
  await page.getByRole('link',{name:'Categories',exact:true}).click();
  await page.getByRole('row').filter({hasText:'QA category'}).getByRole('button',{name:'Delete'}).click();
  await expect(page.getByRole('cell',{name:'QA category',exact:true})).toHaveCount(0);
  await page.getByRole('link',{name:'Audit',exact:true}).click();
  await expect(page.getByRole('cell',{name:'delete',exact:true}).first()).toBeVisible();
});
test('support ticket message happy path',async({page})=>{
  await login(page,'customer');
  await page.getByLabel('Subject',{exact:true}).fill('Delivery question');
  await page.getByLabel('Message',{exact:true}).fill('Please help with delivery');
  await page.getByRole('button',{name:'Create ticket'}).click();
  await page.getByRole('button',{name:'Delivery question · open'}).click();
  await expect(page.getByText('Please help with delivery',{exact:true})).toBeVisible();
  await page.getByLabel('Reply',{exact:true}).fill('An extra detail');
  await page.getByRole('button',{name:'Send reply'}).click();
  await expect(page.getByText('An extra detail',{exact:true})).toBeVisible();
});
test('staff order detail and status update',async({page})=>{
  await login(page,'support_agent');
  await page.getByRole('link',{name:'Orders',exact:true}).click();
  await page.getByRole('button',{name:/test-order/}).click();
  await expect(page.getByText(/Demo item × 1/)).toBeVisible();
  await page.getByLabel('Next status').selectOption('processing');
  await expect(page.getByText('Status: processing · ZAR 149')).toBeVisible();
});
test('role navigation restricts analyst; logout clears UI',async({page})=>{
  await login(page,'analyst');
  await expect(page.getByRole('link',{name:'Products',exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Sign out'}).click();
  await expect(page.getByRole('heading',{name:'Welcome back'})).toBeVisible();
});
test('maintenance pauses catalogue and can be reversed',async({page})=>{
  await login(page);
  await page.getByRole('link',{name:'Settings',exact:true}).click();
  await page.getByRole('button',{name:'Enable maintenance'}).click();
  await expect(page.getByRole('button',{name:'Disable maintenance'})).toBeVisible();
  expect((await page.request.get('/api/products')).status()).toBe(503);
  await page.getByRole('button',{name:'Disable maintenance'}).click();
  await expect(page.getByRole('button',{name:'Enable maintenance'})).toBeVisible();
  expect((await page.request.get('/api/products')).status()).toBe(200);
});
test('database storefront preserves original catalogue and cart',async({page})=>{
  await page.goto('/shop');
  await expect(page.locator('.product')).toHaveCount(30);
  await page.getByRole('button',{name:'Add Gentle Cream Cleanser to bag',exact:true}).click();
  await page.getByRole('link',{name:'Bag (1)'}).click();
  await expect(page.getByTestId('subtotal')).toContainText('149');
  await expect(page.getByText('Demo storefront. Orders and payments are not available.')).toBeVisible();
});

test('Google is safely disabled without configuration; password login remains',async({page})=>{
  await page.goto('/account');
  await expect(page.getByRole('button',{name:'Continue with Google'})).toBeDisabled();
  await expect(page.getByText('Google sign-in is currently unavailable.')).toBeVisible();
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeEnabled();
});
test('Google button is offered only for an enabled provider',async({page})=>{
  await page.route('**/api/auth/providers',route=>route.fulfill({json:{providers:['password','google']}}));
  await page.goto('/login');
  await expect(page.getByRole('button',{name:'Continue with Google'})).toBeEnabled();
});
test('Google return exchanges handoff without URL tokens',async({page})=>{
  await page.route('**/api/auth/google/session',async route=>{
    expect(route.request().headers()['x-moya-oauth']).toBe('1');
    await route.fulfill({status:401,json:{detail:'Google sign-in expired; please try again'}});
  });
  await page.goto('/account?google=complete');
  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByRole('alert')).toContainText('Google sign-in expired');
});
test('static fallback keeps password form and Google disabled',async({page})=>{
  for(const endpoint of ['providers','login']) await page.route(`**/api/auth/${endpoint}`,route=>route.fulfill({contentType:'text/html',body:'<html>Static fallback</html>'}));
  await page.goto('/account');
  await expect(page.getByRole('button',{name:'Continue with Google'})).toBeDisabled();
  await page.getByLabel('Email',{exact:true}).fill('customer@example.test');
  await page.getByLabel('Password',{exact:true}).fill('browser-test-only-pass');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Account services are unavailable on this host');
});
test('successful Google return uses ordinary Moya account session',async({page})=>{
  const session=await page.request.post('/api/auth/login',{data:{email:'customer@example.test',password:'browser-test-only-pass'}});
  expect(session.status()).toBe(200);
  const data=await session.json();
  await page.route('**/api/auth/google/session',route=>route.fulfill({json:data}));
  await page.goto('/account?google=complete');
  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByRole('button',{name:'Sign out'})).toBeVisible();
  await expect(page.getByText('customer@example.test · customer')).toBeVisible();
});

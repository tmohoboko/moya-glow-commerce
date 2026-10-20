import React,{useCallback,useEffect,useRef,useState} from 'react';
import {money} from './products';
import {api} from './api';

export function Account({session,go}){
 const {user,status,message,setUser:onUser}=session;
 const [register,setRegister]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false),[orders,setOrders]=useState(null);
 useEffect(()=>{if(!user)return;let active=true;api('/api/orders').then(value=>{if(active)setOrders(value)}).catch(e=>{if(active){setError(e.message);if(e.status===401)onUser(null)}});return()=>{active=false}},[user,onUser]);
 async function submit(event){
  event.preventDefault();
  if(status==='checking'||status==='unavailable')return;
  setError('');setBusy(true);
  const fields=new FormData(event.currentTarget);
  try{onUser(await api(`/api/auth/${register?'register':'login'}`,{method:'POST',body:JSON.stringify({email:fields.get('email'),password:fields.get('password')})}));if(new URLSearchParams(location.search).get('next')==='cart')go('/cart')}
  catch(e){setError(e.message)}finally{setBusy(false)}
 }
 async function logout(){setBusy(true);setError('');try{await api('/api/auth/logout',{method:'POST'});onUser(null);setOrders(null)}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className="account-panel"><p className="eyebrow">YOUR L BEAUTY ACCOUNT</p><h1>{user?'My account':register?'Create account':'Welcome back'}</h1>
 {status==='checking'&&<p role="status">Checking your session…</p>}
 {status==='unavailable'&&<div><p className="form-error" role="alert">{message}</p><button className="text-button" onClick={session.refresh}>Retry connection</button></div>}
 {error&&<p className="form-error" role="alert">{error}</p>}
 {user?<><p>Signed in as <strong>{user.email}</strong></p><button disabled={busy} onClick={logout}>Log out</button><div className="order-history"><h2>Your test orders</h2>{orders===null?<p>Loading orders…</p>:orders.length?orders.map(order=><article className="order-row" key={order.id}><div><strong>{money(order.amount/100)}</strong><p>{new Date(order.created_at*1000).toLocaleDateString('en-ZA')} · {order.items.map(item=>`${item.name} × ${item.quantity}`).join(', ')}</p><small>Reference: {order.id}</small></div><span className="order-status">{order.status==='paid'?'Test payment confirmed':order.status==='pending'?'Awaiting payment':order.status==='expired'?'Checkout expired':'Payment failed'}</span></article>):<p>No orders yet. Explore the services and add something to your bag.</p>}</div></>:<><p>{register?'Create an account to try our test checkout and see your orders.':'Log in to view your orders or continue to test checkout.'}</p><form onSubmit={submit} className="account-form"><label>Email<input type="email" name="email" autoComplete="email" required maxLength={254}/></label><label>Password<input type="password" name="password" autoComplete={register?'new-password':'current-password'} required minLength={12} maxLength={128} aria-describedby="password-help"/></label><small id="password-help">Use at least 12 characters.</small><button disabled={busy||status==='checking'||status==='unavailable'} type="submit">{busy?'Please wait…':register?'Create account':'Log in'}</button></form><button className="text-button" onClick={()=>{setRegister(!register);setError('')}}>{register?'Already have an account? Log in':'New here? Create an account'}</button></>}
 </section>;
}

export function CheckoutButton({cart,session,go}){
 const {user,status}=session;
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const [attempt,setAttempt]=useState(null);
 async function checkout(){
  if(status==='checking'||status==='unavailable')return;
  if(!user){go('/account?next=cart');return}
  setError('');setBusy(true);
  const items=Object.entries(cart).sort(([a],[b])=>a.localeCompare(b)).map(([id,quantity])=>({id,quantity}));
  const fingerprint=JSON.stringify(items);
  const request_key=attempt?.fingerprint===fingerprint?attempt.key:crypto.randomUUID();
  setAttempt({fingerprint,key:request_key});
  try{
   const result=await api('/api/checkout',{method:'POST',body:JSON.stringify({items,request_key})});
   const target=new URL(result.url);
   if(target.protocol!=='https:'||target.hostname!=='checkout.stripe.com')throw new Error('Unable to open the test checkout.');
   sessionStorage.setItem('lb-checkout-order',result.order_id);
   location.assign(target.href);
  }catch(e){setError(e.message);if(e.status===409)setAttempt(null);if(e.status===401)session.setUser(null)}finally{setBusy(false)}
 }
 return <><p className="test-badge">Test checkout · No real charge</p>{error&&<p className="form-error" role="alert">{error}</p>}<button disabled={busy||status==='checking'||status==='unavailable'} onClick={checkout}>{busy?'Opening checkout…':status==='checking'?'Checking your session…':status==='unavailable'?'Account service unavailable':user?'Continue to Stripe test checkout':'Log in to test checkout'}</button></>;
}

export function CheckoutResult({cancelled,onPaid,go}){
 const orderId=new URLSearchParams(location.search).get('order');
 const [order,setOrder]=useState(null),[error,setError]=useState(''),[checking,setChecking]=useState(true);
 const finished=useRef(false);
 const refresh=useCallback(async(signal)=>{
  if(!orderId){setError('No order reference was provided.');setChecking(false);return}
  try{const value=await api(`/api/orders/${encodeURIComponent(orderId)}`,{signal});if(signal?.aborted)return;setOrder(value);setError('');if(value.status==='paid'){finished.current=true;onPaid(value)}}catch(e){if(!signal?.aborted)setError(e.message)}finally{if(!signal?.aborted)setChecking(false)}
 },[orderId,onPaid]);
 useEffect(()=>{const controller=new AbortController();let attempts=0;finished.current=false;refresh(controller.signal);const timer=setInterval(()=>{if(!finished.current&&++attempts<=10)refresh(controller.signal);else clearInterval(timer)},3000);return()=>{controller.abort();clearInterval(timer)}},[refresh]);
 const paid=order?.status==='paid';
 return <section className="account-panel"><p className="eyebrow">STRIPE TEST CHECKOUT</p><h1>{paid?'Test payment confirmed':cancelled?'Checkout cancelled':'Checking your payment'}</h1>{error&&<p className="form-error" role="alert">{error}</p>}<p>{paid?'Your test order is saved. No real payment was taken. Appointment times are arranged separately.':cancelled?'Your bag is saved. You can return to it whenever you’re ready.':checking?'Please wait while we check your order.':'We’re waiting for Stripe to confirm your test payment. Your order will update when confirmation arrives.'}</p>{order&&<><p><strong>{money(order.amount/100)}</strong> · {order.items.map(item=>`${item.name} × ${item.quantity}`).join(', ')}</p><small>Order reference: {order.id}</small></>}<div className="account-actions"><button onClick={()=>go(paid?'/account':'/cart')}>{paid?'View my orders':'Return to bag'}</button>{!paid&&<button className="text-button" onClick={()=>refresh()}>Refresh payment status</button>}</div></section>;
}

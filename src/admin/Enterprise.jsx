import React, {useEffect, useState} from 'react';
import {api, setToken} from '../lib/api';

const sections = ['dashboard', 'products', 'categories', 'orders', 'support', 'audit', 'settings'];
const title = value => value[0].toUpperCase() + value.slice(1);
const blankProduct = {name:'', price:0, category_id:'', image:'/product.svg', description:'', stock:0, published:false};

export default function Enterprise({path, link}) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function login(event) {
    event.preventDefault(); setBusy(true); setError('');
    const data = new FormData(event.currentTarget);
    try {
      const result = await api('/auth/login', {method:'POST', body:{email:data.get('email'), password:data.get('password')}});
      setToken(result.access_token);
      setUser(await api('/auth/me'));
    } catch (e) { setToken(null); setError(e.message); }
    finally { setBusy(false); }
  }
  async function logout() {
    try { await api('/auth/logout', {method:'POST'}); }
    catch (e) { setError(e.message); }
    finally { setToken(null); setUser(null); }
  }
  if (!user) return <section className="enterprise"><p className="eyebrow">MOYA GLOW ACCOUNT</p><h1>Welcome back</h1><p>Sign in to your account or staff workspace.</p><form className="panel form" onSubmit={login}><label>Email<input required type="email" name="email" autoComplete="username"/></label><label>Password<input required type="password" name="password" maxLength="128" autoComplete="current-password"/></label><button disabled={busy}>{busy?'Signing in…':'Sign in'}</button><p role="alert">{error}</p></form><p>Accounts are currently issued by the Moya Glow team.</p><a href="/shop" onClick={link('/shop')}>Return to shop →</a></section>;
  const allowed = sections.filter(s => user.permissions.includes(s) || s === 'support');
  const requested = path.split('/')[2];
  const section = requested || (path.startsWith('/admin') ? allowed[0] : 'support');
  return <section className="enterprise"><div className="section-title"><div><p className="eyebrow">MOYA GLOW WORKSPACE</p><h1>{path.startsWith('/admin')?'Administration':'Your account'}</h1><p>{user.email} · {user.role.replaceAll('_',' ')}</p></div><button onClick={logout}>Sign out</button></div><nav className="admin-nav" aria-label="Workspace">{allowed.map(s=><a key={s} aria-current={section===s?'page':undefined} href={`/admin/${s}`} onClick={link(`/admin/${s}`)}>{title(s)}</a>)}</nav>{error&&<p role="alert">{error}</p>}{allowed.includes(section)?<Workspace key={`${user.id}-${section}`} section={section} user={user}/>:<p role="alert">You do not have permission to view this section.</p>}</section>;
}

function Workspace({section, user}) {
  const [rows, setRows] = useState(null), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [editing, setEditing] = useState(null), [detail, setDetail] = useState(null), [categories, setCategories] = useState([]), [busy, setBusy] = useState(false);
  const endpoint = section==='support'?'/support/tickets':`/admin/${section}`;
  async function refresh() { setRows(await api(endpoint)); }
  useEffect(()=>{
    let active=true;
    api(endpoint).then(value=>{if(active)setRows(value);}).catch(e=>{if(active)setError(e.message);});
    if(section==='products') api('/admin/categories').then(value=>{if(active)setCategories(value);}).catch(e=>{if(active)setError(e.message);});
    return ()=>{active=false;};
  },[endpoint,section]);
  async function action(task) {
    setBusy(true); setError(''); setNotice('');
    try { await task(); await refresh(); setNotice('Saved successfully.'); }
    catch(e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function show(id) { setError(''); try { setDetail(await api(`${endpoint}/${id}`)); } catch(e){setError(e.message);} }
  function save(event) {
    event.preventDefault();
    action(async()=>{const {id, ...body}=editing;await api(`${endpoint}${id?`/${id}`:''}`,{method:id?'PUT':'POST',body});setEditing(null);});
  }
  const field = (key, value) => setEditing(old=>({...old,[key]:value}));
  return <div className="panel"><h2>{title(section)}</h2><p role="alert">{error}</p><p role="status">{notice}</p>{rows===null?<p>{error?'Could not load this section.':'Loading…'}</p>:<>
    {section==='dashboard'&&<div className="metrics">{Object.entries(rows).filter(([k])=>k!=='payments_enabled').map(([key,value])=><article key={key}><h3>{title(key.replaceAll('_',' '))}</h3><strong>{value}</strong></article>)}<p>Orders and payments remain disabled in this prototype.</p></div>}
    {(section==='products'||section==='categories')&&<><button onClick={()=>setEditing(section==='products'?{...blankProduct,category_id:categories[0]?.id||''}:{name:''})}>New {section==='products'?'product':'category'}</button>{editing&&<form className="form" onSubmit={save}><h3>{editing.id?'Edit':'Create'} {section==='products'?'product':'category'}</h3><label>Name<input required maxLength={section==='products'?150:100} value={editing.name} onChange={e=>field('name',e.target.value)}/></label>{section==='products'&&<><label>Price (ZAR)<input type="number" min="0" max="1000000" step="0.01" required value={editing.price} onChange={e=>field('price',Number(e.target.value))}/></label><label>Product category<select required value={editing.category_id} onChange={e=>field('category_id',e.target.value)}><option value="">Choose category</option>{categories.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Stock<input type="number" min="0" max="1000000" step="1" required value={editing.stock} onChange={e=>field('stock',Number(e.target.value))}/></label><label>Description<textarea maxLength="5000" value={editing.description} onChange={e=>field('description',e.target.value)}/></label><label>Image URL<input value={editing.image} onChange={e=>field('image',e.target.value)}/></label><label className="check"><input type="checkbox" checked={!!editing.published} onChange={e=>field('published',e.target.checked)}/>Published</label></>}<div className="actions"><button disabled={busy}>Save</button><button type="button" onClick={()=>setEditing(null)}>Cancel</button></div></form>}<div className="table-wrap"><table><thead><tr><th>Name</th>{section==='products'&&<><th>Price</th><th>Stock</th><th>Published</th></>}<th>Actions</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td>{row.name}</td>{section==='products'&&<><td>{row.price}</td><td>{row.stock}</td><td>{row.published?'Yes':'No'}</td></>}<td className="actions"><button onClick={()=>setEditing(section==='products'?Object.fromEntries(['id',...Object.keys(blankProduct)].map(k=>[k,row[k]])):row)}>Edit</button><button disabled={busy} onClick={()=>{if(window.confirm(`Delete ${row.name}?`))action(()=>api(`${endpoint}/${row.id}`,{method:'DELETE'}));}}>Delete</button></td></tr>)}</tbody></table></div>{!rows.length&&<p>No records yet.</p>}</>}
    {section==='orders'&&<><p>Up to 200 most recent orders. Checkout remains disabled.</p><div className="record-list">{rows.map(row=><button key={row.id} onClick={()=>show(row.id)}>{row.id} · {row.status} · ZAR {row.total}</button>)}</div>{!rows.length&&<p>No orders yet.</p>}{detail&&<article><h3>Order {detail.id}</h3><p>Status: {detail.status} · ZAR {detail.total}</p>{detail.items.map(item=><p key={item.id}>{item.name} × {item.quantity} · ZAR {item.unit_price}</p>)}<p>Payment references: {detail.payments.length}</p><label>Next status<select aria-label="Next status" value="" disabled={busy} onChange={e=>action(async()=>{await api(`${endpoint}/${detail.id}/status`,{method:'PATCH',body:{status:e.target.value}});await show(detail.id);})}><option value="">Choose transition</option>{({pending:['processing','cancelled'],processing:['shipped','cancelled'],shipped:['completed'],completed:[],cancelled:[]}[detail.status]||[]).map(s=><option key={s}>{s}</option>)}</select></label></article>}</>}
    {section==='support'&&<><form className="form" onSubmit={e=>{e.preventDefault();const form=e.currentTarget;const data=new FormData(form);action(async()=>{await api(endpoint,{method:'POST',body:{subject:data.get('subject'),message:data.get('message')}});form.reset();});}}><h3>New support ticket</h3><label>Subject<input required name="subject" maxLength="200"/></label><label>Message<textarea required name="message" maxLength="5000"/></label><button disabled={busy}>Create ticket</button></form><div className="record-list">{rows.map(row=><button key={row.id} onClick={()=>show(row.id)}>{row.subject} · {row.status}</button>)}</div>{!rows.length&&<p>No tickets yet.</p>}{detail&&<article><h3>{detail.subject}</h3><p>Status: {detail.status}</p>{detail.messages.map(message=><div className="message" key={message.id}><small>{message.user_id===user.id?'You':'Moya Glow conversation'} · {message.created_at}</small><p>{message.body}</p></div>)}{detail.status==='open'&&<form className="form" onSubmit={e=>{e.preventDefault();const form=e.currentTarget;const body={message:new FormData(form).get('reply')};action(async()=>{await api(`${endpoint}/${detail.id}/messages`,{method:'POST',body});form.reset();await show(detail.id);});}}><label>Reply<textarea name="reply" required maxLength="5000"/></label><button disabled={busy}>Send reply</button></form>}{user.permissions.includes('support')&&<button disabled={busy} onClick={()=>action(async()=>{await api(`${endpoint}/${detail.id}/status`,{method:'PATCH',body:{status:detail.status==='open'?'closed':'open'}});await show(detail.id);})}>{detail.status==='open'?'Close ticket':'Reopen ticket'}</button>}</article>}</>}
    {section==='audit'&&<><p>Latest 200 events. Audit records are read only.</p><div className="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Resource</th><th>Request reference</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td>{row.created_at}</td><td>{row.actor_id}</td><td>{row.action}</td><td>{row.resource} / {row.resource_id}</td><td>{row.request_id}</td></tr>)}</tbody></table></div></>}
    {section==='settings'&&<><p>Maintenance is {rows.maintenance?'enabled':'disabled'}. Public catalogue requests pause while staff can still sign in and restore service.</p><button disabled={busy} onClick={()=>action(()=>api(endpoint,{method:'PUT',body:{maintenance:!rows.maintenance}}))}>{rows.maintenance?'Disable':'Enable'} maintenance</button></>}
  </>}</div>;
}

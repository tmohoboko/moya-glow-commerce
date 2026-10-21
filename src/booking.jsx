import React, {useCallback, useEffect, useRef, useState} from 'react';
import {api} from './api';
import {TreatmentImage} from './treatment-image';
import {CalendarNavigator,CalendarSchedule,addDays,todayInSalon,dayLabel,timeLabel} from './calendar';
import {products, money, servicePrice} from './products';

export const salonDay = (value = new Date()) => new Intl.DateTimeFormat('en-CA', {timeZone:'Africa/Johannesburg', year:'numeric', month:'2-digit', day:'2-digit'}).format(value);
export const salonTime = value => new Date(value * 1000).toLocaleString('en-ZA', {timeZone:'Africa/Johannesburg', dateStyle:'medium', timeStyle:'short'});
const clock = value => new Date(value * 1000).toLocaleTimeString('en-ZA', {timeZone:'Africa/Johannesburg', hour:'2-digit', minute:'2-digit', hour12:false});
const labels = {requested:'Awaiting quotation', issued:'Ready to review', accepted:'Quotation accepted', declined:'Declined', confirmed:'Confirmed', cancelled:'Cancelled', completed:'Completed', no_show:'Did not attend', unpaid:'Payment due', pending:'Awaiting payment', paid:'Test payment received', refund_required:'Refund review required', expired:'Payment session expired', not_due:'No payment due', failed:'Payment failed'};

function useLoad(path) {
  const [value, setValue] = useState(null), [error, setError] = useState(''), [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion(n => n + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setError(''); setValue(null);
    if (path) api(path, {signal:controller.signal}).then(setValue).catch(e => {if (!controller.signal.aborted) setError(e.message)});
    return () => controller.abort();
  }, [path, version]);
  return {value, error, reload};
}

export function BookingRequest({session, go, serviceId}) {
  const service = products.find(p => p.id === serviceId);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const attempt = useRef(null);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    const fields = new FormData(event.currentTarget);
    const details = {service_id:service.id, contact_name:fields.get('name'), phone:fields.get('phone'), notes:fields.get('notes')};
    const fingerprint = JSON.stringify(details);
    if (attempt.current?.fingerprint !== fingerprint) attempt.current = {fingerprint, key:crypto.randomUUID()};
    try {
      await api('/api/quotes', {method:'POST', body:JSON.stringify({...details, request_key:attempt.current.key})});
      go('/appointments');
    } catch(e) {setError(e.message); if(e.status === 401) session.setUser(null)} finally {setBusy(false)}
  }
  if (!service) return <section className="account-panel"><p className="eyebrow">APPOINTMENTS</p><h1>Choose your treatment</h1><p>Browse our services, then request a quotation. We confirm the treatment, price and time needed before you book.</p><button onClick={() => go('/services')}>View services</button></section>;
  return <section className="booking-layout"><div><p className="eyebrow">YOUR NEXT MOMENT OF CARE</p><h1>Request an appointment</h1><div className="booking-service"><TreatmentImage src={service.image} alt={service.name}/><div><h2>{service.name}</h2><p>{service.category}</p><strong>{servicePrice(service)}</strong><p className="muted">Published service price. Your quotation confirms the final total and duration.</p></div></div><ol className="booking-steps"><li>Tell us what you need</li><li>Review and accept your quotation</li><li>Choose a time and receive your invoice</li></ol></div><div className="booking-card"><h2>Tell us about your visit</h2>{error && <p role="alert" className="form-error">{error}</p>}{session.user ? <form className="account-form" onSubmit={submit}><label>Your name<input name="name" required minLength={2} maxLength={100} autoComplete="name"/></label><label>Contact number<input name="phone" type="tel" required minLength={7} maxLength={40} autoComplete="tel"/></label><label>Treatment details<textarea name="notes" maxLength={2000} rows={5} placeholder="For nails: existing product to remove, desired length, design and number of nails. Mention any additional treatments you want quoted."/></label><p className="muted">This sends a request. Your time is reserved after you accept a quotation and confirm a slot.</p><button disabled={busy}>{busy ? 'Sending…' : 'Request quotation'}</button></form> : <><p>Log in or create an account to save your request and follow your appointment.</p><button disabled={session.status === 'checking' || session.status === 'unavailable'} onClick={() => go(`/account?next=book&service=${encodeURIComponent(service.id)}`)}>Log in to request a quotation</button>{session.status === 'unavailable' && <><p role="alert">{session.message}</p><button className="text-button" onClick={session.refresh}>Retry connection</button></>}</>}</div></section>;
}

function SlotPicker({quote, booking, onDone}) {
  const [day, setDay] = useState(salonDay()), [view,setView] = useState('day'), [selected, setSelected] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const {value, error:loadError, reload} = useLoad(`/api/availability?quote_id=${quote.id}&day=${day}&view=${view}`);
  const changeDay = value => {setDay(value); setSelected(''); setError('')};
  const changeView = value => {setView(value); setSelected(''); setError('')};
  const availabilityCurrent = value?.day === day && value?.view === view;
  const selectionValid = Boolean(selected) && availabilityCurrent && value.days.some(date => date.slots.includes(Number(selected)));
  const refreshTimes = () => {setSelected(''); setError(''); reload()};
  async function reserve(event) {
    event.preventDefault();
    if(!selectionValid || busy) return;
    setBusy(true); setError('');
    try {
      await api(booking ? `/api/bookings/${booking.id}/reschedule` : '/api/bookings', {method:'POST', body:JSON.stringify(booking ? {starts_at:Number(selected)} : {quote_id:quote.id, starts_at:Number(selected), revision:quote.revision})});
      onDone();
    } catch(e) {setError(e.message); setSelected(''); reload()} finally {setBusy(false)}
  }
  return <form className="slot-picker" onSubmit={reserve} aria-label={booking?'Reschedule appointment form':'Appointment booking form'}><h3>{booking ? 'Choose a new time' : 'Choose your appointment'}</h3><div className="booking-form-summary"><strong>{quote.service_name}</strong><span>{money(quote.amount/100)} · {quote.duration} minutes</span><small>{quote.buffer} minutes reserved after treatment · South African time</small></div><CalendarNavigator day={day} view={view} onDay={changeDay} onView={changeView} min={salonDay()} max={addDays(salonDay(),90)} label="Appointment date"/><div className="available-time-control"><label>Available time<select aria-label="Available time" name="starts_at" required value={selectionValid ? selected : ''} disabled={busy||!availabilityCurrent||!value.days.some(date=>date.slots.length)} onChange={event=>{setSelected(event.target.value);setError('')}} aria-describedby={`slot-help-${quote.id}`}><option value="">Choose an available time</option>{availabilityCurrent && value.days.filter(date=>date.slots.length).map(date=><optgroup key={date.day} label={dayLabel(date.day)}>{date.slots.map(start=><option key={start} value={String(start)}>{timeLabel(start)} SAST · {dayLabel(date.day)}</option>)}</optgroup>)}</select></label><button type="button" className="text-button" disabled={busy} onClick={refreshTimes}>Refresh available times</button></div><p className="muted" id={`slot-help-${quote.id}`}>Only times that fit your treatment and salon buffer can be selected. Occupied times are unavailable.</p>{loadError && <p role="alert" className="form-error">{loadError}</p>}{!value && !loadError && <p role="status">Checking available times…</p>}{value && <div className={`booking-slot-days booking-slot-days--${view}`} role="group" aria-label="Available appointment times">{value.days.map(date=><section className="booking-slot-day" key={date.day} data-slot-day={date.day}><h4>{dayLabel(date.day)}</h4>{date.closed ? <p className="muted">Closed / outside booking dates</p> : date.slots.length+date.unavailable.length ? <div className="slot-grid">{[...date.slots,...date.unavailable].sort((a,b)=>a-b).map(start=><button type="button" key={start} disabled={!date.slots.includes(start)||busy} aria-pressed={Number(selected)===start} onClick={()=>setSelected(String(start))} aria-label={`${timeLabel(start)}${date.slots.includes(start)?'':' unavailable'}`}>{timeLabel(start)}{!date.slots.includes(start)&&<small>Unavailable</small>}</button>)}</div> : <p className="muted">No times fit this treatment.</p>}</section>)}</div>}{value && !value.days.some(date=>date.slots.length>0) && <p>No available times on this date. Try another date or contact the salon.</p>}<div className="booking-confirmation"><p aria-live="polite">{selectionValid ? `Selected: ${salonTime(Number(selected))} SAST · ${quote.service_name}` : 'Select an available time to confirm your appointment.'}</p><p className="muted">Your time is reserved when the booking is saved. We recheck availability on submission.</p>{error && <p role="alert" className="form-error">{error}</p>}<button type="submit" disabled={!selectionValid||busy}>{busy ? 'Saving…' : booking ? 'Confirm new time' : 'Confirm appointment'}</button></div></form>;
}

export function CustomerCalendar({session,go}) {
  const [day,setDay]=useState(salonDay()),[view,setView]=useState('week');
  const {value,error}=useLoad(session.user?'/api/bookings':null);
  return <section className="customer-calendar"><p className="eyebrow">TIME FOR YOURSELF</p><h1>Appointment calendar</h1><p>View your appointments by day or week. All times are South African time.</p><CalendarNavigator day={day} view={view} onDay={setDay} onView={setView}/>{error&&<p role="alert" className="form-error">{error}</p>}{session.user?<><CalendarSchedule day={day} view={view} bookings={value||[]} onDay={value=>{setDay(value);setView('day')}} onInvoice={id=>go(`/invoice/${id}`)}/><button onClick={()=>go('/appointments')}>Review quotations & book a time</button></>:<div className="booking-card"><p>Choose a treatment and accept your quotation to see available appointment slots.</p><div className="account-actions"><button onClick={()=>go('/services')}>Choose a treatment</button><button className="text-button" onClick={()=>go('/account?next=appointments')}>Log in to view my appointments</button></div></div>}</section>;
}

function QuoteCard({quote, reload}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function act(action) {
    setBusy(true); setError('');
    try {await api(`/api/quotes/${quote.id}/${action}`, {method:'POST', ...(action === 'accept' ? {body:JSON.stringify({revision:quote.revision})} : {})}); reload()} catch(e) {setError(e.message)} finally {setBusy(false)}
  }
  return <article className="booking-card" data-quote-id={quote.id}><div className="card-heading"><h3>{quote.service_name}</h3><span className="order-status">{quote.expired && quote.status !== 'requested' ? 'Quotation expired' : labels[quote.status]}</span></div><small className="reference">{quote.number}</small><p>{quote.notes || 'Treatment details to be confirmed with the salon.'}</p>{quote.amount !== null && <><p><strong>{money(quote.amount / 100)}</strong> · {quote.duration} minutes</p><p className="terms">{quote.terms}</p><small>Valid until {salonTime(quote.expires_at)}</small></>}{error && <p role="alert" className="form-error">{error}</p>}{quote.status === 'issued' && !quote.expired && <div className="account-actions"><button disabled={busy} onClick={() => act('accept')}>Accept quotation</button><button disabled={busy} className="text-button" onClick={() => act('decline')}>Decline quotation</button></div>}{quote.status === 'requested' && <p className="muted">The salon will confirm your price and treatment duration. Check this page for your quotation.</p>}{quote.status === 'accepted' && !quote.expired && <SlotPicker quote={quote} onDone={reload}/>}</article>;
}

export function AppointmentCard({booking, reload, go, staff = false}) {
  const [moving, setMoving] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function action(value) {
    setBusy(true); setError('');
    try {await api(staff ? `/api/staff/bookings/${booking.id}/${value}` : `/api/bookings/${booking.id}/cancel`, {method:'POST'}); reload()} catch(e) {setError(e.message)} finally {setBusy(false)}
  }
  return <article className="booking-card" data-booking-id={booking.id}><div className="card-heading"><h3>{booking.quote.service_name}</h3><span className="order-status">{labels[booking.status]}</span></div><p><strong>{salonTime(booking.starts_at)}</strong> – {clock(booking.ends_at)} SAST</p>{staff && <p>{booking.quote.contact_name} · {booking.quote.phone} · {booking.quote.source === 'walk_in' ? 'Walk-in' : 'Online'}</p>}<p>{money(booking.invoice.amount / 100)} · {labels[booking.invoice.payment_status]}</p><small className="reference">{booking.invoice.number}</small>{error && <p role="alert" className="form-error">{error}</p>}<div className="account-actions">{<><button className="text-button" onClick={() => go(`/invoice/${booking.invoice.id}`)}>View invoice{booking.invoice.receipt_number ? ' & receipt' : ''}</button>{!staff && <a className="text-button" href={`/api/bookings/${booking.id}/calendar.ics`}>Download calendar event</a>}</>}{booking.status === 'confirmed' && <>{!staff && booking.starts_at > Date.now()/1000 && <button disabled={busy} className="text-button" onClick={() => setMoving(!moving)}>{moving ? 'Keep current time' : 'Reschedule'}</button>}{(staff || booking.starts_at > Date.now()/1000) && <button disabled={busy} className="text-button" onClick={() => action(staff ? 'cancelled' : 'cancel')}>Cancel appointment</button>}{staff && booking.starts_at <= Date.now()/1000 && <><button disabled={busy} onClick={() => action('completed')}>Mark completed</button><button disabled={busy} className="text-button" onClick={() => action('no_show')}>Mark no-show</button></>}</>}</div>{moving && <SlotPicker quote={booking.quote} booking={booking} onDone={() => {setMoving(false); reload()}}/>}</article>;
}

export function CustomerBookings({session, go, embedded = false}) {
  const [revision, setRevision] = useState(0);
  const quotes = useLoad(session.user ? `/api/quotes?refresh=${revision}` : null);
  const bookings = useLoad(session.user ? `/api/bookings?refresh=${revision}` : null);
  const reload = () => setRevision(n => n + 1);
  const booked = new Set((bookings.value || []).map(row => row.quote_id));
  const activeQuotes = (quotes.value || []).filter(row => !booked.has(row.id));
  return <section className={embedded ? 'booking-history' : 'account-panel'}>{!embedded && <><p className="eyebrow">YOUR L BEAUTY VISITS</p><h1>My appointments</h1></>}{!session.user ? <><p>Log in to review quotations, choose appointment times and view invoices.</p><button onClick={() => go('/account?next=appointments')}>Log in</button></> : <><div className="account-actions"><button onClick={() => go('/services')}>Request another treatment</button><button className="text-button" onClick={reload}>Refresh appointments</button></div>{(quotes.error || bookings.error) && <p role="alert" className="form-error">{quotes.error || bookings.error}</p>}{(!quotes.value || !bookings.value) && !quotes.error && !bookings.error && <p role="status">Loading appointments…</p>}{bookings.value && <><h2>Appointments</h2>{bookings.value.length ? bookings.value.map(booking => <AppointmentCard key={booking.id} booking={booking} reload={reload} go={go}/>) : <p>No appointments yet.</p>}</>}{quotes.value && <><h2>Quotation requests</h2>{activeQuotes.length ? activeQuotes.map(quote => <QuoteCard key={`${quote.id}-${quote.revision}-${quote.status}`} quote={quote} reload={reload}/>) : <p>No open quotations.</p>}</>}</>}</section>;
}

export function Invoice({invoiceId, go}) {
  const {value, error, reload} = useLoad(`/api/invoices/${encodeURIComponent(invoiceId)}`);
  const [busy, setBusy] = useState(false), [paymentError, setPaymentError] = useState('');
  async function pay() {
    setBusy(true); setPaymentError('');
    try {
      const result = await api(`/api/invoices/${value.id}/checkout`, {method:'POST'});
      const url = new URL(result.url);
      if(url.protocol !== 'https:' || url.hostname !== 'checkout.stripe.com') throw new Error('Unable to open test payment.');
      location.assign(url.href);
    } catch(e) {setPaymentError(e.message)} finally {setBusy(false)}
  }
  return <section className="account-panel invoice"><p className="eyebrow">L BEAUTY · INVOICE</p><h1>Your appointment invoice</h1>{error && <p role="alert" className="form-error">{error}</p>}{!value && !error && <p role="status">Loading invoice…</p>}{value && <><small className="reference">{value.number}</small><p>For {value.booking.quote.contact_name}</p><h2>{value.booking.quote.service_name}</h2><p>{salonTime(value.booking.starts_at)} SAST · {value.booking.quote.duration} minutes</p><p className="terms">{value.booking.quote.terms}</p><div className="invoice-total"><span>Total</span><strong>{money(value.amount/100)}</strong></div><p>Appointment: {labels[value.booking.status]} · Invoice: {value.status === 'void' ? 'Voided' : 'Issued'}</p><p>Payment: <strong>{labels[value.payment_status]}</strong></p>{value.receipt_number && <div className="receipt"><h2>Sandbox payment receipt</h2><p>{money(value.amount/100)} received in test mode. No real money moved.</p><small className="reference">{value.receipt_number}</small></div>}{value.payment_status === 'refund_required' && <p className="form-error">This appointment was cancelled after a test payment. The salon must review the refund; cancellation does not automatically refund a payment.</p>}{paymentError && <p role="alert" className="form-error">{paymentError}</p>}<div className="account-actions">{value.can_pay && value.status === 'issued' && value.amount > 0 && ['unpaid','pending'].includes(value.payment_status) && <button disabled={busy} onClick={pay}>{busy ? 'Opening…' : 'Pay invoice in Stripe test mode'}</button>}<button className="text-button" onClick={() => window.print()}>Print invoice{value.receipt_number ? ' & receipt' : ''}</button><button className="text-button" onClick={reload}>Refresh payment status</button><button className="text-button" onClick={() => go('/appointments')}>Back to appointments</button></div><p className="muted">Sandbox invoice for workflow review. No real payment taken.</p></>}</section>;
}

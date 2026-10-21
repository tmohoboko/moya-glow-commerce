import React from 'react';

export const todayInSalon = () => new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Johannesburg',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
export function addDays(day,amount) {const value=new Date(day+'T12:00:00Z');value.setUTCDate(value.getUTCDate()+amount);return value.toISOString().slice(0,10)}
export function weekDays(day) {const weekday=new Date(day+'T12:00:00Z').getUTCDay();const monday=addDays(day,-((weekday+6)%7));return Array.from({length:7},(_,i)=>addDays(monday,i))}
export const dayLabel = day => new Date(day+'T12:00:00Z').toLocaleDateString('en-ZA',{timeZone:'Africa/Johannesburg',weekday:'short',day:'numeric',month:'short'});
export const timeLabel = value => new Date(value*1000).toLocaleTimeString('en-ZA',{timeZone:'Africa/Johannesburg',hour:'2-digit',minute:'2-digit',hour12:false});
export const dateOf = value => new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Johannesburg',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value*1000));

export function CalendarNavigator({day,view,onDay,onView,min,max,label='Calendar date'}) {
  const change = value => {if(value && (!min||value>=min) && (!max||value<=max)) onDay(value)};
  const dates=view==='week'?weekDays(day):[day],step=view==='week'?7:1;
  return <div className="calendar-navigation"><div className="calendar-controls"><div className="view-switch" role="group" aria-label="Calendar view"><button type="button" aria-pressed={view==='day'} onClick={()=>onView('day')}>Day</button><button type="button" aria-pressed={view==='week'} onClick={()=>onView('week')}>Week</button></div><div className="calendar-paging"><button type="button" aria-label={`Previous ${view}`} disabled={Boolean(min&&addDays(day,-step)<min)} onClick={()=>change(addDays(day,-step))}>←</button><button type="button" onClick={()=>change(todayInSalon())}>Today</button><button type="button" aria-label={`Next ${view}`} disabled={Boolean(max&&addDays(day,step)>max)} onClick={()=>change(addDays(day,step))}>→</button></div><label>{label}<input type="date" value={day} min={min} max={max} onChange={e=>change(e.target.value)}/></label></div><div className={`calendar-dates calendar-dates--${view}`}  role="group" aria-label="Calendar dates">{dates.map(date=><button type="button" key={date} aria-label={date} aria-pressed={date===day} disabled={Boolean((min&&date<min)||(max&&date>max))} onClick={()=>change(date)}><span>{dayLabel(date).split(',')[0]}</span><strong>{Number(date.slice(-2))}</strong><small>{date}</small></button>)}</div></div>;
}

export function CalendarSchedule({day,view,bookings=[],blocks=[],onDay,onInvoice,renderDay,emptyLabel='No appointments'}) {
  const dates=view==='week'?weekDays(day):[day];
  return <div className={`calendar-schedule calendar-schedule--${view}`} role="region" aria-label={`${view==='week'?'Week':'Day'} appointment calendar`}>{dates.map(date=>{
    const appointments=bookings.filter(row=>dateOf(row.starts_at)===date);
    const blocked=blocks.filter(row=>dateOf(row.starts_at)<=date&&dateOf(row.ends_at-1)>=date);
    const entries=[...appointments.map(row=>({...row,kind:'appointment'})),...blocked.map(row=>({...row,kind:'block'}))].sort((a,b)=>a.starts_at-b.starts_at);
    return <section className="calendar-column" key={date}><button type="button" className="calendar-column-heading" onClick={()=>onDay(date)}>{dayLabel(date)}</button>{view==='day'&&renderDay?.()}{entries.length?entries.map(row=>row.kind==='appointment'?<button key={row.id} className={`calendar-event calendar-event--${row.status}`} type="button" onClick={()=>onInvoice(row.invoice.id)}><strong>{timeLabel(row.starts_at)} – {timeLabel(row.ends_at)}</strong><span>{row.quote.service_name}</span><small>{row.status.replace('_',' ')} · {row.quote.buffer} min buffer</small></button>:<div key={row.id} className="calendar-event calendar-event--block"><strong>{timeLabel(row.starts_at)} – {timeLabel(row.ends_at)}</strong><span>{row.label}</span><small>Unavailable</small></div>):view==='day'&&renderDay?null:<p className="calendar-empty">{emptyLabel}</p>}</section>;
  })}</div>;
}


export function DayTimeSlots({day,available=[],selected='',onSelect,loading=false,disabled=false}) {
  const first=Math.floor(new Date(`${day}T09:00:00+02:00`).getTime()/1000);
  const times=Array.from({length:33},(_,i)=>first+i*900);
  return <div className="day-time-slots"><p className="muted">09:00–17:00 · South African time · 15-minute intervals</p><div className="slot-grid" role="group" aria-label="Day time slots">{times.map((start,i)=>{
    const free=i<32&&available.includes(start)&&!loading&&!disabled;
    const picked=free&&Number(selected)===start;
    return <button type="button" key={start} disabled={!free} aria-pressed={picked} aria-label={`${timeLabel(start)}${free?'':' unavailable'}`} onClick={()=>onSelect(start)}>{timeLabel(start)}<small>{picked?'Selected':i===32?'Closing time':loading?'Checking…':free?'Available':'Unavailable'}</small></button>;
  })}</div></div>;
}

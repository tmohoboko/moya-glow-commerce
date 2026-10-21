# CR-005 — Day calendar time slots

The public/personal Day calendar displays a 09:00–17:00 grid in 15-minute intervals in South African time. 17:00 is the closing boundary, not a new appointment start. All 33 time labels remain visible on closed dates or while availability is being checked. Unavailable, booked, blocked, elapsed and closing-time cells are grey and disabled. A valid selected time is grey with an explicit Selected label.

A public read-only endpoint `/api/calendar/availability` returns general 15-minute capacity without names, contact information, quotation/booking IDs or notes; responses are not cached. It uses the same interval calculation as authenticated treatment availability, including occupied booking buffer time and staff blocks. The existing configured salon hours remain authoritative: an unconfigured/closed salon does not advertise invented available appointments.

Signed-in customers with accepted, unbooked quotations can book directly inside Day view. Multiple quotations require an explicit choice. Treatment-specific slots must fit the quotation duration and buffer, and reservation still uses the existing authenticated transaction and conflict checks. General availability for visitors is only a preview; a treatment quotation determines which starts fit.

The grid refreshes every 30 seconds while the page is visible, on window focus, manually, and after conflicts or a booking. An unavailable selected time clears when new availability arrives. Existing account-scoped session selection, logout clearing and server-backed confirmed bookings remain in place. The time grid is rendered inside the Day calendar column, replacing the empty appointment-only panel from the client screenshot. Week retains its seven-column appointment overview.

Validation covers public privacy/cache headers, occupied intervals plus buffer, closed days, date/view validation, 33 visible labels, disabled/grey occupied cells, closing time, manual refresh detecting a newly taken slot, mobile layout, direct Day booking, session reload and last-moment conflict recovery. No migration, staff grant or opening-hours change is required.

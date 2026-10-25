# CR-003 — treatment imagery, category grouping and day/week booking

21 October 2026 · Africa/Johannesburg

## Scope implemented

1. Group presentation into Nails, Lashes & Brows, Makeup, Hands & Feet, Massage
   and Waxing. Body/facial/intimate waxing remain identifiable subtypes within
   one Waxing filter. Original 46 IDs, names, prices and 11 source categories are
   preserved, including prior database snapshots and bookings.
2. Rank groups by distinct displayed photo sources, with Waxing explicitly last.
   This counts the displayed service gallery, not unused alternate uploads.
3. Frame lashes/brows around eyes, massage around hands/treatment areas and
   pedicure/waxing around their treatment areas. Apply one shared image component
   across cards, detail, request summary and gallery. Source pixels remain intact;
   no links from the gallery open an uncropped irrelevant portrait. Faces remain
   where they communicate makeup/facial treatment. Replace three generic room/
   equipment views with new treatment-detail photos in the same salon palette.
4. Add public/personal and staff Day/Week calendars, date navigation, Monday-based
   weeks, appointment/invoice links and blocked-time indicators.
5. Replace the slot div with a semantic submit form: accepted service, quoted
   total, duration, buffer, date, available/unavailable slots and selected-time
   confirmation. A slot selection is required; changing date/view clears it.
   Week mode obtains seven days in one authenticated API request. Backend reads
   busy intervals once per range, reveals no customer details and rechecks
   capacity transactionally when submitting. Existing quotation/invoice flow stays.
6. Verify catalogue contract, grouping/order/images, calendar date boundaries,
   permissions, mobile layouts and the complete booking journey; deploy the
   exact checked commit to the existing project.

## Display counts and order

| Order | Group | Distinct pictures | Services |
| --- | --- | ---: | ---: |
| 1 | Nails | 12 | 10 |
| 2 | Lashes & Brows | 9 | 9 |
| 3 | Makeup | 7 | 4 |
| 4 | Hands & Feet | 6 | 6 |
| 5 | Massage | 4 | 4 |
| 6 | Waxing | 13 | 13 |

Waxing is last by the user's explicit instruction, overriding its photo count.
The gallery contains 50 distinct displayed photographs. One hand/nail image
belongs to two groups, so the per-group counts sum to 51. The 46 service image
paths remain unique. Filters and gallery use the same grouping functions.

## Image preparation

Existing images: non-destructive CSS framing in `src/treatment-image.jsx`; shared
framing prevents a close-up card reopening as a full portrait in its detail view.
Focus coordinates are normalized; all cropped source photographs are square
1254px. Images maintain their proportions, and hover/reduced-motion behavior is
retained. New full-resolution square images are stored as web JPEGs, with no
semantic crop or repaint performed during format conversion.

Built-in image generation was used for three new photographs:

- `public/catalogue/services/focus-massage-compress.jpg` — hands preparing a warm
  compress, oil and towels, replacing an empty treatment-room image.
- `public/catalogue/services/focus-body-wax.jpg` — amber wax, gloved hand and
  spatula, replacing a generic chest-wax equipment view.
- `public/catalogue/services/focus-intimate-wax.jpg` — green hard wax, hygienic
  tools and treatment preparation, replacing the empty intimate-wax trolley.

Successful prompt set: square photorealistic professional South African salon
catalogue detail; natural warm light, sage/cream palette, realistic textures,
no faces, text, watermark or collage. Individual subjects were (1) therapist
hands preparing a linen compress beside oil, (2) gloved hand lifting amber wax
with a spatula over a warmer, (3) gloved hands with green hard wax and hygienic
intimate-waxing preparation supplies. Anatomical image attempts were blocked;
safer preparation/tool details were used instead. Original images are preserved.

## Access and deployment boundary

No schema migration, account changes, staff grants, business-hours changes or
payment configuration changes are needed for this patch. Staff access remains
subject to the previously reported explicit-approval requirement. The patch does
not bypass it. Public calendar navigation works without disclosing appointment
records; available slots require an authenticated, accepted quotation. The actual
salon calendar remains closed until an authorised operator configures its hours.

Google Calendar export remains a snapshot. This change does not claim live sync.

## QA traceability

- PATCH-001: six groups, photo-count ordering, unified Waxing, contiguous cards.
- PATCH-002: treatment framing survives card → detail → request navigation.
- PATCH-003: public Day/Week views, seven-day navigation and mobile width.
- PATCH-004: all nine lash/brow photos use close framing and load correctly.
- BOOKING-001: real local customer/staff journey now selects a week-view slot in
  a submit form, then verifies invoice, reschedule and cancellation.
- API: seven-day availability, Monday boundaries, privacy, busy/buffer slots,
  staff authorisation and invalid view validation, alongside retained concurrency,
  invoice/payment and persistence checks.

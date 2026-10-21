# CR-004 — client photo corrections and session calendar

## Client instructions implemented

- Read the WhatsApp screenshot as mapping instructions only. Screenshots are not published. Imported the eleven original JPEG files from the 21 October ZIP, retaining original pixels and before/after composites. Presentation corrects rotation and focuses individual lash/brow portraits; composites remain fully visible.
- Moved the square French-tip client photo to French (Acrylic), R280. French (Gel), R250, now has a generated short natural-nail gel example. Acrylic Overlay, R150, belongs to Natural Nails and uses a new natural-length overlay photo. All 46 IDs and prices remain unchanged; existing quotations retain their stored snapshots.
- Moved the silver finish photo out of Acrylic Overlay into a new Cat eye photo collection under Nails. No unapproved service price was invented for this finish; request details can be quoted by the salon. Existing cat-eye lash add-on remains a separate treatment.
- All 13 waxing service cards show equipment/preparation supplies, with eleven new distinct equipment photographs plus two existing equipment photographs. No bare treatment-area photographs remain mapped to waxing.
- Gallery: 63 distinct sources. Group order by displayed photo count is Lashes & Brows (20), Nails (14), Makeup (7), Hands & Feet (6), Massage (4), Waxing (13, explicitly last). One image belongs to both Nails and Hands & Feet, so group counts sum to 64. Before & after and Client results collections expose supplied originals.

## Calendar and persistence behavior

- Day navigation renders one date and one schedule column. Week navigation renders seven Monday-based dates and columns, including for signed-out visitors; private appointment details still require login.
- Date/view are kept in browser session storage scoped to the current account. Slot drafts are scoped to account, quotation, revision and booking/reschedule identity; no credentials or client notes are stored.
- Selected slot is grey with an explicit Selected label and remains selected after a reload/navigation in the same browser session. This draft is not a reservation. A fresh availability response must still validate it before confirmation; an unavailable restored selection clears. Date/view change, refresh or 409 conflict clears the selection. Logout clears calendar and slot draft storage.
- Confirmed bookings persist on the server and appear grey in the customer calendar. Occupied times remain disabled and grey in the slot picker; backend transaction checks still prevent competing bookings.

## Image generation

Built-in image generation created thirteen 1254×1254 originals. Project JPEGs are in `public/catalogue/services/refresh-*.jpg`; only format conversion/compression was applied. Each prompt asked for warm cream/sage professional salon photography without text, collage or branding. Equipment prompts required no people, faces or skin; manicure prompts show only hands with natural-length nails. The per-image subject prompt is recorded in CR-004_IMAGE_PROMPTS.json. The eleven supplied JPEGs are in `public/catalogue/client-oct21/` and their source-byte hashes are in qa/client-oct21-manifest.json.

No migration, staff grant, business-hour change or live payment is part of this patch. Genuine salon setup is still required before Production offers slots.

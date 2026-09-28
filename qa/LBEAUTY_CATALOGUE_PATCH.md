# L Beauty catalogue patch

Date: 2026-09-28

Source folder: `/home/tmdev012/Reception/LBeautyCatalogue`.
Catalogue data: `src/products.js`. Asset path: `public/catalogue/lbeauty/` (served at `/catalogue/lbeauty/`).

## Implementation

Replaced the existing static demo array with 46 services in 11 categories. The supplied service/price list in the task is authoritative; source JPGs 1–8 were copied unchanged as cover, massage-hand-foot, wax, lash-brow, nails, makeup, contact and closing-cover. Category artwork is reused for individual services. Cover artwork appears on the homepage; contact details appear in the footer. Removed the existing alternating hue filter to preserve source artwork colors. Existing layout and cart storage remain in place.

Categories: Massage (4); Hand and Foot Treatments (4); Body Wax (6); Intimate Wax (4); Facial Wax (3); Lash Extensions (5); Lash and Brow (4); Gel & Acrylic Nail Enhancements (6); Toes (2); Others / Nails (Per Nail) (4); Makeup Looks (4).

Products retain id, name, category, numeric price, image and description. IDs are unique and deterministic, including `nails-french-250`, `nails-french-280` and `toes-french-170`. Massage durations and per-nail pricing are included in descriptions. Existing persisted demo IDs are discarded by the existing cart validation.

Special Effects R600+ and Bridal R1000+ use numeric bases 600 and 1000. Cards, details, cart unit prices, line totals and subtotal preserve “From” when applicable. Cart totals use base prices; the cart explains that final prices may vary.

## Verification

- `npm run build`: PASS, Vite production build.
- `npm test --if-present`: PASS, all 12 existing/extended Playwright smoke tests against the production preview at `http://127.0.0.1:4173`.
- `git diff --check`: PASS.
- Reviewed all 46 service names and numeric prices against the supplied task list.
- All 11 category filters work; search and no-results handling pass.
- All 46 card images decode successfully; all eight asset URLs return JPEG responses.
- No fatal JavaScript errors observed in homepage/catalogue checks.
- Full Body add → R450; increase → R900; add Back and Neck → R1,150. Quantity decrease, refresh persistence and removal to empty bag pass.
- Both starting-price services verified on cards, details and cart, including doubled base totals and removal.
- Mobile width 375px passes overflow and cart usability assertions. Desktop screenshot visually reviewed.
- Automated evidence: `qa/smoke-results.json`, `qa/desktop-home.png`, `qa/mobile-home.png`.

## Known limitations

Static catalogue only; no booking, orders or payment processing. Service images are shared catalogue pages, not individual service photos. Contact and closing-cover artwork are available as assets; footer contact information is rendered as text. Starting prices are estimates. No deployment performed.

## Files changed

- `src/products.js`: service data and price display helper.
- `src/main.jsx`: service copy/artwork/contact and starting-price rendering.
- `src/style.css`: removed artwork hue alteration.
- `public/catalogue/lbeauty/*.jpg`: eight supplied images.
- `tests/smoke.spec.js`: catalogue assertion updates and focused artwork/starting-price checks.
- `qa/LBEAUTY_CATALOGUE_PATCH.md`: this evidence.
- `qa/smoke-results.json`, `qa/desktop-home.png`, `qa/mobile-home.png`: refreshed automated evidence.

Scope review: no enterprise merge, backend work, auth changes, new architecture or unrelated refactoring. Pre-existing untracked `.deploy-enterprise/`, `.venv/` and `backend/` are left untouched and excluded from the commit.

# L Beauty service artwork stabilization

Date: 2026-09-30. Baseline: `74ad759` (L Beauty catalogue integration).

## Identity and generation

- Products: **46**. Generated SVGs: **46**. Unique product image paths: **46**.
- Authoritative source: `src/products.js`; no second service catalogue.
- Generator: `scripts/generate-service-artwork.mjs`. Run with `node scripts/generate-service-artwork.mjs`.
- Output: `public/catalogue/services/`, served at `/catalogue/services/<existing-id-slug>.svg`.
- Shared path helper: `src/service-artwork.js`. Existing IDs distinguish repeated names, including French nail/toe services.
- Generator stops before writing if catalogue count differs from 46, slugs collide, paths mismatch, or unexpected output files exist.
- Second generation is byte-identical: no duplicate files or changed filenames. All 46 SVGs parse as XML; every referenced asset exists. No product references the old category artwork.
- Compared every product against baseline after excluding only `image`: all IDs, names, categories, descriptions, numeric prices and starting-price flags are unchanged.
- Artwork contains L BEAUTY, individual service name, category, price, and duration wherever the existing description provides it. Special Effects: FROM R 600; Bridal: FROM R 1 000.
- Artwork uses SVG text and geometry, system fonts, and no raster/remote assets, image services or new dependencies. Long names/categories wrap; Chromium checks every label's rendered bounds.

## Local verification

- `npm run build`: PASS (Vite production build).
- `npm test`: PASS, **13/13** Playwright tests against production preview at `http://127.0.0.1:4173`.
- `BASE_URL=http://127.0.0.1:5173 npm test -- --grep SMOKE-013 --reporter=list`: PASS against the Vite development server.
- Existing checks cover search/no results, all 11 categories, detail routing, quantity changes, refresh persistence, removal, mobile overflow, and starting prices.
- One added regression checks 46 products/unique image paths, Full Body vs Back and Neck, successful SVG responses, XML parsing, complete service/category/price text, text bounds, and artwork/name/price continuity into the bag for all 46 services.
- All 46 cart images decode; aggregate base subtotal matches the existing calculation. Full Body R450 + Back and Neck R250 = R700; existing quantity test confirms R1,150 after doubling Full Body.
- No fatal JavaScript errors in the exercised homepage/catalogue/cart flows.
- Visually reviewed desktop catalogue, mobile screenshot, and local cart: four Massage services have individual names/prices/durations, long names wrap, and bag thumbnails match the chosen services.
- Refreshed automated evidence: `qa/smoke-results.json`, `qa/desktop-home.png`, `qa/mobile-home.png`.

## HTTPS frontend

HTTPS verification: **BLOCKED by network/tool access; no deployment performed**. The existing CLI package bootstrap stalled on registry downloads; a direct Vercel CLI 61.1.0 `whoami` attempt reported failure fetching npm dist-tags and timed out after 30 seconds. The public production HTTPS request also timed out. Authentication status could not be established; no claim is made that production contains this patch.

`README.md` and `qa/RELEASE_ACCEPTANCE.md` document the existing project (`moya-glow-commerce`) and manual `npx vercel --prod --yes` mechanism. Automatic GitHub deployments are not connected; pushing main alone will not deploy. No push was performed.

A frontend-only copy is ready at `/tmp/moya-service-release-1dpv4uz8`, preserving the existing `vercel.json` and `.vercel/project.json` link while excluding the unrelated untracked backend/enterprise folders. Once network access is restored, the human action is:

```sh
cd /tmp/moya-service-release-1dpv4uz8
npx vercel login # only if authentication is required
npx vercel --prod --yes
cd /home/tmdev012/Reception/moya-glow-commerce
BASE_URL=https://moya-glow-commerce.vercel.app npm test -- --reporter=list
```

This uses only the existing frontend project/mechanism. No hosting architecture or deployment configuration was changed.

## Known limitations and scope

- Chromium coverage only; tiny existing cart thumbnails keep their existing dimensions. Artwork is a service identity graphic, not photography.
- Duration is shown only when available in existing catalogue descriptions. Starting-price totals remain base estimates.
- Components, layout, typography outside SVGs, navigation, search, filters, prices, IDs, cart calculations and backend are unchanged.
- Existing untracked `.deploy-enterprise/`, `.venv/`, and `backend/` are excluded from this work and commit.
- No FastAPI hosting started. Stop after the artwork task.

## Manual QA

1. Open the catalogue.
2. Compare Full Body with Back and Neck artwork.
3. Add one to bag; confirm the same service artwork, name and price in the cart.

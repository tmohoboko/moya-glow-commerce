# Service photo refinement — 19 October 2026

User request: remove source captions, replace repeated photographs, and make image interactions livelier while preserving the existing storefront.

## Changes

- Replace shared category imagery with 24 new service-specific photographs.
- Use the existing short-nail portfolio photograph for Full Manicure and the silver finish for Acrylic Overlay, reducing near-identical portfolio views.
- Curate the visible gallery to 17 distinct supplied looks plus 33 service photographs, retaining all original uploaded files.
- Keep 46 service records, prices, categories and bag logic unchanged.
- Remove image-source captions from service cards, details and the gallery. Gallery descriptions use neutral treatment/appearance names without claiming that illustrative photographs are actual client results.
- Add gentle image zoom, card lift and a readable service-link cue on pointer hover. Keyboard focus reveals the same cue. Respect `prefers-reduced-motion` and avoid hover-only interactions on touch screens.
- Move portrait crops upward slightly so the face stays visible.

## Image production

The built-in image-generation tool supplies the 24 new photographs, in square composition and a warm candid South African salon style. Each photograph has a different service activity, angle or arrangement. Source prompts and the final service paths are retained with this change. Supplied photographs are preserved unchanged.

There are 46 distinct primary service paths; final verification must also establish 46 distinct file hashes and successful image decoding.

## Verification scope

Production build, existing functional regression, all service images retained with the correct title/price in the bag, gallery filtering, absence of removed captions, hover and keyboard interactions, reduced-motion behavior, and deployed-page visual review.

Application commit, CI result and Vercel deployment are reported with the completed release.

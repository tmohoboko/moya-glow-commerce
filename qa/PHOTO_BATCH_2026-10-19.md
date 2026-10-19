# L Beauty photo batch — 19 October 2026

## Scope and coverage

The 30-photo ZIP is preserved as 30 byte-identical JPEG assets, with original filenames recorded in `src/photo-library.js`. Fourteen nail photos serve the nail-enhancement and nail-detail galleries; sixteen portrait/preparation photos serve Makeup Looks. These cover three catalogue categories. Eight categories previously had no supplied photographs.

Nine new built-in image-generation outputs fill those eight category gaps plus the Special Effects makeup service. All generated assets are explicitly captioned “AI-generated illustration” in the catalogue, service detail and gallery. They are examples, not evidence of actual salon work.

All 46 service IDs, names, descriptions, prices, starting-price rules and categories are unchanged. Thirteen cards use supplied portfolio images (including the two previously approved makeup photos); 33 use illustrations. There are 22 distinct primary photos because category illustrations are intentionally shared. The gallery contains all 30 new supplied photos and all nine generated images.

## Assignment policy

- Keep the two previously approved makeup assignments.
- Use a white-robe makeup portrait as a representative Bridal example.
- Use visible red/pink finishes, extensions and French tips as representative nail-enhancement examples. Gel versus acrylic, fill versus new set and actual treatment provenance cannot be established from appearance; these assignments are for visual review.
- Use the geometric art, gold metallic detail, decorated nails and raised bows for Art, Chrome, Charms/Rhinestones and 3D respectively. Exact materials remain unverified.
- Keep preparation portraits and alternate views in the gallery rather than creating additional services.
- Use category illustrations for missing categories, with a pedicure-specific illustration on Full Pedicure.
- Original SVG artwork remains available as fallback; this batch intentionally replaces primary display images with photos.

## Generated prompt set

Built-in image generation was used. Shared direction: square candid smartphone salon photography, warm natural window light, cream walls, modest South African salon setting, natural dark skin texture, realistic anatomy, gentle background blur, different adult clients, no text/logos/watermarks/collages. Final files are `public/catalogue/services/illustrative-<slug>.jpg`.

| Slug | Scene |
| --- | --- |
| massage | Fully clothed adult Black woman seated in a salon chair; therapist gently massaging shoulders over an opaque cotton T-shirt. |
| hand-foot | Therapist exfoliating and massaging an adult Black woman's hand over a white manicure towel; bowl and moisturiser nearby. |
| body-wax | Gloved therapist applying a small strip of warm wax to an adult Black woman's lower leg on a towel. |
| intimate-wax | Neutral clean waxing trolley with plain wax heater, disposable wooden spatulas, towels and gloves; no people or body parts. |
| facial-wax | Gloved therapist applying a small amount of wax beside an adult Black woman's eyebrow; eye closed. |
| lash-extensions | Closed eyes with neat long lash extensions, under-eye pads and therapist's precision tweezers held safely nearby. |
| lash-brow | Portrait with black salon cape and headband, groomed natural eyebrows and subtly tinted lashes; minimal makeup. |
| toes | Feet on a clean pedicure towel, glossy pale pink toenails with white French tips. |
| special-effects | Salon portrait with tasteful sculpted gold celestial accents on one cheek and purple/gold creative eye makeup. |

## Verification

Production build: PASS. Catalogue integrity and all referenced files: PASS. Local Playwright execution is blocked before browser launch by missing Chromium; the existing GitHub Actions regression workflow validates the committed change. Inspect its run and the deployed page before recording release acceptance.

Review on `/shop#photos`; the existing category selector filters both services and photos. Clicking a gallery photo opens the original JPEG.

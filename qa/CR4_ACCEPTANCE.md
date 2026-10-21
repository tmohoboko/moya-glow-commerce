# CR-004 release acceptance

Runtime commit: `4dc80d32346f48c1b9699bbd5d690ccb12a9b008`.
Production: `dpl_9F9XuPzauvTaeGCKyDHbjU2M9aq3`, READY.
Review: https://moya-glow-commerce.vercel.app/gallery
CI: https://github.com/tmohoboko/moya-glow-commerce/actions/runs/39542215988

Delivered: 13 new generated treatment/equipment images, 11 source-byte-identical client JPEGs, Natural Nails correction for Acrylic Overlay, French gel/acrylic photo correction, Cat eye nail-finish collection, three before/after examples, 63 distinct gallery photos. All 13 waxing service cards show equipment/preparation supplies. The four WhatsApp instruction screenshots were read only and are not repository/site assets.

Day now displays one date and schedule column; Week displays seven. Live browser verified both structures and Day selection after reload. Slot draft tests verify date/time persistence on reload, grey Selected styling, selection clearing on refresh, disabled occupied slots, 409 conflict recovery and no false confirmation. The full real disposable-CI quotation → acceptance → Week time picker → booking → invoice → reschedule → cancel journey passes. Confirmed reservations are server-backed; unconfirmed selections are remembered only within the browser session and are revalidated before confirmation. Logout clears saved draft preferences.

Validation: 30 browser tests passed; SQLite 53 passed / 1 PostgreSQL-only skip; PostgreSQL 54 passed. Build, catalogue sync, secret scan and whitespace checks passed. Production 31 read-only checks passed, including 24 exact image hashes, catalogue equality, routes and readiness. Live browser reviewed equipment pictures, 3 before/after figures and the 1-image Cat eye collection. No Production booking, payment, staff grant or opening-hours change was created. Existing genuine business hours and staff setup still govern whether slots can be offered. Vercel runtime-log access remains an existing observability gap; no claim of clean runtime logs is made.

Evidence-only commit follows the deployed runtime SHA; PR #5 remains a draft and unmerged. Full implementation and prompts: docs/CR-004_CLIENT_PHOTOS_SESSION_CALENDAR.md and docs/CR-004_IMAGE_PROMPTS.json.

# Defect log

| ID | Severity | Status | Finding / resolution |
|---|---|---|---|
| PORT-001 | High | Fixed, retested | Initial seed/create SQL supplied nine placeholders to an eight-column table. Corrected; full API and browser CRUD suites pass. |
| PORT-002 | Medium | Fixed, retested | ESLint latest major conflicted with React plugin peer range. Installed compatible ESLint 9; lint passes. Upgrade when plugin supports newer major. |
| PORT-003 | High | Open, deployment limitation | No persistent backend hosting workflow/credentials were available. Third Vercel host serves static catalogue and account shell; authenticated admin requires local Docker service. |
| PORT-004 | Medium | Open | Password reset, email verification and self-service registration absent; operator provisioning is required. |
| PORT-005 | Medium | Open | SQLite single-instance persistence; no hosted backup/restore or concurrency/load certification. |
| PORT-006 | Medium | Open | Login/support limits use socket IP and can group users behind proxies/NAT. Configure trusted edge rate limiting for hosted launch. |
| PORT-007 | Low | Open | Orders/support/audit show latest 200 entries without cursor pagination. Catalogue list is unpaginated. |
| PORT-008 | Low | Open | Chromium coverage only; mobile device, Firefox/Safari, accessibility and manual exploratory checks pending. |
| PORT-009 | Low | Open | HTTPX TestClient emits a dependency deprecation warning; tests pass. Compatible ESLint/Newman tooling also emits deprecation notices. |
| PORT-010 | Medium | Open | Browser sessions intentionally live in memory: refresh requires sign-in. No MFA, password rotation UI or staff-user management UI. |
| PORT-012 | Medium | Fixed, retested | Concurrent Playwright suites shared output files and raised ENOENT trace errors. Separate output directories; seven enterprise rerun tests pass. |
| PORT-013 | Low | Resolved on rerun | Live navigation hit ERR_NETWORK_CHANGED once; complete live suite rerun passed ten tests. |
| PORT-011 | Low | Fixed, retested | API catalogue refresh on navigation added; hidden/removed product IDs no longer contribute phantom bag counts. |

No live payments, customer orders or donor financial records were used in QA. Existing pre-port defects in qa/cycle-01 remain historical evidence; this document does not erase them.

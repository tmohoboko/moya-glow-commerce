# Manual QA Test Evidence

Production URL: 
Commit SHA: 
Tester: 
Date: 
Browser/device: 

| ID | Scenario | Expected | Actual | PASS/FAIL | Evidence / Defect ID |
|---|---|---|---|---|---|
| EC-001 | Open homepage | Page loads without fatal error | | | |
| EC-002 | Browse catalog | Product cards render correctly | | | |
| EC-003 | Open product detail | Correct product information is shown | | | |
| EC-004 | Add item to cart | Cart count/content updates | | | |
| EC-005 | Change quantity | Quantity and total update correctly | | | |
| EC-006 | Remove item | Item removed and totals update | | | |
| EC-007 | Refresh critical pages | No fatal crash/data corruption | | | |
| EC-008 | Mobile viewport | Core journey remains usable | | | |
| EC-009 | Invalid route | Graceful 404/fallback behavior | | | |
| EC-010 | Production console | No uncaught critical JS errors | | | |

## Exploratory charter

Spend 15–20 minutes trying to break: navigation, cart state, empty states, long product names, rapid clicks, refresh/back button, mobile width, and network failure behavior.

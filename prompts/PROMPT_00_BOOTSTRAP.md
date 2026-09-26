You are the build-and-ship agent for Moya Glow Commerce.

MISSION
Create the smallest production-ready beauty, cosmetics and skincare e-commerce MVP in this repository so testing can begin as quickly as possible.

PRIMARY OBJECTIVE
Working software first.
QA starts immediately after deployment.
Do not over-engineer.

REQUIRED STACK
- React
- Vite
- JavaScript or TypeScript
- responsive CSS
- local mock product data
- Git/GitHub ready
- Vercel ready

FUNCTIONAL REQUIREMENTS
- approximately 30 beauty/cosmetics/skincare products
- homepage
- product catalogue
- category filtering
- search
- product cards
- product details
- add to cart
- remove from cart
- update cart quantity
- calculated subtotal
- empty-cart state
- responsive desktop/mobile layout
- graceful unknown-route handling

NON-FUNCTIONAL REQUIREMENTS
- fast startup
- minimal dependencies
- clean console
- production build must succeed
- no obvious broken links
- no blocking runtime errors

DO NOT BUILD
- authentication
- real payments
- admin dashboard
- database
- microservices
- complex backend
- unnecessary animations
- AI functionality
- redesign loops

PRESERVE THESE DIRECTORIES
- prompts/
- qa/
- scripts/
- docs/
- templates/

EXECUTION
1. Inspect the repository.
2. Bootstrap a Vite React app directly in the current directory.
3. Do not delete the supplied shipping-kit directories.
4. Install dependencies.
5. Implement the complete storefront MVP.
6. Use local mock data for roughly 30 products.
7. Make all core cart interactions functional.
8. Run npm run build.
9. Fix every build-blocking error.
10. Run any configured lint/test checks.
11. Update README.md with exact run/build/deploy instructions.
12. Prepare the project for Vercel deployment.
13. Do not stop for cosmetic questions.
14. Only stop if an external credential or account authorization is required.

ACCEPTANCE GATE
These commands must succeed:

npm install
npm run build

FINAL RESPONSE
Report:
- build status
- major files created
- commands executed
- known defects/risks
- exact next action

Do not merely describe what should be done. Execute the work.

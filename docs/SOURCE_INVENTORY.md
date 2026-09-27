# Source inventory

Purchased package: `codecanyon-zhgBGLQ0-adfund-fund-raising-platform-website-androidios-app-admin-panel.zip`.
Extracted, without replacing purchased files, to `../adfund-latest/`.
Latest full web archive: `main-files/adfund-web/adfund-web-new-file-v3.6.0.zip` (3.6.0). The previously extracted `../main-files` contains 3.3.0 and was not used.
Flutter reference: `main-files/adfund-app/adfund-app-new-v3.6.0/lib/`. Update-only archives were not used.

High-signal web files extracted separately into `../adfund-latest/web-source/`: composer/package manifests, routes, controllers, models, migrations, configuration. Vendor, caches, dependencies and generated output were excluded from reconnaissance. No purchased code is copied into the Moya repository.

Inspected evidence:
- `composer.json`: PHP ^8.2, Laravel ^12.60, Passport ^13, Sanctum ^4, Socialite, S3 adapter, notification and payment dependencies.
- `routes/admin.php`: admin authentication, `admin.role.guard`, role permission assignments, system maintenance, support tickets, notification setup.
- `routes/user.php`: authenticated user support-ticket flow.
- `app/Http/Controllers/Api/V1/Auth/LoginController.php`: credentials/password validation, active-user check, token authentication. Donor account-enumerating errors are deliberately not copied.
- `app/Http/Controllers/User/SupportTicketController.php`: subject/body validation, ticket ownership, threaded replies, closed ticket handling; attachments deferred.
- `app/Http/Controllers/Admin/SystemMaintenanceController.php`: persisted maintenance toggle.
- `database/migrations/`: admin login logs, users/auth, app settings, support, transactions; commerce schema is authored natively instead of translating fundraising tables.
- Flutter `lib/backend/services/api_endpoint.dart` and `lib/views/screens/auth/login/signin_screen.dart`: sign-in/reset/profile endpoint family, form validation, password entry, loading/error flow.

Target baseline: commit `d2a9f03`, React 19 + Vite static catalogue and cart; no pre-existing backend/API/payment provider. See PROTECTION_NOTE.md.

Purchased ZIP SHA-256: `65cefcf8f93104bec94b9ece1303195309841606932c0946be1b95ec0e13cb2d`.

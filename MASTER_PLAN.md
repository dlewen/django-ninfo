# MASTER_PLAN: django-ninfo

## Identity

**Type:** web-app (Django/DRF backend + SPA frontend)
**Languages:** Python (70%), JavaScript (20%), HTML/CSS (10%)
**Root:** /home/dm/code/ninfo/django-ninfo
**Created:** 2026-03-03
**Last updated:** 2026-04-18

Django/DRF web frontend for the `ninfo` threat intelligence plugin framework. Provides a browser-based interface for querying ninfo plugins (single and multi-lookup) with parallel API fetches, progress tracking, and HTML fragment rendering. Deployed via Docker (Gunicorn + nginx + Traefik) from a separate ninfo-docker repo. The app has no Django models -- it wraps the ninfo library's plugin system through 3 DRF API endpoints and serves a single-page application.

## Architecture

  django_ninfo/           -- Django app package (views, urls, templates, static)
  django_ninfo/views.py   -- 3 DRF views: PluginViewSet (list), PluginResult (get html/json/txt), Extract (parse query)
  django_ninfo/urls.py    -- URL routing: API endpoints + login-required index view
  django_ninfo/templates/ -- index.html (SPA shell), login.html (bare form)
  django_ninfo/static/    -- AngularJS app (app.js), partials (single/multiple.html), Bootstrap 5, CSS
  setup.py                -- Package config, dependencies (djangorestframework, ninfo>=0.3.1)

## Original Intent

> Modernize django-ninfo: replace the bare Django login form with Keycloak/Azure Entra
> OIDC authentication via mozilla-django-oidc, replace the AngularJS 1.2.6 SPA with
> Alpine.js 3.x (no build step, near-1:1 directive replacement), and clean up Django
> internals (re_path to path, python-decouple for secrets, DEFAULT_AUTO_FIELD). The app
> should remain backward-compatible with plain Django auth for local development.

## Principles

These are the project's enduring design principles. They do not change between initiatives.

1. **No Build Step** -- The frontend ships as static files loaded via CDN or vendored. No webpack, no npm, no node_modules. Alpine.js and htmx-style simplicity.
2. **Provider-Agnostic Auth** -- Authentication configuration is entirely env-var-driven. The same code handles Keycloak, Azure Entra, or any OIDC provider. No provider-specific code paths.
3. **Backward Compatibility** -- The app must work with plain Django auth when OIDC is not configured. This supports local development and non-OIDC deployments.
4. **Minimal Footprint** -- This is a small app wrapping a library. Keep it small. No ORM models, no complex middleware, no unnecessary abstractions.
5. **Configuration via Environment** -- Secrets and deployment-specific values come from environment variables, never hardcoded. Enforced via custom `_env()`/`_bool_env()` helpers in `oidc_settings.py` (python-decouple was considered but intentionally skipped — see DEC-CLEAN-002-OVERRIDE).

---

## Decision Log

Append-only record of significant decisions across all initiatives. Each entry references
the initiative and decision ID. This log persists across initiative boundaries -- it is the
project's institutional memory.

| Date | DEC-ID | Initiative | Decision | Rationale |
|------|--------|-----------|----------|-----------|
| 2026-03-03 | DEC-AUTH-001 | modernize | Use mozilla-django-oidc v5.0.2 for OIDC authentication | Provider-agnostic; same code for Keycloak and Azure Entra via env vars. Mature library, Django-native, handles token refresh and session management. |
| 2026-03-03 | DEC-AUTH-002 | modernize | Keep Django auth fallback when OIDC is unconfigured | Supports local dev without running an IdP. login_required and IsAuthenticated work unchanged with either backend. |
| 2026-03-03 | DEC-FE-001 | modernize | Replace AngularJS 1.2.6 with Alpine.js 3.x | Near-1:1 replacement for ng-* directives. ~15KB, no build step, CDN-loadable. AngularJS 1.x is EOL and has known XSS vectors. |
| 2026-03-03 | DEC-FE-002 | modernize | Drop jQuery 1.12.4 | Only used for $.each() in Angular controllers and smooth scroll. Alpine.js uses native JS; scroll uses Element.scrollIntoView(). |
| 2026-03-03 | DEC-CLEAN-001 | modernize | Migrate re_path() to path() where regex is unnecessary | path() is more readable and the standard Django pattern. Keep re_path only where regex capture groups are genuinely needed. |
| 2026-03-03 | DEC-CLEAN-002 | modernize | Adopt python-decouple for settings/secrets management | Separates config from code. Reads from .env files and environment variables. Standard pattern for 12-factor Django apps. |
| 2026-03-03 | DEC-CLEAN-003 | modernize | Set DEFAULT_AUTO_FIELD | Silences Django 3.2+ warning. Required for any future model additions (e.g., if mozilla-django-oidc needs migration state). |
| 2026-03-03 | DEC-ROUTE-001 | modernize | Serve app at / instead of /ninfo/ | Eliminates double-redirect. ninfo-docker mounts django_ninfo.urls at '' (last in urlpatterns). Frontend API paths change from /ninfo/api/ to /api/. Cross-repo: ninfo-docker urls.py + django-ninfo app.js (and Alpine.js rewrite). |
| 2026-04-18 | DEC-CLEAN-002-OVERRIDE | modernize | Skip python-decouple; use custom `_env()`/`_bool_env()` helpers in `oidc_settings.py` | One less dependency. Trivial wrappers over `os.environ` are sufficient for this app's config surface. The OIDC settings file already encapsulates all env-var access through these helpers. Overrides DEC-CLEAN-002. |
| 2026-04-18 | DEC-FE-003 | modernize | Vendor Alpine.js locally instead of loading from CDN | No external CDN dependency at runtime; deployment is self-contained. Commit `7ffe476`. Diverges from DEC-FE-001 which planned CDN loading. |

---

## Active Initiatives

### Initiative: Modernize
**Status:** active
**Started:** 2026-03-03
**Goal:** Replace deprecated frontend and authentication with modern, maintainable alternatives while cleaning up Django internals.

> django-ninfo runs on AngularJS 1.2.6 (EOL since 2021, known security issues) and jQuery
> 1.12.4, with a bare Django login form for authentication. The modernization replaces auth
> with provider-agnostic OIDC (supporting both Keycloak and Azure Entra deployments), rewrites
> the 177-line AngularJS SPA to Alpine.js 3.x with no build step, and cleans up Django routing
> and configuration patterns. All three workstreams are largely independent.

**Dominant Constraint:** simplicity

#### Goals
- REQ-GOAL-001: Eliminate all EOL JavaScript dependencies (AngularJS 1.2.6, jQuery 1.12.4)
- REQ-GOAL-002: Enable enterprise SSO via OIDC (Keycloak and Azure Entra) without provider-specific code
- REQ-GOAL-003: Externalize all secrets and deployment config to environment variables
- REQ-GOAL-004: Preserve full feature parity -- single lookup, multi lookup, plugin progress, theme toggle all work identically

#### Non-Goals
- REQ-NOGO-001: Django model layer changes -- the app has no models and should stay that way (mozilla-django-oidc uses Django's existing auth tables)
- REQ-NOGO-002: ninfo-docker deployment changes -- env var additions for OIDC are deployment config, tracked separately
- REQ-NOGO-003: API endpoint changes -- the 3 DRF views (PluginViewSet, PluginResult, Extract) stay as-is; only auth decorators may change
- REQ-NOGO-004: Build toolchain -- no webpack, no npm, no transpilation. Static files only.

#### Requirements

**Must-Have (P0)**

- REQ-P0-001: OIDC authentication via mozilla-django-oidc with Keycloak and Azure Entra support
  Acceptance: Given OIDC env vars are set, When a user visits the app unauthenticated, Then they are redirected to the OIDC provider login, and after successful auth they land on the index page with a valid Django session.

- REQ-P0-002: Fallback to Django auth when OIDC is not configured
  Acceptance: Given OIDC env vars are unset, When a user visits the app unauthenticated, Then they see the Django login form and can authenticate with username/password.

- REQ-P0-003: Replace AngularJS app.js with Alpine.js equivalent
  Acceptance: Given the Alpine.js rewrite is deployed, When a user performs a single lookup, Then plugins load in parallel with a progress bar, results render as HTML fragments, and the plugin nav pills appear -- identical to the AngularJS version.

- REQ-P0-004: Replace AngularJS partials (single.html, multiple.html) with Alpine.js templates
  Acceptance: Given the Alpine.js rewrite, When a user navigates to multi search, Then they can paste multiple indicators, select plugins, and see results grouped by indicator with progress tracking.

- REQ-P0-005: Drop jQuery 1.12.4 and AngularJS 1.2.6 CDN dependencies
  Acceptance: Given the rewrite is complete, When index.html is loaded, Then no requests are made to ajax.googleapis.com for jQuery or AngularJS.

- REQ-P0-006: Externalize secrets with python-decouple
  Acceptance: Given a .env file with SECRET_KEY and OIDC settings, When the app starts, Then it reads config from environment/file without any hardcoded secrets in source.

**Nice-to-Have (P1)**

- REQ-P1-001: Convert re_path() to path() in urls.py where regex is not needed
  Acceptance: The extract and index URL patterns use path(); plugin result patterns may keep re_path if regex capture is genuinely needed.

- REQ-P1-002: Set DEFAULT_AUTO_FIELD in Django settings
  Acceptance: No Django startup warnings about DEFAULT_AUTO_FIELD.

- REQ-P1-003: OIDC logout (redirect to provider logout endpoint)
  Acceptance: Given the user clicks logout, Then their Django session is destroyed AND they are logged out of the OIDC provider.

**Future Consideration (P2)**

- REQ-P2-001: OIDC group/role mapping for authorization (admin vs. read-only)
- REQ-P2-002: Rate limiting on API endpoints
- REQ-P2-003: WebSocket-based plugin result streaming (replace polling/parallel fetch)

#### Definition of Done

All P0 requirements pass acceptance criteria. The app works with both OIDC auth (Keycloak or Azure Entra) and fallback Django auth. No AngularJS or jQuery code remains. No hardcoded secrets. The Docker deployment (ninfo-docker) can be updated with env vars to enable OIDC without code changes to django-ninfo.

#### Architectural Decisions

- DEC-AUTH-001: Use mozilla-django-oidc v5.0.2 for OIDC authentication
  Addresses: REQ-P0-001, REQ-P0-002.
  Rationale: Provider-agnostic OIDC integration. Adds OIDCAuthenticationBackend to AUTHENTICATION_BACKENDS alongside ModelBackend. When OIDC_OP_AUTHORIZATION_ENDPOINT is set, the OIDC middleware activates; when unset, Django falls back to ModelBackend. Same code handles Keycloak and Azure Entra -- only env vars differ per deployment.

- DEC-AUTH-002: Keep Django auth fallback when OIDC is unconfigured
  Addresses: REQ-P0-002.
  Rationale: ModelBackend stays in AUTHENTICATION_BACKENDS list. The login view conditionally redirects to OIDC or shows the Django form based on whether OIDC is configured. Zero-config local development without an IdP.

- DEC-FE-001: Replace AngularJS 1.2.6 with Alpine.js 3.x
  Addresses: REQ-P0-003, REQ-P0-004, REQ-P0-005.
  Rationale: Alpine.js provides x-data, x-for, x-show, x-on, x-html as near-1:1 replacements for ng-model, ng-repeat, ng-show, ng-submit, ng-bind-html. ~15KB from CDN, no build step. The current app.js is 177 lines -- the Alpine.js version will be comparable. Client-side routing (Angular ngRoute) is replaced by showing/hiding sections or using simple hash-based routing in Alpine.

- DEC-FE-002: Drop jQuery 1.12.4
  Addresses: REQ-P0-005.
  Rationale: jQuery is only used for $.each() (replaced by native forEach) and animated scroll (replaced by Element.scrollIntoView({behavior:'smooth'})). No other jQuery usage in the codebase.

- DEC-CLEAN-001: Migrate re_path() to path() where possible
  Addresses: REQ-P1-001.
  Rationale: The extract endpoint (`r'api/extract'`) and index (`r'^$'`) need no regex. Plugin result routes use regex capture groups for format and arg -- evaluate whether path converters suffice or re_path should stay.

- DEC-CLEAN-002: Adopt python-decouple for settings/secrets
  Addresses: REQ-P0-006.
  Rationale: Reads .env files in development, environment variables in production. Standard 12-factor pattern. Replaces any os.environ.get() scattered in settings with typed config() calls.

- DEC-CLEAN-003: Set DEFAULT_AUTO_FIELD
  Addresses: REQ-P1-002.
  Rationale: Required since Django 3.2. Set to django.db.models.BigAutoField. Even though django-ninfo has no models, it silences the warning for the project-level settings.

#### Phase 1: OIDC Authentication
**Status:** completed
**Decision IDs:** DEC-AUTH-001, DEC-AUTH-002
**Requirements:** REQ-P0-001, REQ-P0-002, REQ-P1-003
**Issues:** [#1](https://github.com/dlewen/django-ninfo/issues/1)
**Definition of Done:**
- REQ-P0-001 satisfied: Unauthenticated users redirected to OIDC provider, successful auth creates Django session
- REQ-P0-002 satisfied: App works with plain Django auth when OIDC env vars are absent
- REQ-P1-003 satisfied: Logout destroys session and redirects to OIDC provider logout

##### Planned Decisions
- DEC-AUTH-001: mozilla-django-oidc with dual backend (OIDC + ModelBackend) -- provider-agnostic via env vars -- Addresses: REQ-P0-001, REQ-P0-002
- DEC-AUTH-002: Conditional OIDC activation based on env var presence -- Addresses: REQ-P0-002

##### Work Items

**W1-1: Add mozilla-django-oidc to dependencies**
- Add `mozilla-django-oidc>=5.0.0` to `setup.py` install_requires
- File: `/home/dm/code/ninfo/django-ninfo/setup.py` line 31

**W1-2: Configure OIDC authentication backends**
- Add OIDCAuthenticationBackend to AUTHENTICATION_BACKENDS (keep ModelBackend)
- Add OIDC settings block: OIDC_OP_AUTHORIZATION_ENDPOINT, OIDC_OP_TOKEN_ENDPOINT, OIDC_OP_USER_ENDPOINT, OIDC_OP_JWKS_ENDPOINT, OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET, OIDC_RP_SIGN_ALGO
- All values read from environment via python-decouple config()
- Add conditional: only add OIDCAuthenticationBackend if OIDC_RP_CLIENT_ID is set
- Note: Django settings file is in the deployment repo (ninfo-docker), but the app package should document required settings. Consider adding a `django_ninfo/settings_oidc.py` mixin or documenting in README.
- Risk: The Django settings file lives in ninfo-docker, not in this repo. Phase 1 work items that touch settings need to either (a) provide a settings snippet for ninfo-docker to include, or (b) use Django's AppConfig.ready() to inject settings conditionally. Recommend (a) with clear documentation.

**W1-3: Add OIDC URL patterns**
- Include `mozilla_django_oidc.urls` in url patterns
- Add OIDC callback URL: `path('oidc/', include('mozilla_django_oidc.urls'))`
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/urls.py`

**W1-4: Conditional login redirect**
- When OIDC is configured: login_required redirects to OIDC authorize endpoint (LOGIN_URL = '/oidc/authenticate/')
- When OIDC is unconfigured: login_required redirects to Django login form (LOGIN_URL = '/accounts/login/')
- Note: with DEC-ROUTE-001, the app serves at / so unauthenticated visits to / redirect directly to OIDC — no double-redirect
- The login.html template can show a "Login with SSO" button when OIDC is configured, or the standard form when not
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/registration/login.html`

**W1-5: OIDC logout**
- Add logout view that destroys Django session and redirects to OIDC end_session_endpoint
- mozilla-django-oidc provides OIDCLogoutView for this
- Wire up logout URL in navbar (currently no logout link exists -- add one)
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/ninfo/index.html` (navbar)

**W1-6: Add OIDC session refresh middleware**
- Add `mozilla_django_oidc.middleware.SessionRefresh` to MIDDLEWARE
- This silently refreshes OIDC tokens before they expire
- Settings documentation for ninfo-docker

##### Critical Files
- `/home/dm/code/ninfo/django-ninfo/setup.py` -- dependency addition
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/urls.py` -- OIDC URL include
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/registration/login.html` -- conditional SSO/form login
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/ninfo/index.html` -- logout link in navbar

##### Risks and Considerations
- Django settings live in ninfo-docker, not this repo. OIDC settings must be documented as a snippet for the deployment repo.
- mozilla-django-oidc requires Django's auth tables (django_session, auth_user). These already exist in the Docker SQLite DB.
- OIDC callback URL must be registered with the IdP. Document the expected callback URL in README.
- Session refresh middleware adds a check on every request. Acceptable for this low-traffic app.

##### Decision Log
| Date | DEC-ID | Decision | Rationale |
|------|--------|----------|-----------|
| 2026-04-18 | DEC-AUTH-001 | mozilla-django-oidc v5.0.0+ added to setup.py install_requires; `oidc_settings.py` + `oidc_utils.py` created for OIDC configuration and RP-initiated logout | Provider-agnostic; env-var-driven. Commits: `6cb74ea` (primary impl), `3ee6bc1` (move OIDC URLs out of namespaced app urls). ninfo-docker wired at `7e58798`, `fb0db5f`, `92f002b`. |
| 2026-04-18 | DEC-AUTH-002 | Conditional OIDC activation via `oidc_enabled()` helper in `oidc_settings.py`; login.html shows SSO button only when OIDC is configured; `?force_local=1` override preserved for local dev | ModelBackend stays active; zero-config local dev without an IdP. |

#### Phase 2: Alpine.js Frontend Rewrite
**Status:** completed
**Decision IDs:** DEC-FE-001, DEC-FE-002
**Requirements:** REQ-P0-003, REQ-P0-004, REQ-P0-005, REQ-GOAL-001, REQ-GOAL-004
**Issues:** [#2](https://github.com/dlewen/django-ninfo/issues/2)
**Definition of Done:**
- REQ-P0-003 satisfied: Single lookup works with parallel plugin fetches, progress bar, HTML fragment rendering
- REQ-P0-004 satisfied: Multi lookup works with textarea input, plugin selection, grouped results
- REQ-P0-005 satisfied: No AngularJS or jQuery script tags remain in index.html
- REQ-GOAL-004 satisfied: Visual and functional parity with current AngularJS app

##### Planned Decisions
- DEC-FE-001: Alpine.js 3.x as AngularJS replacement -- CDN-loaded, no build step -- Addresses: REQ-P0-003, REQ-P0-004, REQ-P0-005
- DEC-FE-002: Drop jQuery, use native JS equivalents -- Addresses: REQ-P0-005
- DEC-ROUTE-001: Serve app at / instead of /ninfo/ -- Addresses: REQ-GOAL-004

##### Work Items

**W2-1: Rewrite app.js as Alpine.js application**
- Replace Angular module/routing/controllers with Alpine.js x-data components
- Current routing: `/single`, `/single/:arg`, `/multiple` via ngRoute
- Alpine.js approach: Use hash-based routing with a reactive `page` variable, or inline all views in index.html with x-show. Given the app has only 2 routes, inline with x-show is simpler.
- Port controller logic:
  - `Single` controller: arg model, lookup() navigates to single/:arg
  - `SingleArg` controller: fetch plugins, parallel HTML fetches, progress tracking (started/running/success/error/empty), scroll_to
  - `Multiple` controller: textarea q model, extract API call, parallel fetches per arg per plugin, toggle_all, progress
- Port `result` directive: Alpine.js component that fetches `/api/plugins/{name}/html/{arg}`, sets innerHTML via x-html
- Replace `$.each()` with `Array.forEach()` or `for...of`
- Replace `$sce.trustAsHtml()` with Alpine.js x-html (note: XSS consideration -- ninfo plugins generate trusted HTML server-side)
- Replace jQuery animated scroll with `Element.scrollIntoView({behavior:'smooth'})`
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/js/app.js` (full rewrite, ~177 lines)

**W2-2: Rewrite index.html for Alpine.js**
- Remove ng-app, ng-controller, ng-view, ng-submit, ng-model, ng-click, ng-show directives
- Add Alpine.js CDN script tag: `<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>`
- Remove AngularJS and jQuery CDN script tags (lines 229-231)
- Replace ng-view with Alpine.js routed content (x-show sections or template switching)
- Move navbar search form to use Alpine.js: x-data, x-model, @submit.prevent
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/ninfo/index.html`

**W2-3: Rewrite single.html partial**
- Convert ng-show, ng-repeat, ng-style, ng-click to Alpine.js equivalents (x-show, x-for, :style, @click)
- The progress bar logic (bar_success/bar_empty/bar_error) becomes computed properties in x-data
- Plugin nav pills: x-for over checked plugins with x-show for hasResult
- Result rendering: x-html for trusted HTML content
- May inline into index.html if using x-show routing (eliminate partials entirely)
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/partials/single.html`

**W2-4: Rewrite multiple.html partial**
- Convert form with textarea, plugin checkboxes, toggle_all to Alpine.js
- Nested results: x-for over args, x-for over plugins per arg
- Progress tracking across all arg/plugin combinations
- May inline into index.html (eliminate partials)
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/partials/multiple.html`

**W2-5: Remove /ninfo/ prefix from API paths (DEC-ROUTE-001)**
- Alpine.js rewrite uses `/api/` instead of `/ninfo/api/` for all fetch calls
- No changes needed in django_ninfo/urls.py (API paths are relative: `api/plugins/...`)
- Cross-repo: ninfo-docker urls.py must mount django_ninfo at `path('', ...)` instead of `path('ninfo/', ...)`
- Cross-repo: ninfo-docker urls.py remove the `/` → `/ninfo/` RedirectView
- Cross-repo: ninfo-docker urls.py ensure django_ninfo include is LAST (after admin/, accounts/, oidc/)
- Files: `app.js` (this repo, part of rewrite), `ninfo_www/urls.py` (ninfo-docker repo)

**W2-6: Clean up removed files**
- If partials are inlined into index.html, delete single.html and multiple.html
- Remove jQuery CDN reference
- Remove AngularJS CDN references
- Verify no other static files reference Angular or jQuery

##### Critical Files
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/js/app.js` -- full rewrite (177 lines Angular -> Alpine.js)
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/templates/ninfo/index.html` -- script tags, directives, routing
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/partials/single.html` -- rewrite or inline
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/partials/multiple.html` -- rewrite or inline

##### Risks and Considerations
- x-html in Alpine.js does not sanitize HTML. The ninfo plugins generate HTML server-side, which is trusted. This is equivalent to the current ng-bind-html + $sce.trustAsHtml() pattern. Document this trust boundary.
- The current app uses Angular's ngRoute for client-side routing with browser back/forward support. Alpine.js has no built-in router. Options: (a) hash-based routing with window.onhashchange, (b) inline all views with x-show. For 2 routes, x-show is simpler but loses URL-based navigation. Recommend hash routing to preserve bookmark-ability of `/single/:arg`.
- The `result` directive creates a child scope with isolated arg/plugin bindings and communicates progress to $parent. Alpine.js equivalent: use x-init with fetch() inside a template loop, with progress state in the parent x-data.

##### Decision Log
| Date | DEC-ID | Decision | Rationale |
|------|--------|----------|-----------|
| 2026-04-18 | DEC-FE-001 | AngularJS 1.2.6 + jQuery 1.12.4 replaced with Alpine.js 3.x; partials (`single.html`, `multiple.html`) deleted and inlined into `index.html`; hash-based routing via custom `ninfoRouter` in `app.js` | Near-1:1 directive replacement, no build step, ~15KB. Commit: `cbe0a5a`. |
| 2026-04-18 | DEC-FE-002 | jQuery dropped; native `Array.forEach()` and `Element.scrollIntoView()` used throughout | No jQuery usage remained once Angular controllers were ported. Commit: `cbe0a5a`. |
| 2026-04-18 | DEC-FE-003 | Alpine.js vendored locally instead of CDN | No external CDN dependency at runtime; deployment is self-contained. Commit: `7ffe476`. Diverges from original DEC-FE-001 CDN plan. |
| 2026-04-18 | DEC-ROUTE-001 | API fetch paths use `/api/` (not `/ninfo/api/`); ninfo-docker mounts `django_ninfo.urls` at `path('', ...)` as catch-all | Eliminates double-redirect; single consistent URL namespace. Cross-repo: ninfo-docker. Commit: `cbe0a5a` (app.js), ninfo-docker `7e58798`. |

#### Phase 3: Django Cleanup
**Status:** in-progress
**Decision IDs:** DEC-CLEAN-001, DEC-CLEAN-002, DEC-CLEAN-003
**Requirements:** REQ-P0-006, REQ-P1-001, REQ-P1-002
**Issues:** [#3](https://github.com/dlewen/django-ninfo/issues/3)
**Definition of Done:**
- REQ-P0-006 satisfied: Env-var-based config encapsulated (done via `_env()`/`_bool_env()` helpers — see DEC-CLEAN-002-OVERRIDE; python-decouple intentionally skipped)
- REQ-P1-001 satisfied: 3 eligible re_path() patterns migrated to path() in urls.py (W3-2)
- REQ-P1-002 satisfied: No DEFAULT_AUTO_FIELD warning on startup (DONE — set in ninfo-docker settings)
- Python classifiers updated to include 3.10, 3.11, 3.12 (W3-5)
- .env.example created at repo root (W3-3)

##### Planned Decisions
- DEC-CLEAN-001: re_path() to path() migration -- Addresses: REQ-P1-001
- DEC-CLEAN-002: python-decouple for settings -- OVERRIDDEN by DEC-CLEAN-002-OVERRIDE (custom helpers used instead)
- DEC-CLEAN-003: Set DEFAULT_AUTO_FIELD -- Addresses: REQ-P1-002 (completed in ninfo-docker)

##### Work Items

**W3-1: Add python-decouple to dependencies** — INTENTIONALLY SKIPPED (see DEC-CLEAN-002-OVERRIDE)
- Rationale: Custom `_env()`/`_bool_env()` helpers in `oidc_settings.py` provide equivalent functionality with one fewer dependency. All env-var access for OIDC is already encapsulated there.
- File: `/home/dm/code/ninfo/django-ninfo/setup.py`

**W3-2: Migrate urls.py to path() where possible** — NOT STARTED
- Scope (3 eligible patterns out of 7 total):
  - `r'api/extract'` → `path('api/extract', ...)` (no captures)
  - `r'api/'` router include → `path('api/', ...)`
  - `r'^$'` index → `path('', ...)`
- Keep re_path for the 4 patterns that legitimately need regex:
  - Plugin result routes with `\w*` and format-suffix captures (`.json|.txt`)
- File: `/home/dm/code/ninfo/django-ninfo/django_ninfo/urls.py`

**W3-3: Create .env.example file**
- Document all environment variables: SECRET_KEY, DEBUG, ALLOWED_HOSTS, OIDC_* settings
- Provide sensible defaults for local development
- File: `/home/dm/code/ninfo/django-ninfo/.env.example` (new file)

**W3-4: Document DEFAULT_AUTO_FIELD setting** — DONE
- `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` set in `ninfo-docker/build/app/ninfo_www/settings.py` line 148.
- No further action needed in this repo.

**W3-5: Update setup.py metadata** — PARTIAL
- `mozilla-django-oidc>=5.0.0` already added (done in Phase 1, commit `6cb74ea`)
- `python-decouple` intentionally skipped (see DEC-CLEAN-002-OVERRIDE)
- Python version classifiers still list only 3.9 — update to include 3.10, 3.11, 3.12
- File: `/home/dm/code/ninfo/django-ninfo/setup.py`

##### Critical Files
- `/home/dm/code/ninfo/django-ninfo/django_ninfo/urls.py` -- path() migration
- `/home/dm/code/ninfo/django-ninfo/setup.py` -- dependency and metadata updates
- `/home/dm/code/ninfo/django-ninfo/.env.example` -- new file, environment documentation

##### Risks and Considerations
- path() converter `<str:plugin>` matches non-empty strings without slashes. The current `\w*` matches zero-or-more word chars. If any plugin name is empty string, path() would not match. This is likely fine (empty plugin name is an error case) but verify.
- python-decouple requires the consuming settings.py (in ninfo-docker) to import and use config(). This is a cross-repo change.
- Phase 3 can be done in parallel with Phase 1 or Phase 2 since it touches different concerns, but the python-decouple work in W3-1 supports the OIDC config in Phase 1. Consider doing W3-1 and W3-2 first, or bundling W3-1 with Phase 1.

##### Decision Log
<!-- Guardian appends here after phase completion -->

#### Modernize Worktree Strategy

Main is sacred. Each phase works in its own worktree:
- **Phase 1:** `/home/dm/code/ninfo/django-ninfo/.worktrees/phase-1-oidc-auth` on branch `feature/oidc-auth`
- **Phase 2:** `/home/dm/code/ninfo/django-ninfo/.worktrees/phase-2-alpine-frontend` on branch `feature/alpine-frontend`
- **Phase 3:** `/home/dm/code/ninfo/django-ninfo/.worktrees/phase-3-django-cleanup` on branch `feature/django-cleanup`

Phase 1 and Phase 2 are independent and can be worked in parallel. Phase 3 overlaps with Phase 1 (python-decouple supports OIDC config) -- either bundle decouple with Phase 1, or do Phase 3 first.

#### Modernize References

- mozilla-django-oidc docs: https://mozilla-django-oidc.readthedocs.io/en/stable/
- Alpine.js docs: https://alpinejs.dev/
- python-decouple docs: https://pypi.org/project/python-decouple/
- ninfo library: https://github.com/JustinAzoff/ninfo
- ninfo-docker deployment: /home/dm/code/ninfo/ninfo-docker/ (separate repo, out of scope for code changes)
- Current AngularJS app: `/home/dm/code/ninfo/django-ninfo/django_ninfo/static/ninfo/js/app.js` (177 lines, reference for Alpine.js port)

---

## Active Initiatives

### Initiative: IOC Linkification
**Status:** active
**Started:** 2026-03-08
**Goal:** Server-side linkification of IOC values in plugin HTML output so that hashes, IPs, and domains rendered by ninfo plugins become clickable links navigating to the single-lookup view.

**Dominant Constraint:** minimal footprint — one new dependency (beautifulsoup4), no JS changes, no new views.

#### Goals
- REQ-GOAL-005: IOC spans in plugin HTML output become anchor tags pointing to `#/single/<value>`
- REQ-GOAL-006: Only ninfo-typed spans (md5, sha1, sha256, ip, domain) are linkified; surrounding HTML is preserved
- REQ-GOAL-007: Linkification is transparent — non-HTML formats (json, txt) are unaffected

#### Requirements

**Must-Have (P0)**

- REQ-P0-007: Server-side linkification of IOC spans in plugin HTML responses
  Acceptance: Given a plugin returns HTML with `<span class="ninfo-ip">...</span>`, When the PluginResult view returns the response, Then the span is replaced with a clickable anchor pointing to `#/single/<value>`.

#### Architectural Decisions

- DEC-LINKIFY-001: Server-side linkification via BeautifulSoup in PluginResult.get()
  Addresses: REQ-P0-007, REQ-GOAL-005, REQ-GOAL-006, REQ-GOAL-007.
  Rationale: Parsing HTML in the view layer with BeautifulSoup ensures all plugin outputs get clickable IOC links without requiring JS-side post-processing. Spans with ninfo-* classes are replaced with anchor tags pointing to #/single/<value>. Applied only when format == "html".

#### Phase: IOC Linkification
**Status:** in-progress
**Decision IDs:** DEC-LINKIFY-001
**Branch:** feature/ioc-linkify
**Worktree:** .worktrees/ioc-linkify

##### Work Items

**WL-1: Add BeautifulSoup import and linkify_iocs() function to views.py**
- File: `django_ninfo/views.py`
- Status: done

**WL-2: Call linkify_iocs() in PluginResult.get() for HTML format**
- File: `django_ninfo/views.py`
- Status: done

**WL-3: Create ninfo.css with anchor styles for .ninfo-ioc**
- File: `django_ninfo/static/ninfo/css/ninfo.css`
- Status: done

**WL-4: Add beautifulsoup4 to install_requires**
- File: `setup.py`
- Status: done

**WL-5: Unit tests for linkify_iocs()**
- File: `tests/test_linkify.py`
- Status: in-progress

##### Decision Log
| Date | DEC-ID | Decision | Rationale |
|------|--------|----------|-----------|
| 2026-03-08 | DEC-LINKIFY-001 | BeautifulSoup server-side linkification | No JS changes needed; pure HTML transformation in view layer |

---

## Completed Initiatives

| Initiative | Period | Phases | Key Decisions | Archived |
|-----------|--------|--------|---------------|----------|

---

## Parked Issues

Issues not belonging to any active initiative. Tracked for future consideration.

| Issue | Description | Reason Parked |
|-------|-------------|---------------|

"""
OIDC settings helper for django-ninfo.

Provides a conditional OIDC configuration that deployment projects can import
and merge into their Django settings. OIDC is enabled only when
OIDC_RP_CLIENT_ID is present in the environment; otherwise the app falls back
to standard Django authentication, keeping local development working without
an identity provider.

Usage in the deployment settings.py::

    from django_ninfo.oidc_settings import get_oidc_settings
    locals().update(get_oidc_settings())

Required environment variables (when OIDC is desired):
    OIDC_RP_CLIENT_ID               -- Relying-party client ID
    OIDC_RP_CLIENT_SECRET           -- Relying-party client secret
    OIDC_OP_AUTHORIZATION_ENDPOINT  -- IdP authorization endpoint URL
    OIDC_OP_TOKEN_ENDPOINT          -- IdP token endpoint URL
    OIDC_OP_USER_ENDPOINT           -- IdP userinfo endpoint URL
    OIDC_OP_JWKS_ENDPOINT           -- IdP JWKS (public keys) endpoint URL

Optional environment variables:
    OIDC_OP_END_SESSION_ENDPOINT    -- IdP end-session URL (enables RP-initiated logout)
    OIDC_RP_SIGN_ALGO               -- JWT signing algorithm (default: RS256)
    OIDC_USE_PKCE                   -- Set to "True" to enable PKCE (default: True)
    OIDC_VERIFY_SSL                 -- Set to "False" to skip SSL verification (dev only)

@decision DEC-AUTH-001
@title Use mozilla-django-oidc for OIDC authentication
@status accepted
@rationale Provider-agnostic OIDC client — same code handles Keycloak and
            Azure Entra, only environment variables differ. No proprietary
            SDK or provider lock-in.

@decision DEC-AUTH-002
@title Keep Django ModelBackend when OIDC is unconfigured
@status accepted
@rationale Local development works without an IdP. The fallback is
            controlled purely by the absence of OIDC_RP_CLIENT_ID.
"""

import os

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _env(key, default=None):
    """Return stripped environment variable value, or default."""
    val = os.environ.get(key, default)
    return val.strip() if isinstance(val, str) else val


def _bool_env(key, default=True):
    """Return boolean from environment variable."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() not in ("false", "0", "no", "off")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def oidc_enabled():
    """Return True when OIDC_RP_CLIENT_ID is set in the environment."""
    return bool(_env("OIDC_RP_CLIENT_ID"))


def get_oidc_settings():
    """
    Return a dict of Django settings for OIDC configuration.

    The returned dict is designed to be merged into the deployment project's
    settings module::

        locals().update(get_oidc_settings())

    When OIDC is disabled (OIDC_RP_CLIENT_ID absent), returns minimal
    settings that keep standard Django auth working unchanged.

    When OIDC is enabled, returns the full complement of mozilla-django-oidc
    settings drawn from environment variables plus safe defaults.
    """
    if not oidc_enabled():
        return {
            "AUTHENTICATION_BACKENDS": [
                "django.contrib.auth.backends.ModelBackend",
            ],
            "LOGIN_URL": "/accounts/login/",
            # Expose flag for templates / context processors
            "OIDC_ENABLED": False,
        }

    settings = {
        # --- Auth backends: OIDC first, Django local auth as fallback ---
        "AUTHENTICATION_BACKENDS": [
            "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
            "django.contrib.auth.backends.ModelBackend",
        ],

        # --- Redirect to OIDC provider on unauthenticated access ---
        "LOGIN_URL": "/oidc/authenticate/",

        # --- Expose flag for templates / context processors ---
        "OIDC_ENABLED": True,

        # --- Relying-party credentials (required) ---
        "OIDC_RP_CLIENT_ID": _env("OIDC_RP_CLIENT_ID"),
        "OIDC_RP_CLIENT_SECRET": _env("OIDC_RP_CLIENT_SECRET"),

        # --- Provider endpoints (required) ---
        "OIDC_OP_AUTHORIZATION_ENDPOINT": _env("OIDC_OP_AUTHORIZATION_ENDPOINT"),
        "OIDC_OP_TOKEN_ENDPOINT": _env("OIDC_OP_TOKEN_ENDPOINT"),
        "OIDC_OP_USER_ENDPOINT": _env("OIDC_OP_USER_ENDPOINT"),
        "OIDC_OP_JWKS_ENDPOINT": _env("OIDC_OP_JWKS_ENDPOINT"),

        # --- Optional: end-session (RP-initiated logout) ---
        "OIDC_OP_LOGOUT_URL_METHOD": "django_ninfo.oidc_utils.provider_logout",

        # --- Algorithm and security ---
        "OIDC_RP_SIGN_ALGO": _env("OIDC_RP_SIGN_ALGO", "RS256"),
        "OIDC_USE_PKCE": _bool_env("OIDC_USE_PKCE", default=True),
        "OIDC_VERIFY_SSL": _bool_env("OIDC_VERIFY_SSL", default=True),

        # --- Session behaviour: renew token in background ---
        # Requires SessionRefresh middleware — see deployment notes below.
        "OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS": 15 * 60,  # 15 minutes
    }

    # Include end-session endpoint only if provided; absence is valid.
    end_session = _env("OIDC_OP_END_SESSION_ENDPOINT")
    if end_session:
        settings["OIDC_OP_END_SESSION_ENDPOINT"] = end_session

    return settings


# ---------------------------------------------------------------------------
# Deployment notes
# ---------------------------------------------------------------------------
#
# Add to INSTALLED_APPS (deployment settings.py):
#
#     "mozilla_django_oidc",
#
# Add to MIDDLEWARE *after* AuthenticationMiddleware (deployment settings.py):
#
#     "mozilla_django_oidc.middleware.SessionRefresh",
#
# Add to TEMPLATES context_processors (deployment settings.py):
#
#     "django_ninfo.context_processors.oidc_enabled",
#
# Add to ROOT_URLCONF urls.py (deployment urls.py):
#
#     path("oidc/", include("mozilla_django_oidc.urls")),
#     path("oidc/", include("django_ninfo.oidc_urls")),  # custom logout
#
# Full example — deployment settings.py snippet:
#
#     from django_ninfo.oidc_settings import get_oidc_settings
#
#     _oidc = get_oidc_settings()
#     AUTHENTICATION_BACKENDS = _oidc["AUTHENTICATION_BACKENDS"]
#     LOGIN_URL = _oidc["LOGIN_URL"]
#     locals().update({k: v for k, v in _oidc.items()
#                      if k not in ("AUTHENTICATION_BACKENDS", "LOGIN_URL")})
#
#     INSTALLED_APPS += ["mozilla_django_oidc"]
#
#     idx = MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware")
#     MIDDLEWARE.insert(idx + 1, "mozilla_django_oidc.middleware.SessionRefresh")
#
# ---------------------------------------------------------------------------

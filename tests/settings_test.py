"""
Minimal Django settings for running CombinedQueryView tests.

@decision DEC-QUERY-002
@title Minimal test settings with in-memory SQLite and Token auth
@status accepted
@rationale The django-ninfo package is a reusable app with no top-level project.
  These settings wire up the minimum needed to exercise DRF TokenAuthentication
  and the combined-query endpoint in isolation.
"""
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "rest_framework.authtoken",
    "mozilla_django_oidc",
    "django_ninfo",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "django_ninfo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# mozilla-django-oidc requires these even when OIDC is not actively used
OIDC_RP_CLIENT_ID = "test-client-id"
OIDC_RP_CLIENT_SECRET = "test-client-secret"
OIDC_OP_JWKS_ENDPOINT = "https://example.com/jwks"
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://example.com/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://example.com/token"
OIDC_OP_USER_ENDPOINT = "https://example.com/userinfo"

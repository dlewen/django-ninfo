"""
Template context processors for django-ninfo.

Exposes OIDC_ENABLED to all templates so the login page can conditionally
show the SSO button vs the standard Django login form.

Add to TEMPLATES['OPTIONS']['context_processors'] in deployment settings::

    "django_ninfo.context_processors.oidc_enabled",
"""

from django.conf import settings


def oidc_enabled(request):
    """Inject OIDC_ENABLED flag into template context."""
    return {"OIDC_ENABLED": getattr(settings, "OIDC_ENABLED", False)}

"""
Template context processors for django-ninfo.

Exposes OIDC_ENABLED to all templates so the login page can conditionally
show the SSO button vs the standard Django login form.

Exposes multi-search plugin configuration (default-checked and hidden plugin
lists) so the index template can embed them as JSON for app.js to consume.

Add to TEMPLATES['OPTIONS']['context_processors'] in deployment settings::

    "django_ninfo.context_processors.oidc_enabled",
    "django_ninfo.context_processors.multi_search_config",
"""

from django.conf import settings


def oidc_enabled(request):
    """Inject OIDC_ENABLED flag into template context."""
    return {"OIDC_ENABLED": getattr(settings, "OIDC_ENABLED", False)}


def multi_search_config(request):
    """
    Inject multi-search plugin configuration into template context.

    Provides two lists consumed by the ninfo-config JSON script tag in
    index.html and read by multipleComponent._loadPlugins in app.js:

    - multi_default_plugins: plugins checked by default (empty = all checked)
    - multi_hidden_plugins: plugins hidden entirely from the multi-search UI
    """
    return {
        "multi_default_plugins": getattr(settings, "NINFO_MULTI_DEFAULT_PLUGINS", []),
        "multi_hidden_plugins": getattr(settings, "NINFO_MULTI_HIDDEN_PLUGINS", []),
        "ninfo_mcp_url": getattr(settings, "NINFO_MCP_URL", ""),
        "ninfo_custom_link_label": getattr(settings, "NINFO_CUSTOM_LINK_LABEL", ""),
        "ninfo_custom_link_url": getattr(settings, "NINFO_CUSTOM_LINK_URL", ""),
    }

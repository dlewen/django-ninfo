"""
OIDC utility functions for django-ninfo.

Provides the provider logout URL builder used by mozilla-django-oidc when
OIDC_OP_LOGOUT_URL_METHOD is configured. The function constructs an
RP-initiated logout redirect to the IdP's end_session_endpoint when that
endpoint is configured, enabling single sign-out across all RP sessions.

When OIDC_OP_END_SESSION_ENDPOINT is absent, logout silently falls back to
Django-only session termination — no error is raised.
"""

from django.conf import settings


def provider_logout(request):
    """
    Build the IdP end-session URL for RP-initiated logout.

    Called by mozilla-django-oidc as OIDC_OP_LOGOUT_URL_METHOD.  Returns the
    OIDC provider's end_session_endpoint (if configured) so the browser is
    redirected there after the local Django session is cleared.  When the
    setting is absent, returns an empty string and only the local session is
    destroyed.

    Args:
        request: The current HttpRequest.

    Returns:
        str: The IdP end-session URL, or empty string if not configured.
    """
    end_session_endpoint = getattr(settings, "OIDC_OP_END_SESSION_ENDPOINT", "")
    return end_session_endpoint or ""

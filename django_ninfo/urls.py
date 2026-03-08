"""
URL configuration for the django-ninfo reusable app.

Registers the DRF API endpoints (plugin list, plugin result, extract) plus
the login-required SPA shell view.  OIDC authentication routes are included
unconditionally — mozilla-django-oidc is a hard dependency — but they only
affect behaviour when OIDC is enabled via environment variables.

The deployment project's ROOT_URLCONF must also include:
    path('oidc/', include('mozilla_django_oidc.urls'))
or delegate that responsibility here via the oidc/ prefix below.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.urls import path, re_path, include
from django_ninfo import views

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'plugins', views.PluginViewSet, basename="plugins")

app_name = 'django-ninfo'

urlpatterns = [
    # --- DRF API endpoints ---
    re_path(r'api/plugins/(?P<plugin>\w*)/(?P<format>[a-z]+)/(?P<arg>.*)$', views.PluginResult.as_view()),
    re_path(r'api/plugins/(?P<plugin>\w*)/(?P<arg>.*)$', views.PluginResult.as_view()),
    re_path(r'api/extract', views.Extract.as_view()),
    re_path(r'api/', include(router.urls)),

    # --- SPA shell (login required) ---
    re_path(r'^$', login_required(TemplateView.as_view(template_name='ninfo/index.html')), name='index'),

    # --- OIDC authentication routes ---
    # Provides /oidc/authenticate/, /oidc/callback/, /oidc/logout/ etc.
    # When OIDC is disabled (no env vars), these routes exist but are unused;
    # LOGIN_URL will point to /accounts/login/ instead.
    path('oidc/', include('mozilla_django_oidc.urls')),

    # --- Logout ---
    # Works for both OIDC and standard Django sessions.
    # mozilla-django-oidc's OIDCLogoutView handles OIDC token revocation and
    # RP-initiated logout when OIDC_OP_END_SESSION_ENDPOINT is configured.
    # When OIDC is not active, this falls back to Django's standard LogoutView.
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]

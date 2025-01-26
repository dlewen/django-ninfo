from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.urls import re_path, include
from django_ninfo import views

from rest_framework import routers
router = routers.DefaultRouter()

router.register(r'plugins', views.PluginViewSet, base_name="plugins")

app_name = 'django-ninfo'
urlpatterns = [
    re_path(r'api/plugins/(?P<plugin>\w*)/(?P<format>[a-z]+)/(?P<arg>.*)$', views.PluginResult.as_view()),
    re_path(r'api/plugins/(?P<plugin>\w*)/(?P<arg>.*)$', views.PluginResult.as_view()),
    re_path(r'api/extract', views.Extract.as_view()),
    re_path(r'api/', include(router.urls)),
    re_path(r'^$', login_required(TemplateView.as_view(template_name='ninfo/index.html')), name='index'),
]

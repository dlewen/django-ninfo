from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.urls import url, include
from django_ninfo import views

from rest_framework import routers
router = routers.DefaultRouter()

router.register(r'plugins', views.PluginViewSet, base_name="plugins")

app_name = 'django-ninfo'
urlpatterns = [
    url(r'api/plugins/(?P<plugin>\w*)/(?P<format>[a-z]+)/(?P<arg>.*)$', views.PluginResult.as_view()),
    url(r'api/plugins/(?P<plugin>\w*)/(?P<arg>.*)$', views.PluginResult.as_view()),
    url(r'api/extract', views.Extract.as_view()),
    url(r'api/', include(router.urls)),
    url(r'^$', login_required(TemplateView.as_view(template_name='ninfo/index.html')), name='index'),
]

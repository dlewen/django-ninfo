from django.views.generic.base import RedirectView
from django.conf.urls import patterns, url, include
from django_ninfo import views

from rest_framework import routers
router = routers.DefaultRouter()

router.register(r'plugins', views.PluginViewSet, base_name="plugins")

urlpatterns = patterns('',
    url(r'api/plugins/(?P<plugin>\w*)/(?P<format>[a-z]+)/(?P<arg>.*)$', views.PluginResult.as_view()),
    url(r'api/plugins/(?P<plugin>\w*)/(?P<arg>.*)$', views.PluginResult.as_view()),
    url(r'api/extract', views.Extract.as_view()),
    url(r'api/', include(router.urls)),
    url(r'^$', RedirectView.as_view(url='/static/ninfo/index.html', permanent=False), name='index'),

)

from ninfo import Ninfo, PluginError
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, StaticHTMLRenderer, BaseRenderer

from django.http import Http404

import threading
local_data = threading.local()

def get_info_object():
    if hasattr(local_data, 'info'):
        return local_data.info

    info = Ninfo()
    local_data.info = info
    return info

class PluginViewSet(viewsets.ViewSet):
    """
    Ninfo plugins
    request one of the following urls for plugin result:

        /api/plugins/name/format/argument
        /api/plugins/name/argument

    """
    permission_classes=[IsAuthenticated]
    def list(self, request, format=None):
        P = get_info_object()
        data = plugins = [p.as_json() for p in P.plugins]
        data = {"plugins": plugins}
        return Response(data)


class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'
    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, dict):
            return data["detail"].encode(self.charset)
        return data.encode(self.charset)

mapping = {
    "txt": "get_info_text",
    "html": "get_info_html",
    "json": "get_info_json",
}

class PluginResult(views.APIView):
    permission_classes=[IsAuthenticated]
    #i'm not using renderers, but this needs to be here to allow it to accept the content types
    renderer_classes = (JSONRenderer, StaticHTMLRenderer, PlainTextRenderer)
    def get(self, request, plugin, arg, format="json"):
        P = get_info_object()
        plugin_obj = P.get_plugin(plugin)
        if plugin_obj is None:
            raise Http404
        func = mapping[format]
        try:
            resp = getattr(P, func)(plugin, arg)
        except PluginError as e:
            resp = "Error: %r" % e
        timeout = P.get_plugin(plugin).cache_timeout or 60
        headers = {'Cache-Control':  'max-age=%d' % timeout}
        return Response(resp, headers=headers)


class Extract(views.APIView):
    permission_classes=[IsAuthenticated]
    #i'm not using renderers, but this needs to be here to allow it to accept the content types
    renderer_classes = [JSONRenderer]
    def get(self, request):
        args = request.GET["q"].split()
        resp = {"args": args}
        return Response(resp)

"""
Django views for django-ninfo.

@decision DEC-APIKEY-001
@title DRF TokenAuthentication for per-user API key management
@status accepted
@rationale DRF's built-in Token model provides per-user opaque tokens stored in
the database. ApiKeyView GET returns the existing key (or null if none exists),
POST regenerates it by deleting and recreating the token. This gives users a
deterministic way to rotate credentials without admin intervention.
TokenAuthentication uses the "Authorization: Token <key>" header (not Bearer),
which is DRF convention. SessionAuthentication is also registered in settings
so browser-based requests (with CSRF) continue to work transparently alongside
token auth.
"""
from ninfo import Ninfo, PluginError
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, StaticHTMLRenderer, BaseRenderer
from rest_framework.authtoken.models import Token

from django.http import Http404, HttpResponse

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


class CombinedQueryView(views.APIView):
    """
    Query all compatible ninfo plugins for a given argument and return combined output.

    GET /api/query/<arg>         — plain-text output (default), one section per plugin
    GET /api/query/<arg>.json    — JSON dict {plugin_name: result}

    Optional query parameter:
        ?plugins=shodan,cymruwhois   — comma-separated list of plugin names to run

    Text format mirrors Ninfo.show_info(): each plugin's output is preceded by a
    "*** <title> (<description>) ***" header, matching CLI output for consistency.

    @decision DEC-QUERY-001
    @title CombinedQueryView mirrors show_info() text format
    @status accepted
    @rationale Using the same header format ("*** title (description) ***") as the CLI
    show_info() method ensures text consumers (scripts, MCP tool output) see identical
    structure regardless of whether they call the CLI or the API. JSON format returns
    get_info_dict() directly so callers get structured data without re-parsing text.
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = (JSONRenderer, PlainTextRenderer)

    def get(self, request, arg, format="txt"):
        P = get_info_object()

        # Parse optional plugin filter from query string
        plugins_param = request.query_params.get("plugins")
        plugins = [p.strip() for p in plugins_param.split(",")] if plugins_param else None

        if format == "json":
            data = P.get_info_dict(arg, plugins=plugins)
            return Response(data)

        # Text format: concatenate per-plugin sections with headers.
        # Return HttpResponse directly to bypass DRF content negotiation —
        # an empty string would otherwise be JSON-encoded as '""' by JSONRenderer.
        parts = []
        for plugin_obj, result in P.get_info_iter(arg, plugins=plugins):
            header = "*** %s (%s) ***" % (plugin_obj.title, plugin_obj.description)
            body = plugin_obj.render_template("text", arg, result) or ""
            parts.append(header + "\n" + body)

        text = "\n".join(parts)
        return HttpResponse(text, content_type="text/plain; charset=utf-8")


class Extract(views.APIView):
    permission_classes=[IsAuthenticated]
    #i'm not using renderers, but this needs to be here to allow it to accept the content types
    renderer_classes = [JSONRenderer]
    def get(self, request):
        args = request.GET["q"].split()
        resp = {"args": args}
        return Response(resp)


class ApiKeyView(views.APIView):
    """
    Manage the DRF auth token (API key) for the authenticated user.

    GET  /api/key/  — Returns {"key": "<token>"} or {"key": null} if none exists.
    POST /api/key/  — Deletes any existing token and creates a new one.
                      Returns {"key": "<new-token>"}.

    Requires session or token authentication (IsAuthenticated).
    TokenAuthentication does not enforce CSRF; SessionAuthentication does.
    Browser requests via the navbar UI use SessionAuthentication + CSRF cookie.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            token = Token.objects.get(user=request.user)
            return Response({"key": token.key})
        except Token.DoesNotExist:
            return Response({"key": None})

    def post(self, request):
        # Delete existing token if present, then create a fresh one.
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({"key": token.key})

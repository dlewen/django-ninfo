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
        except Exception as e:
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

    Text format uses markdown headers (## plugin_name) for each plugin section.
    Human-readable and renders well in markdown viewers.

    @decision DEC-QUERY-001
    @title CombinedQueryView with markdown section headers
    @status accepted
    @rationale Markdown ## headers are human-readable in terminals and render nicely
    in markdown-capable tools (MCP clients, documentation). Plugin name only (no
    description) keeps output clean. JSON format returns get_info_dict() directly.
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
            header = "## %s" % plugin_obj.name
            body = plugin_obj.render_template("text", arg, result) or ""
            parts.append(header + "\n\n" + body)

        text = "\n".join(parts)
        return HttpResponse(text, content_type="text/plain; charset=utf-8")


class Extract(views.APIView):
    permission_classes=[IsAuthenticated]
    #i'm not using renderers, but this needs to be here to allow it to accept the content types
    renderer_classes = [JSONRenderer]
    def get(self, request):
        args = request.GET["q"].replace(",", " ").split()
        resp = {"args": args}
        return Response(resp)


class UserInfoView(views.APIView):
    """
    Return basic identity information for the authenticated user.

    GET /api/me/ — Returns {"username": "...", "email": "..."}.

    Used by the MCP server to validate DRF bearer tokens: the MCP server
    calls this endpoint with the user's token and caches the result.

    @decision DEC-ME-001
    @title /api/me/ for MCP token validation
    @status accepted
    @rationale Stateless token validation without exposing user list or admin
    endpoints. MCP server calls GET /api/me/ with Authorization: Token <key>;
    a 200 means the token is valid and returns the username for audit logging.
    DRF's TokenAuthentication handles the token lookup transparently.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "username": request.user.username,
                "email": request.user.email,
            }
        )


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

"""
Tests for CombinedQueryView — GET /api/query/<arg>

Covers:
- Unauthenticated requests return 401
- Text format (default): returns 200 with plugin headers and body
- JSON format (.json suffix): returns 200 with structured dict
- ?plugins= filter: restricts output to named plugins
- Arg with no compatible plugins: returns 200 with empty body / empty dict
- .txt suffix: same as default text format

@decision DEC-QUERY-003
@title Test CombinedQueryView with real Ninfo instance using injected test plugins
@status accepted
@rationale Rather than mocking Ninfo internals, we inject a real Ninfo instance
  pre-loaded with a known test plugin (plug_ip.py). The thread-local
  get_info_object() is patched at the module level so all view calls use the
  controlled instance. This exercises the real get_info_iter / get_info_dict
  code paths without hitting external services.
"""
import importlib
import os
import sys
import pytest

import ninfo
import django_ninfo.views as views_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Wrapper:
    """Mimics importlib entry-point .load() used by Ninfo plugin loading."""
    def __init__(self, module_name):
        self.name = module_name

    def load(self):
        return importlib.import_module(self.name)


def _make_ninfo():
    """Return a Ninfo instance loaded with only the test IP plugin."""
    tests_dir = os.path.dirname(__file__)
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    return ninfo.Ninfo(plugin_modules={"testip": _Wrapper("plug_ip")})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_client(db):
    """Authenticated DRF APIClient with a token for a fresh test user."""
    from django.contrib.auth.models import User
    from rest_framework.authtoken.models import Token
    from rest_framework.test import APIClient

    user = User.objects.create_user(username="testuser", password="testpass")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture()
def anon_client():
    """Unauthenticated DRF APIClient."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture(autouse=True)
def patch_ninfo(monkeypatch):
    """
    Replace get_info_object() with a controlled Ninfo instance for every test.
    Prevents cross-test contamination from the thread-local lazy initialiser.
    """
    test_ninfo = _make_ninfo()
    monkeypatch.setattr(views_module, "get_info_object", lambda: test_ninfo)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCombinedQueryViewAuth:
    def test_unauthenticated_returns_401(self, anon_client):
        resp = anon_client.get("/api/query/1.2.3.4")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCombinedQueryViewText:
    def test_text_format_returns_200(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4")
        assert resp.status_code == 200

    def test_text_format_contains_plugin_header(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Header mirrors show_info() format: *** <title> (<description>) ***
        assert "*** Test IP Plugin (Returns a fixed result for any IP address) ***" in content

    def test_txt_suffix_is_text_format(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.txt")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "*** Test IP Plugin" in content

    def test_hostname_arg_no_compatible_plugins_returns_empty(self, auth_client):
        # testip only handles 'ip' type; a hostname has no compatible plugin
        resp = auth_client.get("/api/query/example.com")
        assert resp.status_code == 200
        assert resp.content.decode().strip() == ""


@pytest.mark.django_db
class TestCombinedQueryViewJson:
    def test_json_suffix_returns_200(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.json")
        assert resp.status_code == 200

    def test_json_suffix_content_type(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.json")
        assert "application/json" in resp["Content-Type"]

    def test_json_suffix_contains_plugin_result(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.json")
        data = resp.json()
        assert "testip" in data
        assert data["testip"]["address"] == "1.2.3.4"
        assert data["testip"]["asn"] == "AS64496"

    def test_json_hostname_no_compatible_plugins_returns_empty_dict(self, auth_client):
        resp = auth_client.get("/api/query/example.com.json")
        assert resp.status_code == 200
        assert resp.json() == {}


@pytest.mark.django_db
class TestCombinedQueryViewPluginsFilter:
    def test_plugins_param_matching_plugin_returns_result(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.json?plugins=testip")
        assert resp.status_code == 200
        data = resp.json()
        assert "testip" in data

    def test_plugins_param_nonexistent_plugin_returns_empty(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4.json?plugins=nosuchplugin")
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_plugins_param_filters_text_output(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4?plugins=testip")
        assert resp.status_code == 200
        assert "*** Test IP Plugin" in resp.content.decode()

    def test_plugins_param_wrong_plugin_no_text_output(self, auth_client):
        resp = auth_client.get("/api/query/1.2.3.4?plugins=nosuchplugin")
        assert resp.status_code == 200
        assert resp.content.decode().strip() == ""

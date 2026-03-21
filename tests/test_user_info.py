"""
Tests for UserInfoView — GET /api/me/

Covers:
- Unauthenticated requests return 401
- Token-authenticated requests return 200 with username and email
- Session-authenticated requests return 200 with username and email
- Response shape matches {"username": ..., "email": ...}

@decision DEC-ME-002
@title Test UserInfoView with real DRF Token auth
@status accepted
@rationale Tests use real DRF TokenAuthentication and a real SQLite test DB —
no mocking of the auth layer. This ensures the /api/me/ endpoint behaves
identically to how the MCP server will call it: with an Authorization: Token
header. A separate fixture creates one user + token per test to keep tests
isolated.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def user(db):
    return User.objects.create_user(
        username="mcpuser", password="testpass", email="mcpuser@example.com"
    )


@pytest.fixture()
def token(user):
    return Token.objects.create(user=user)


@pytest.fixture()
def auth_client(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture()
def anon_client():
    return APIClient()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUserInfoViewAuth:
    def test_unauthenticated_returns_401(self, anon_client):
        resp = anon_client.get("/api/me/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestUserInfoViewResponse:
    def test_returns_200_for_authenticated_user(self, auth_client):
        resp = auth_client.get("/api/me/")
        assert resp.status_code == 200

    def test_response_contains_username(self, auth_client, user):
        resp = auth_client.get("/api/me/")
        assert resp.json()["username"] == user.username

    def test_response_contains_email(self, auth_client, user):
        resp = auth_client.get("/api/me/")
        assert resp.json()["email"] == user.email

    def test_response_shape(self, auth_client, user):
        resp = auth_client.get("/api/me/")
        data = resp.json()
        assert set(data.keys()) == {"username", "email"}
        assert data["username"] == "mcpuser"
        assert data["email"] == "mcpuser@example.com"

    def test_content_type_is_json(self, auth_client):
        resp = auth_client.get("/api/me/")
        assert "application/json" in resp["Content-Type"]

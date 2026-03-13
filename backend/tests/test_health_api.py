from __future__ import annotations

from typing import Any

import pytest
from apps.authz.models import User
from django.db import connection
from django.db.utils import OperationalError
from pytest_django.plugin import DjangoDbBlocker
from rest_framework.test import APIRequestFactory, force_authenticate
from shared.api.urls import urlpatterns as shared_api_urlpatterns


def test_health_endpoint_reports_application_and_database_status(
    client: Any, django_db_blocker: DjangoDbBlocker
) -> None:
    with django_db_blocker.unblock():
        try:
            connection.ensure_connection()
            response = client.get("/api/v1/health/")
        except OperationalError as exc:
            pytest.skip(
                f"Configured PostgreSQL is unavailable for readiness smoke validation: {exc}"
            )

    assert response.status_code == 200
    assert response.json() == {"database": "ok", "service": "backend", "status": "ok"}


def test_health_endpoint_returns_problem_details_when_database_is_unavailable(
    client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_ensure_connection() -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(connection, "ensure_connection", fake_ensure_connection)

    response = client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json() == {
        "code": "service_unavailable",
        "detail": "Database connectivity check failed.",
        "status": 503,
        "title": "A required dependency is unavailable.",
        "type": "urn:dle-saas:error:service_unavailable",
    }


def test_schema_endpoint_requires_authentication(client: Any) -> None:
    response = client.get("/api/v1/schema/")

    assert response.status_code == 403


def test_schema_endpoint_returns_openapi_document_for_authenticated_request() -> None:
    request = APIRequestFactory().get("/api/v1/schema/")
    force_authenticate(request, user=User(username="schema-user"))
    schema_view = next(
        p.callback for p in shared_api_urlpatterns if getattr(p, "name", None) == "schema"
    )

    response = schema_view(request)

    assert response.status_code == 200
    assert response.data["openapi"].startswith("3.")


def test_schema_docs_endpoint_requires_authentication(client: Any) -> None:
    response = client.get("/api/v1/schema/docs/")

    assert response.status_code == 403


def test_schema_docs_endpoint_renders_for_authenticated_request() -> None:
    request = APIRequestFactory().get("/api/v1/schema/docs/")
    force_authenticate(request, user=User(username="swagger-user"))
    schema_docs_view = next(
        p.callback for p in shared_api_urlpatterns if getattr(p, "name", None) == "schema-docs"
    )

    response = schema_docs_view(request)
    response.render()

    assert response.status_code == 200
    assert "swagger-ui" in response.content.decode()

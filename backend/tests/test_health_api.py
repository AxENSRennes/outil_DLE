from __future__ import annotations

from typing import Any

import pytest
from django.db import connection
from django.db.utils import OperationalError
from pytest_django.plugin import DjangoDbBlocker


def test_health_endpoint_reports_application_and_database_status(
    client: Any, django_db_blocker: DjangoDbBlocker
) -> None:
    with django_db_blocker.unblock():
        try:
            connection.ensure_connection()
            response = client.get("/api/v1/health/")
        except OperationalError as exc:
            pytest.skip(
                "Configured PostgreSQL is unavailable for readiness smoke validation: "
                f"{exc}"
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

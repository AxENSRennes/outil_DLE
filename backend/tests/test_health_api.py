from __future__ import annotations

from typing import Any

import pytest


def test_health_endpoint_reports_application_and_database_status(
    client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.db import connection

    def fake_ensure_connection() -> None:
        return None

    monkeypatch.setattr(connection, "ensure_connection", fake_ensure_connection)

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"database": "ok", "service": "backend", "status": "ok"}

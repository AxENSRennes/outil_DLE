from __future__ import annotations

from typing import Any

from rest_framework.test import APIClient


def csrf_client(*, user: Any | None = None) -> tuple[APIClient, str]:
    client = APIClient(enforce_csrf_checks=True)
    client.get("/admin/login/")
    if user is not None:
        client.force_login(user)
    token = client.cookies["csrftoken"].value
    return client, token


def post_json(client: APIClient, path: str, payload: dict[str, Any], *, csrf_token: str) -> Any:
    return client.post(
        path,
        payload,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

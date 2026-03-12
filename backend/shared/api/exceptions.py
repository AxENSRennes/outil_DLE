from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def problem_details_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)

    if response is None:
        return None

    title = "Request failed"
    if isinstance(exc, APIException):
        title = exc.default_detail if isinstance(exc.default_detail, str) else title

    detail = response.data
    if isinstance(detail, dict):
        normalized_detail: Any = detail.get("detail", detail)
    else:
        normalized_detail = detail

    response.data = {
        "type": "about:blank",
        "title": title,
        "status": response.status_code,
        "detail": normalized_detail,
    }
    return response


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "A required dependency is unavailable."
    default_code = "service_unavailable"

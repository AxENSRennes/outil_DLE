from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _problem_type_for_code(code: Any) -> str:
    if isinstance(code, str):
        return f"urn:dle-saas:error:{code}"
    return "about:blank"


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

    error_code: Any = exc.get_codes() if isinstance(exc, APIException) else None

    response.data = {
        "type": _problem_type_for_code(error_code),
        "title": title,
        "status": response.status_code,
        "detail": normalized_detail,
    }
    if error_code is not None:
        response.data["code"] = error_code
    return response


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "A required dependency is unavailable."
    default_code = "service_unavailable"


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicted with a concurrent operation."
    default_code = "conflict"


class UnprocessableEntity(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The request could not be processed."
    default_code = "unprocessable_entity"

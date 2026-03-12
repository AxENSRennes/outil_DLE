from __future__ import annotations

from typing import ClassVar

from django.db import connection
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.api.exceptions import ServiceUnavailable


class HealthCheckView(APIView):
    authentication_classes: ClassVar[list[type]] = []
    permission_classes: ClassVar[list[type]] = []

    def get(self, request: HttpRequest) -> Response:
        try:
            connection.ensure_connection()
        except Exception as exc:
            raise ServiceUnavailable("Database connectivity check failed.") from exc

        return Response(
            {"database": "ok", "service": "backend", "status": "ok"},
            status=status.HTTP_200_OK,
        )

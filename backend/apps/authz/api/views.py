from __future__ import annotations

from typing import Any, ClassVar, cast

from django.http import HttpRequest
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authz.api.serializers import AuthContextSerializer
from apps.authz.models import User
from apps.authz.selectors.access_context import list_site_access_contexts


class AuthContextView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated]

    def get(self, request: HttpRequest) -> Response:
        user = cast(User, request.user)
        payload: dict[str, Any] = {
            "user": {
                "id": user.id,
                "username": user.get_username(),
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "site_assignments": [
                {
                    "site": {
                        "id": access.site_id,
                        "code": access.site_code,
                        "name": access.site_name,
                    },
                    "roles": list(access.roles),
                }
                for access in list_site_access_contexts(user)
            ],
        }
        serializer = AuthContextSerializer(payload)
        return Response(serializer.data)

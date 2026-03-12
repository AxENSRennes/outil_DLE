from __future__ import annotations

from typing import Any, ClassVar, cast

from django.http import HttpRequest
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission, get_active_site_by_code

from apps.authz.api.serializers import AuthContextSerializer, SiteRoleAccessProbeSerializer
from apps.authz.models import SiteRole, User
from apps.authz.selectors.access_context import list_site_access_contexts
from apps.sites.models import Site


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


class OperatorSiteAccessProbeView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.OPERATOR,)
    site_lookup_kwarg = "site_code"

    def get_site(self) -> Site:
        existing_site = getattr(self, "site", None)
        if isinstance(existing_site, Site):
            return existing_site

        # SiteScopedRolePermission may populate self.site during has_permission(),
        # but the view resolves and caches it directly as well.
        site = get_active_site_by_code(self.kwargs["site_code"])
        self.site = site
        return site

    def get(self, request: HttpRequest, site_code: str) -> Response:
        site = self.get_site()
        payload = {
            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
            },
            "required_role": SiteRole.OPERATOR,
            "status": "authorized",
        }
        serializer = SiteRoleAccessProbeSerializer(payload)
        return Response(serializer.data)

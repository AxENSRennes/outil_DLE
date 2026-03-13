from __future__ import annotations

from typing import ClassVar, cast

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission, get_active_site_by_code

from apps.authz.api.serializers import (
    AuthContextSerializer,
    SignatureReauthRequestSerializer,
    SignatureReauthResponseSerializer,
    SiteRoleAccessProbeSerializer,
    WorkstationIdentifyRequestSerializer,
    WorkstationIdentifyResponseSerializer,
    WorkstationLockResponseSerializer,
)
from apps.authz.api.throttles import (
    SignatureReauthThrottle,
    WorkstationIdentifyThrottle,
    WorkstationLockThrottle,
)
from apps.authz.domain.workstation import (
    build_auth_context_payload,
    identify_workstation_user,
    lock_workstation,
    reauthenticate_signature_authority,
)
from apps.authz.models import SiteRole, User
from apps.sites.models import Site


class AuthContextView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        payload = build_auth_context_payload(user)
        serializer = AuthContextSerializer(payload)
        return Response(serializer.data)


@method_decorator(csrf_protect, name="dispatch")
class WorkstationIdentifyView(APIView):
    permission_classes: ClassVar[list[type]] = [AllowAny]
    throttle_classes: ClassVar[list[type]] = [WorkstationIdentifyThrottle]

    @extend_schema(
        request=WorkstationIdentifyRequestSerializer,
        responses=WorkstationIdentifyResponseSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = WorkstationIdentifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = identify_workstation_user(
            request,
            username=serializer.validated_data["username"],
            pin=serializer.validated_data["pin"],
        )
        response_serializer = WorkstationIdentifyResponseSerializer(payload)
        return Response(response_serializer.data)


@method_decorator(csrf_protect, name="dispatch")
class WorkstationLockView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated]
    throttle_classes: ClassVar[list[type]] = [WorkstationLockThrottle]

    @extend_schema(
        request=None,
        responses=WorkstationLockResponseSerializer,
    )
    def post(self, request: Request) -> Response:
        payload = lock_workstation(request)
        serializer = WorkstationLockResponseSerializer(payload)
        return Response(serializer.data)


@method_decorator(csrf_protect, name="dispatch")
class SignatureReauthView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated]
    throttle_classes: ClassVar[list[type]] = [SignatureReauthThrottle]

    @extend_schema(
        request=SignatureReauthRequestSerializer,
        responses=SignatureReauthResponseSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = SignatureReauthRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = reauthenticate_signature_authority(
            request,
            user=cast(User, request.user),
            site_code=serializer.validated_data["site_code"],
            required_roles=tuple(serializer.validated_data["required_roles"]),
            pin=serializer.validated_data["pin"],
        )
        response_serializer = SignatureReauthResponseSerializer(payload)
        return Response(response_serializer.data)


@method_decorator(csrf_protect, name="dispatch")
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

    def get(self, request: Request, site_code: str) -> Response:
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

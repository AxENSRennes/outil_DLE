from __future__ import annotations

from typing import ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.domain.policies import get_active_site_role_assignments
from apps.authz.models import SiteRole
from apps.mmr.api.serializers import (
    MMRCreateSerializer,
    MMRDetailSerializer,
    MMRListSerializer,
    MMRVersionCreateSerializer,
    MMRVersionDetailSerializer,
    MMRVersionListSerializer,
)
from apps.mmr.domain.mmr_service import create_mmr
from apps.mmr.domain.version_lifecycle import create_draft_version
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site


class MMRListCreateView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.INTERNAL_CONFIGURATOR,)
    allow_object_level_site_resolve = True

    @extend_schema(responses=MMRListSerializer(many=True))
    def get(self, request: Request) -> Response:
        authorized_site_ids = get_active_site_role_assignments(
            request.user
        ).filter(
            role__in=[str(r) for r in self.required_site_roles],
        ).values_list("site_id", flat=True)
        mmrs = MMR.objects.filter(site_id__in=authorized_site_ids).select_related(
            "site", "product"
        )
        serializer = MMRListSerializer(mmrs, many=True)
        return Response(serializer.data)

    @method_decorator(csrf_protect)
    @extend_schema(request=MMRCreateSerializer, responses=MMRDetailSerializer)
    def post(self, request: Request) -> Response:
        serializer = MMRCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        site = Site.objects.filter(pk=data["site_id"], is_active=True).first()
        if site is None:
            return Response(
                {"type": "validation_error", "title": "Invalid site", "detail": "Site not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check role on target site
        self.site = site
        self.check_permissions(request)

        product = Product.objects.filter(pk=data["product_id"], site=site, is_active=True).first()
        if product is None:
            return Response(
                {
                    "type": "validation_error",
                    "title": "Invalid product",
                    "detail": "Product not found for this site.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mmr = create_mmr(
                site=site,
                product=product,
                name=data["name"],
                code=data["code"],
                description=data["description"],
                actor=request.user,
            )
        except ValueError as exc:
            return Response(
                {"type": "validation_error", "title": "Duplicate MMR code", "detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        response_serializer = MMRDetailSerializer(mmr)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_site_for_object(self, obj: MMR) -> Site:
        return obj.site


class MMRDetailView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.INTERNAL_CONFIGURATOR,)
    allow_object_level_site_resolve = True

    @extend_schema(responses=MMRDetailSerializer)
    def get(self, request: Request, mmr_id: int) -> Response:
        mmr = MMR.objects.select_related("site", "product").filter(pk=mmr_id).first()
        if mmr is None:
            return Response(
                {"type": "not_found", "title": "Not found", "detail": "MMR not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.site = mmr.site
        self.check_permissions(request)
        serializer = MMRDetailSerializer(mmr)
        return Response(serializer.data)

    def get_site_for_object(self, obj: MMR) -> Site:
        return obj.site


class MMRVersionListCreateView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.INTERNAL_CONFIGURATOR,)
    allow_object_level_site_resolve = True

    def _get_mmr(self, mmr_id: int) -> MMR | None:
        return MMR.objects.select_related("site").filter(pk=mmr_id).first()

    @extend_schema(responses=MMRVersionListSerializer(many=True))
    def get(self, request: Request, mmr_id: int) -> Response:
        mmr = self._get_mmr(mmr_id)
        if mmr is None:
            return Response(
                {"type": "not_found", "title": "Not found", "detail": "MMR not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.site = mmr.site
        self.check_permissions(request)
        versions = MMRVersion.objects.filter(mmr=mmr).select_related("created_by")
        serializer = MMRVersionListSerializer(versions, many=True)
        return Response(serializer.data)

    @method_decorator(csrf_protect)
    @extend_schema(
        request=MMRVersionCreateSerializer, responses=MMRVersionDetailSerializer
    )
    def post(self, request: Request, mmr_id: int) -> Response:
        mmr = self._get_mmr(mmr_id)
        if mmr is None:
            return Response(
                {"type": "not_found", "title": "Not found", "detail": "MMR not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.site = mmr.site
        self.check_permissions(request)

        serializer = MMRVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version = create_draft_version(
            mmr=mmr,
            actor=request.user,
            change_summary=serializer.validated_data["change_summary"],
        )
        response_serializer = MMRVersionDetailSerializer(version)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_site_for_object(self, obj: object) -> Site:
        if isinstance(obj, MMR):
            return obj.site
        if isinstance(obj, MMRVersion):
            return obj.mmr.site
        raise ValueError("Unexpected object type")


class MMRVersionDetailView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.INTERNAL_CONFIGURATOR,)
    allow_object_level_site_resolve = True

    @extend_schema(responses=MMRVersionDetailSerializer)
    def get(self, request: Request, mmr_id: int, version_id: int) -> Response:
        version = (
            MMRVersion.objects.select_related("mmr__site", "created_by", "activated_by")
            .filter(pk=version_id, mmr_id=mmr_id)
            .first()
        )
        if version is None:
            return Response(
                {"type": "not_found", "title": "Not found", "detail": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.site = version.mmr.site
        self.check_permissions(request)
        serializer = MMRVersionDetailSerializer(version)
        return Response(serializer.data)

    def get_site_for_object(self, obj: MMRVersion) -> Site:
        return obj.mmr.site

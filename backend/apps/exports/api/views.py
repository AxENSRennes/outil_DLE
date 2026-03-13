from __future__ import annotations

from typing import ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.api.exceptions import Conflict, UnprocessableEntity
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole
from apps.batches.models import Batch
from apps.exports.api.serializers import DossierStructureSerializer
from apps.exports.domain.composition import (
    DossierCompositionError,
    resolve_dossier_structure,
)
from apps.exports.selectors.dossier_structure import get_batch_dossier_structure
from apps.sites.models import Site


class BatchDossierStructureView(APIView):
    """GET the resolved dossier structure for a batch."""

    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]
    required_site_roles = (
        SiteRole.OPERATOR,
        SiteRole.PRODUCTION_REVIEWER,
        SiteRole.QUALITY_REVIEWER,
    )

    def get_site(self) -> Site:
        try:
            batch = Batch.objects.select_related("site").get(pk=self.kwargs["batch_id"])
        except Batch.DoesNotExist:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from None
        return batch.site

    @extend_schema(
        responses=DossierStructureSerializer,
        summary="Retrieve the resolved dossier structure for a batch.",
    )
    def get(self, request: Request, batch_id: int) -> Response:
        structure = get_batch_dossier_structure(batch_id)
        if structure is None:
            raise NotFound(
                detail="No resolved dossier structure for this batch.",
                code="dossier_structure_not_found",
            )

        serializer = DossierStructureSerializer(structure)
        return Response(serializer.data)


@method_decorator(csrf_protect, name="dispatch")
class ResolveBatchDossierView(APIView):
    """POST to trigger dossier composition for a batch."""

    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]
    required_site_roles = (
        SiteRole.OPERATOR,
        SiteRole.PRODUCTION_REVIEWER,
        SiteRole.QUALITY_REVIEWER,
    )

    def get_site(self) -> Site:
        try:
            batch = Batch.objects.select_related("site", "mmr_version").get(
                pk=self.kwargs["batch_id"],
            )
        except Batch.DoesNotExist:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from None
        self._batch = batch
        return batch.site

    @extend_schema(
        request=None,
        responses=DossierStructureSerializer,
        parameters=[
            OpenApiParameter(
                name="force",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="If true, deactivate the existing structure and resolve a fresh one.",
            ),
        ],
        summary="Resolve (or return existing) dossier structure for a batch.",
    )
    def post(self, request: Request, batch_id: int) -> Response:
        batch = getattr(self, "_batch", None)
        if batch is None or batch.pk != batch_id:
            try:
                batch = Batch.objects.select_related("mmr_version").get(pk=batch_id)
            except Batch.DoesNotExist:
                raise NotFound(detail="Batch not found.", code="batch_not_found") from None

        force = request.query_params.get("force", "").lower() == "true"

        try:
            resolve_dossier_structure(batch, force=force, actor=request.user, site=self.site)
        except DossierCompositionError as exc:
            raise UnprocessableEntity(detail=str(exc), code="composition_error") from exc

        read_model = get_batch_dossier_structure(batch_id)
        if read_model is None:
            raise Conflict(
                detail="Dossier structure was modified by a concurrent request. Please retry.",
                code="dossier_structure_race",
            )
        serializer = DossierStructureSerializer(read_model)
        return Response(serializer.data)

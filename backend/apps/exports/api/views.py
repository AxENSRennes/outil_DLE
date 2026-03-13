from __future__ import annotations

from typing import ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.batches.models import Batch
from apps.exports.api.serializers import DossierStructureSerializer
from apps.exports.domain.composition import (
    DossierCompositionError,
    resolve_dossier_structure,
)
from apps.exports.selectors.dossier_structure import get_batch_dossier_structure


class BatchDossierStructureView(APIView):
    """GET the resolved dossier structure for a batch."""

    permission_classes: ClassVar[list[type]] = [IsAuthenticated]

    @extend_schema(
        responses=DossierStructureSerializer,
        summary="Retrieve the resolved dossier structure for a batch.",
    )
    def get(self, request: Request, batch_id: int) -> Response:
        if not Batch.objects.filter(pk=batch_id).exists():
            raise NotFound(detail="Batch not found.", code="batch_not_found")

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

    permission_classes: ClassVar[list[type]] = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses=DossierStructureSerializer,
        summary="Resolve (or return existing) dossier structure for a batch.",
    )
    def post(self, request: Request, batch_id: int) -> Response:
        try:
            batch = Batch.objects.select_related("mmr_version").get(pk=batch_id)
        except Batch.DoesNotExist:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from None

        try:
            resolve_dossier_structure(batch)
        except DossierCompositionError as exc:
            return Response(
                {"type": "composition_error", "detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        read_model = get_batch_dossier_structure(batch_id)
        serializer = DossierStructureSerializer(read_model)
        return Response(serializer.data, status=status.HTTP_200_OK)

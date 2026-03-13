from __future__ import annotations

from collections import OrderedDict
from typing import Any, ClassVar

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole
from apps.batches.api.serializers import (
    BatchDocumentRequirementSerializer,
    BatchStepSerializer,
    CompositionResponseSerializer,
    StepGroupSerializer,
)
from apps.batches.domain.composition import CompositionError, generate_repeated_controls
from apps.batches.domain.occurrences import OccurrenceError, add_occurrence
from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
)


def _get_batch_or_404(batch_id: int) -> Batch:
    try:
        return Batch.objects.get(pk=batch_id)
    except Batch.DoesNotExist as exc:
        from rest_framework.exceptions import NotFound

        raise NotFound(detail=f"Batch with id {batch_id} not found.") from exc


class BatchSiteMixin:
    """Resolve site from batch_id URL kwarg for SiteScopedRolePermission."""

    required_site_roles = (
        SiteRole.OPERATOR,
        SiteRole.PRODUCTION_REVIEWER,
        SiteRole.QUALITY_REVIEWER,
        SiteRole.INTERNAL_CONFIGURATOR,
    )
    _batch: Batch

    def get_site(self) -> Any:
        return self.get_batch().site

    def get_batch(self) -> Batch:
        if hasattr(self, "_batch"):
            return self._batch
        batch = _get_batch_or_404(self.kwargs["batch_id"])  # type: ignore[attr-defined]
        self._batch = batch
        return batch


@method_decorator(csrf_protect, name="dispatch")
class BatchComposeView(BatchSiteMixin, APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]

    @extend_schema(
        request=None,
        responses=CompositionResponseSerializer,
    )
    def post(self, request: Request, batch_id: int) -> Response:
        batch = self.get_batch()
        try:
            created_steps = generate_repeated_controls(batch)
        except CompositionError as e:
            return Response(
                {
                    "type": "urn:dle-saas:error:composition_error",
                    "title": "Composition failed",
                    "status": 400,
                    "detail": str(e),
                    "code": "composition_error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_count = BatchDocumentRequirement.objects.filter(batch=batch).count()
        payload = {
            "batch_id": batch.pk,
            "batch_number": batch.batch_number,
            "steps_created": len(created_steps),
            "document_requirements_created": doc_count,
        }
        serializer = CompositionResponseSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class BatchAddOccurrenceView(BatchSiteMixin, APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]

    @extend_schema(
        request=None,
        responses=BatchStepSerializer,
    )
    def post(
        self, request: Request, batch_id: int, step_key: str
    ) -> Response:
        batch = self.get_batch()
        try:
            new_step = add_occurrence(batch, step_key)
        except OccurrenceError as e:
            return Response(
                {
                    "type": "urn:dle-saas:error:occurrence_error",
                    "title": "Add occurrence failed",
                    "status": 400,
                    "detail": str(e),
                    "code": "occurrence_error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BatchStepSerializer(new_step)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BatchStepsListView(BatchSiteMixin, APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]

    @extend_schema(
        responses=StepGroupSerializer(many=True),
    )
    def get(self, request: Request, batch_id: int) -> Response:
        batch = self.get_batch()
        steps = BatchStep.objects.filter(batch=batch).order_by("sequence_order")

        # Prefetch doc requirements in one query
        doc_reqs_map = {
            dr.document_code: dr
            for dr in BatchDocumentRequirement.objects.filter(batch=batch)
        }

        # Group by step_key preserving order
        groups: OrderedDict[str, dict[str, Any]] = OrderedDict()
        for step in steps:
            if step.step_key not in groups:
                doc_req = doc_reqs_map.get(step.step_key)
                groups[step.step_key] = {
                    "step_key": step.step_key,
                    "title": step.title,
                    "repeat_mode": doc_req.repeat_mode if doc_req else "single",
                    "is_applicable": step.is_applicable,
                    "occurrences": [],
                }
            groups[step.step_key]["occurrences"].append(step)

        serializer = StepGroupSerializer(list(groups.values()), many=True)
        return Response(serializer.data)


class BatchDocumentRequirementsListView(BatchSiteMixin, APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]

    @extend_schema(
        responses=BatchDocumentRequirementSerializer(many=True),
    )
    def get(self, request: Request, batch_id: int) -> Response:
        batch = self.get_batch()
        doc_reqs = BatchDocumentRequirement.objects.filter(batch=batch).order_by(
            "document_code"
        )
        serializer = BatchDocumentRequirementSerializer(doc_reqs, many=True)
        return Response(serializer.data)

from __future__ import annotations

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
    BatchStepSerializer,
    BatchSummarySerializer,
    CompositionResponseSerializer,
    DocumentRequirementReadModelSerializer,
    StepGroupSerializer,
)
from apps.batches.domain.composition import (
    CompositionError,
    generate_repeated_controls,
)
from apps.batches.domain.occurrences import OccurrenceError, add_occurrence
from apps.batches.models import Batch
from apps.batches.selectors.completeness import (
    get_document_requirement_completeness,
    get_grouped_steps,
)


def _get_batch_or_404(batch_id: int) -> Batch:
    try:
        return Batch.objects.get(pk=batch_id)
    except Batch.DoesNotExist as exc:
        from rest_framework.exceptions import NotFound

        raise NotFound(detail=f"Batch with id {batch_id} not found.") from exc


def _problem_response(
    *,
    code: str,
    detail: str,
    title: str,
    status_code: int,
) -> Response:
    return Response(
        {
            "type": f"urn:dle-saas:error:{code}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "code": code,
        },
        status=status_code,
    )


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
            result = generate_repeated_controls(batch)
        except CompositionError as e:
            return _problem_response(
                code=e.code,
                detail=e.detail,
                title="Composition failed",
                status_code=e.status_code,
            )

        step_groups = get_grouped_steps(batch)
        document_requirements = get_document_requirement_completeness(batch)
        payload = {
            "batch": BatchSummarySerializer(batch).data,
            "steps_created": len(result.created_steps),
            "document_requirements_created": result.document_requirements_created,
            "step_groups": step_groups,
            "document_requirements": document_requirements,
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
    def post(self, request: Request, batch_id: int, step_key: str) -> Response:
        batch = self.get_batch()
        try:
            new_step = add_occurrence(batch, step_key)
        except OccurrenceError as e:
            return _problem_response(
                code=e.code,
                detail=e.detail,
                title="Add occurrence failed",
                status_code=e.status_code,
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
        serializer = StepGroupSerializer(get_grouped_steps(batch), many=True)
        return Response(serializer.data)


class BatchDocumentRequirementsListView(BatchSiteMixin, APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]

    @extend_schema(
        responses=DocumentRequirementReadModelSerializer(many=True),
    )
    def get(self, request: Request, batch_id: int) -> Response:
        batch = self.get_batch()
        serializer = DocumentRequirementReadModelSerializer(
            get_document_requirement_completeness(batch),
            many=True,
        )
        return Response(serializer.data)

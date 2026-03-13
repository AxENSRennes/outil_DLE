from __future__ import annotations

from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.authz.models import SiteRole
from apps.batches.api.serializers import BatchExecutionSerializer, BatchStepDetailSerializer
from apps.batches.models import Batch, BatchStep
from apps.batches.selectors.execution import get_batch_execution_payload, get_step_detail_payload
from apps.sites.models import Site


class BatchExecutionView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (
        SiteRole.OPERATOR,
        SiteRole.PRODUCTION_REVIEWER,
        SiteRole.QUALITY_REVIEWER,
    )
    allow_object_level_site_resolve = True

    def _get_batch(self, batch_id: int) -> Batch:
        batch = (
            Batch.objects.select_related("site")
            .prefetch_related("steps")
            .filter(id=batch_id)
            .first()
        )
        if batch is None:
            raise NotFound(detail="Batch not found.", code="batch_not_found")
        return batch

    @extend_schema(
        responses=BatchExecutionSerializer,
        operation_id="batch_execution_retrieve",
    )
    def get(self, request: Request, batch_id: int) -> Response:
        batch = self._get_batch(batch_id)
        self.check_object_permissions(request, batch)
        record_audit_event(
            AuditEventType.BATCH_EXECUTION_VIEWED,
            actor=request.user,
            site=batch.site,
            target_type="Batch",
            target_id=batch.id,
            metadata={"batch_number": batch.batch_number},
        )
        payload = get_batch_execution_payload(batch)
        serializer = BatchExecutionSerializer(payload)
        return Response(serializer.data)


class BatchStepDetailView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (
        SiteRole.OPERATOR,
        SiteRole.PRODUCTION_REVIEWER,
        SiteRole.QUALITY_REVIEWER,
    )
    allow_object_level_site_resolve = True

    def get_site_for_object(self, obj: BatchStep) -> Site:
        return obj.batch.site

    def _get_step(self, step_id: int) -> BatchStep:
        step = BatchStep.objects.select_related("batch__site").filter(id=step_id).first()
        if step is None:
            raise NotFound(detail="Batch step not found.", code="batch_step_not_found")
        return step

    @extend_schema(
        responses=BatchStepDetailSerializer,
        operation_id="batch_step_detail_retrieve",
    )
    def get(self, request: Request, step_id: int) -> Response:
        step = self._get_step(step_id)
        self.check_object_permissions(request, step)
        record_audit_event(
            AuditEventType.BATCH_STEP_VIEWED,
            actor=request.user,
            site=step.batch.site,
            target_type="BatchStep",
            target_id=step.id,
            metadata={"step_key": step.step_key, "batch_id": step.batch_id},
        )
        payload = get_step_detail_payload(step)
        serializer = BatchStepDetailSerializer(payload)
        return Response(serializer.data)

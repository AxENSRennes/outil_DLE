from __future__ import annotations

from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.http import get_client_ip
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole
from apps.batches.api.serializers import (
    CorrectionRequestSerializer,
    CorrectionResponseSerializer,
)
from apps.batches.domain.corrections import submit_correction
from apps.batches.models import BatchStep
from apps.sites.models import Site


class SubmitCorrectionView(APIView):
    """Submit a controlled correction to a batch step's data.

    Creates an attributed, justified correction event rather than
    silently replacing prior values.  Returns 404 for missing
    resources *and* for authorization failures (fail-closed, no
    enumeration).
    """

    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.OPERATOR, SiteRole.PRODUCTION_REVIEWER)
    allow_object_level_site_resolve = True

    def get_authenticate_header(self, request: Request) -> str:
        return "Session"

    def permission_denied(
        self,
        request: Request,
        message: str | None = None,
        code: str | None = None,
    ) -> None:
        if not request.successful_authenticator and not request.user.is_authenticated:
            raise NotAuthenticated(
                detail="Authentication credentials were not provided.",
                code="not_authenticated",
            )
        super().permission_denied(request, message=message, code=code)

    def get_object(self) -> BatchStep:
        try:
            step = BatchStep.objects.select_related("batch__site").get(pk=self.kwargs["step_id"])
        except BatchStep.DoesNotExist:
            raise NotFound(detail="Step not found.", code="step_not_found") from None
        try:
            self.check_object_permissions(self.request, step)
        except (PermissionDenied, NotFound) as exc:
            raise NotFound(detail="Step not found.", code="step_not_found") from exc
        return step

    def get_site_for_object(self, obj: BatchStep) -> Site:
        return obj.batch.site

    @extend_schema(
        request=CorrectionRequestSerializer,
        responses={201: CorrectionResponseSerializer},
        summary="Submit a batch step correction",
        description=(
            "Submit a controlled correction to a batch step's data with a "
            "required reason for change. Creates an attributed audit event "
            "that captures old and new values for traceability."
        ),
    )
    def post(self, request: Request, step_id: int) -> Response:
        step = self.get_object()

        serializer = CorrectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            audit_event = submit_correction(
                step=step,
                actor=request.user,
                corrections=serializer.validated_data["corrections"],
                reason_for_change=serializer.validated_data["reason_for_change"],
                ip_address=get_client_ip(request),
            )
        except ValueError as exc:
            raise ValidationError(detail=str(exc), code="correction_rejected") from exc

        response_data = {
            "correction_id": audit_event.pk,
            "step_id": step.pk,
            "corrected_at": audit_event.occurred_at,
            "corrected_by": audit_event.actor_id,
            "corrections_applied": audit_event.metadata["corrections"],
            "reason_for_change": audit_event.metadata["reason_for_change"],
        }

        response_serializer = CorrectionResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

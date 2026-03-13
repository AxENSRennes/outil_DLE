"""API views for pre-QA review actions.

Provides endpoints for confirming pre-QA handoff and marking
individual flagged steps as reviewed.
"""

from __future__ import annotations

from typing import ClassVar

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole
from apps.batches.models import Batch, BatchStep
from apps.reviews.api.serializers_pre_qa import (
    ConfirmPreQaReviewRequestSerializer,
    MarkStepReviewedRequestSerializer,
    MarkStepReviewedResponseSerializer,
    PreQaReviewConfirmationSerializer,
)
from apps.reviews.domain.pre_qa_review import confirm_pre_qa_review, mark_step_reviewed
from apps.sites.models import Site


class _PreQaBaseView(APIView):
    """Shared base for pre-QA review views.

    Provides fail-closed batch resolution and site-scoped permission
    enforcement for the PRODUCTION_REVIEWER role.
    """

    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.PRODUCTION_REVIEWER,)
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

    def get_batch(self) -> Batch:
        batch_id = self.kwargs["batch_id"]
        try:
            batch = Batch.objects.select_related("site").get(pk=batch_id)
        except Batch.DoesNotExist:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from None
        try:
            self.check_object_permissions(self.request, batch)
        except (PermissionDenied, NotFound) as exc:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from exc
        return batch

    def get_site_for_object(self, obj: Batch) -> Site:
        return obj.site


class ConfirmPreQaReviewView(_PreQaBaseView):
    """Confirm pre-QA review and handoff batch to quality.

    POST /api/v1/batches/{batch_id}/pre-qa-review/confirm
    """

    @extend_schema(
        request=ConfirmPreQaReviewRequestSerializer,
        responses={200: PreQaReviewConfirmationSerializer},
        summary="Confirm pre-QA review",
        description=(
            "Confirms that a batch has passed pre-QA review and is ready "
            "for quality handoff. Transitions batch status to "
            "awaiting_quality_review. Blocked when severity is red."
        ),
    )
    def post(self, request: Request, batch_id: int) -> Response:
        batch = self.get_batch()

        request_serializer = ConfirmPreQaReviewRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        note = request_serializer.validated_data.get("note", "")

        try:
            result = confirm_pre_qa_review(
                batch=batch,
                reviewer=request.user,
                note=note,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(
                detail=exc.message,
                code=exc.code,
            ) from exc

        response_data = {
            "batch_id": result.batch.pk,
            "batch_reference": result.batch.reference,
            "batch_status": result.batch.status,
            "confirmed_at": result.review_event.occurred_at,
            "reviewer_note": note,
        }
        response_serializer = PreQaReviewConfirmationSerializer(response_data)
        return Response(response_serializer.data)


class MarkStepReviewedView(_PreQaBaseView):
    """Mark a flagged step as reviewed during pre-QA.

    POST /api/v1/batches/{batch_id}/review-items/{step_id}/mark-reviewed
    """

    @extend_schema(
        request=MarkStepReviewedRequestSerializer,
        responses={200: MarkStepReviewedResponseSerializer},
        summary="Mark step as reviewed",
        description=(
            "Marks a flagged batch step as reviewed, clearing "
            "changed_since_review and review_required flags. "
            "Transitions batch to in_pre_qa_review if currently "
            "awaiting_pre_qa."
        ),
    )
    def post(self, request: Request, batch_id: int, step_id: int) -> Response:
        batch = self.get_batch()

        try:
            step = BatchStep.objects.get(pk=step_id, batch_id=batch.pk)
        except BatchStep.DoesNotExist:
            raise NotFound(
                detail="Step not found.", code="step_not_found"
            ) from None

        request_serializer = MarkStepReviewedRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        note = request_serializer.validated_data.get("note", "")

        try:
            result = mark_step_reviewed(
                batch=batch,
                step=step,
                reviewer=request.user,
                note=note,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(
                detail=exc.message,
                code=exc.code,
            ) from exc

        response_data = {
            "step_id": result.step.pk,
            "step_reference": result.step.reference,
            "review_status": "reviewed",
            "flags_cleared": list(result.flags_cleared),
            "batch_status": result.batch_status,
        }
        response_serializer = MarkStepReviewedResponseSerializer(response_data)
        return Response(response_serializer.data)

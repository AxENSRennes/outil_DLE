from __future__ import annotations

import dataclasses
from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole
from apps.batches.models import Batch
from apps.reviews.api.serializers import ReviewSummarySerializer
from apps.reviews.selectors.review_summary import get_batch_review_summary
from apps.sites.models import Site


class ReviewSummaryView(APIView):
    """Return a review-oriented completeness summary for a batch.

    Accessible to production_reviewer and quality_reviewer roles scoped
    to the batch's site.  Returns 404 for missing batches *and* for
    unauthorized access (fail-closed, no enumeration).
    """

    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.PRODUCTION_REVIEWER, SiteRole.QUALITY_REVIEWER)
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

    def get_object(self) -> Batch:
        batch_id = self.kwargs["batch_id"]
        try:
            batch = Batch.objects.select_related("site").get(pk=batch_id)
        except Batch.DoesNotExist:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from None
        try:
            self.check_object_permissions(self.request, batch)
        except PermissionDenied as exc:
            raise NotFound(detail="Batch not found.", code="batch_not_found") from exc
        return batch

    def get_site_for_object(self, obj: Batch) -> Site:
        return obj.site

    @extend_schema(
        responses=ReviewSummarySerializer,
        summary="Get batch review summary",
        description=(
            "Returns a review-oriented completeness summary for a batch, "
            "including step completion, missing signatures, integrity flags, "
            "and traffic-light severity."
        ),
    )
    def get(self, request: Request, batch_id: int) -> Response:
        batch = self.get_object()
        summary = get_batch_review_summary(batch)
        serializer = ReviewSummarySerializer(dataclasses.asdict(summary))
        return Response(serializer.data)

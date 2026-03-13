from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Max

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.mmr.models import MMR, MMRVersion, MMRVersionStatus


def create_draft_version(
    *,
    mmr: MMR,
    actor: Any,
    change_summary: str = "",
) -> MMRVersion:
    with transaction.atomic():
        # Lock the MMR row to prevent race conditions on version_number
        MMR.objects.select_for_update().get(pk=mmr.pk)

        max_version = MMRVersion.objects.filter(mmr=mmr).aggregate(
            max_v=Max("version_number")
        )["max_v"]
        next_version = (max_version or 0) + 1

        version = MMRVersion.objects.create(
            mmr=mmr,
            version_number=next_version,
            status=MMRVersionStatus.DRAFT,
            created_by=actor,
            change_summary=change_summary,
        )

    record_audit_event(
        AuditEventType.MMR_VERSION_CREATED,
        actor=actor,
        site=mmr.site,
        metadata={
            "mmr_id": mmr.pk,
            "mmr_code": mmr.code,
            "version_id": version.pk,
            "version_number": version.version_number,
        },
    )
    return version

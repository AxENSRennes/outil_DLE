from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.mmr.models import MMR
from apps.sites.models import Product, Site


def create_mmr(
    *,
    site: Site,
    product: Product,
    name: str,
    code: str,
    description: str = "",
    actor: Any,
) -> MMR:
    with transaction.atomic():
        try:
            mmr = MMR.objects.create(
                site=site,
                product=product,
                name=name,
                code=code,
                description=description,
            )
        except IntegrityError as exc:
            raise ValueError(
                f"An MMR with code '{code}' already exists on this site."
            ) from exc

        record_audit_event(
            AuditEventType.MMR_CREATED,
            actor=actor,
            site=site,
            metadata={"mmr_id": mmr.pk, "mmr_code": mmr.code, "mmr_name": mmr.name},
        )
    return mmr

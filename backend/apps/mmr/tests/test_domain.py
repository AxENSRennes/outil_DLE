from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, AuditEventType
from apps.mmr.domain.mmr_service import create_mmr
from apps.mmr.domain.version_lifecycle import create_draft_version
from apps.mmr.models import MMRVersion, MMRVersionStatus
from apps.sites.models import Product, Site


@pytest.fixture()
def site() -> Site:
    return Site.objects.create(code="lyon", name="Lyon")


@pytest.fixture()
def product(site: Site) -> Product:
    return Product.objects.create(site=site, name="Parfum 100mL", code="PARFUM-100ML")


@pytest.fixture()
def user() -> Any:
    return get_user_model().objects.create_user(username="configurator", password="testpass")


# --- create_mmr tests ---


@pytest.mark.django_db
def test_create_mmr_happy_path(site: Site, product: Product, user: Any) -> None:
    mmr = create_mmr(
        site=site,
        product=product,
        name="Template Pilot",
        code="TPL-PILOT",
        description="A pilot template",
        actor=user,
    )
    assert mmr.pk is not None
    assert mmr.site == site
    assert mmr.product == product
    assert mmr.name == "Template Pilot"
    assert mmr.code == "TPL-PILOT"
    assert mmr.description == "A pilot template"
    assert mmr.is_active is True


@pytest.mark.django_db
def test_create_mmr_records_audit_event(site: Site, product: Product, user: Any) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    event = AuditEvent.objects.get(event_type=AuditEventType.MMR_CREATED)
    assert event.actor == user
    assert event.site == site
    assert event.metadata["mmr_code"] == "T1"
    assert event.metadata["mmr_id"] == mmr.pk
    assert event.metadata["mmr_name"] == "T"


@pytest.mark.django_db
def test_create_mmr_duplicate_code_raises(site: Site, product: Product, user: Any) -> None:
    create_mmr(site=site, product=product, name="A", code="SAME", actor=user)
    with pytest.raises(ValueError, match="already exists"):
        create_mmr(site=site, product=product, name="B", code="SAME", actor=user)


# --- create_draft_version tests ---


@pytest.mark.django_db
def test_create_draft_version_first_version(site: Site, product: Product, user: Any) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    version = create_draft_version(mmr=mmr, actor=user, change_summary="Initial")
    assert version.version_number == 1
    assert version.status == MMRVersionStatus.DRAFT
    assert version.created_by == user
    assert version.change_summary == "Initial"
    assert version.schema_json == {}
    assert version.activated_by is None
    assert version.activated_at is None


@pytest.mark.django_db
def test_create_draft_version_auto_increments(site: Site, product: Product, user: Any) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    v1 = create_draft_version(mmr=mmr, actor=user)
    v2 = create_draft_version(mmr=mmr, actor=user)
    v3 = create_draft_version(mmr=mmr, actor=user)
    assert v1.version_number == 1
    assert v2.version_number == 2
    assert v3.version_number == 3


@pytest.mark.django_db
def test_create_draft_version_immutability(site: Site, product: Product, user: Any) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    v1 = create_draft_version(mmr=mmr, actor=user, change_summary="V1")
    v1_created_at = v1.created_at

    create_draft_version(mmr=mmr, actor=user, change_summary="V2")

    # Refresh v1 from database to verify it was NOT mutated
    v1.refresh_from_db()
    assert v1.version_number == 1
    assert v1.status == MMRVersionStatus.DRAFT
    assert v1.change_summary == "V1"
    assert v1.created_at == v1_created_at


@pytest.mark.django_db
def test_create_draft_version_records_audit_event(
    site: Site, product: Product, user: Any
) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    version = create_draft_version(mmr=mmr, actor=user)
    event = AuditEvent.objects.get(event_type=AuditEventType.MMR_VERSION_CREATED)
    assert event.actor == user
    assert event.site == site
    assert event.metadata["mmr_code"] == "T1"
    assert event.metadata["version_number"] == version.version_number
    assert event.metadata["version_id"] == version.pk


@pytest.mark.django_db
def test_create_draft_version_status_is_always_draft(
    site: Site, product: Product, user: Any
) -> None:
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    version = create_draft_version(mmr=mmr, actor=user)
    assert version.status == MMRVersionStatus.DRAFT
    assert MMRVersion.objects.get(pk=version.pk).status == MMRVersionStatus.DRAFT


@pytest.mark.django_db
def test_create_draft_version_sets_created_by(
    site: Site, product: Product, user: Any
) -> None:
    other_user = get_user_model().objects.create_user(username="other", password="testpass")
    mmr = create_mmr(site=site, product=product, name="T", code="T1", actor=user)
    version = create_draft_version(mmr=mmr, actor=other_user)
    assert version.created_by == other_user

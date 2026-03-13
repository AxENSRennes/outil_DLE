from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.mmr.models import MMR, MMRVersion, MMRVersionStatus
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


@pytest.fixture()
def mmr(site: Site, product: Product) -> MMR:
    return MMR.objects.create(
        site=site,
        product=product,
        name="Chateau-Renard Parfum 100mL Pilot",
        code="CHR-PARFUM-100ML-PILOT",
    )


# --- MMR model tests ---


@pytest.mark.django_db
def test_mmr_creation(site: Site, product: Product) -> None:
    mmr = MMR.objects.create(
        site=site,
        product=product,
        name="Template Pilot",
        code="TPL-PILOT",
        description="Pilot template",
    )
    assert mmr.pk is not None
    assert mmr.site == site
    assert mmr.product == product
    assert mmr.name == "Template Pilot"
    assert mmr.code == "TPL-PILOT"
    assert mmr.description == "Pilot template"
    assert mmr.is_active is True
    assert mmr.created_at is not None
    assert mmr.updated_at is not None


@pytest.mark.django_db
def test_mmr_unique_code_per_site(site: Site, product: Product) -> None:
    MMR.objects.create(site=site, product=product, name="A", code="SAME-CODE")
    with pytest.raises(IntegrityError):
        MMR.objects.create(site=site, product=product, name="B", code="SAME-CODE")


@pytest.mark.django_db
def test_mmr_same_code_different_sites(product: Product) -> None:
    site_b = Site.objects.create(code="paris", name="Paris")
    product_b = Product.objects.create(site=site_b, name="Prod B", code="PB")
    m1 = MMR.objects.create(
        site=product.site, product=product, name="A", code="SAME-CODE"
    )
    m2 = MMR.objects.create(site=site_b, product=product_b, name="B", code="SAME-CODE")
    assert m1.pk != m2.pk


@pytest.mark.django_db
def test_mmr_str(mmr: MMR) -> None:
    assert str(mmr) == "CHR-PARFUM-100ML-PILOT - Chateau-Renard Parfum 100mL Pilot"


@pytest.mark.django_db
def test_delete_site_with_mmrs_raises_protected(mmr: MMR) -> None:
    with pytest.raises(ProtectedError):
        mmr.site.delete()


@pytest.mark.django_db
def test_delete_product_with_mmrs_raises_protected(mmr: MMR) -> None:
    with pytest.raises(ProtectedError):
        mmr.product.delete()


# --- MMRVersion model tests ---


@pytest.mark.django_db
def test_mmr_version_creation(mmr: MMR, user: Any) -> None:
    version = MMRVersion.objects.create(
        mmr=mmr,
        version_number=1,
        created_by=user,
        change_summary="Initial draft",
    )
    assert version.pk is not None
    assert version.mmr == mmr
    assert version.version_number == 1
    assert version.status == MMRVersionStatus.DRAFT
    assert version.schema_json == {}
    assert version.change_summary == "Initial draft"
    assert version.created_by == user
    assert version.activated_by is None
    assert version.activated_at is None
    assert version.created_at is not None
    assert version.updated_at is not None


@pytest.mark.django_db
def test_mmr_version_unique_version_number(mmr: MMR, user: Any) -> None:
    MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)
    with pytest.raises(IntegrityError):
        MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)


@pytest.mark.django_db
def test_mmr_version_ordering(mmr: MMR, user: Any) -> None:
    MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)
    MMRVersion.objects.create(mmr=mmr, version_number=2, created_by=user)
    MMRVersion.objects.create(mmr=mmr, version_number=3, created_by=user)
    versions = list(MMRVersion.objects.filter(mmr=mmr).values_list("version_number", flat=True))
    assert versions == [3, 2, 1]


@pytest.mark.django_db
def test_mmr_version_str(mmr: MMR, user: Any) -> None:
    v = MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)
    assert str(v) == "CHR-PARFUM-100ML-PILOT v1 (draft)"


@pytest.mark.django_db
def test_delete_mmr_with_versions_raises_protected(mmr: MMR, user: Any) -> None:
    MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)
    with pytest.raises(ProtectedError):
        mmr.delete()


@pytest.mark.django_db
def test_delete_user_with_created_versions_raises_protected(mmr: MMR, user: Any) -> None:
    MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)
    with pytest.raises(ProtectedError):
        user.delete()

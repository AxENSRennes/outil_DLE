from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.sites.models import Product, Site


@pytest.mark.django_db
def test_site_requires_unique_code() -> None:
    Site.objects.create(code="lyon-qc", name="Lyon Quality Control")

    with pytest.raises(IntegrityError):
        Site.objects.create(code="lyon-qc", name="Lyon Duplicate")


# --- Product model tests ---


@pytest.mark.django_db
def test_product_creation() -> None:
    site = Site.objects.create(code="lyon", name="Lyon")
    product = Product.objects.create(
        site=site,
        name="Parfum 100mL",
        code="PARFUM-100ML",
        family="Fragrance",
        format_label="100mL Spray",
    )
    assert product.pk is not None
    assert product.site == site
    assert product.name == "Parfum 100mL"
    assert product.code == "PARFUM-100ML"
    assert product.family == "Fragrance"
    assert product.format_label == "100mL Spray"
    assert product.is_active is True
    assert product.created_at is not None
    assert product.updated_at is not None


@pytest.mark.django_db
def test_product_unique_code_per_site() -> None:
    site = Site.objects.create(code="lyon", name="Lyon")
    Product.objects.create(site=site, name="Parfum 100mL", code="PARFUM-100ML")

    with pytest.raises(IntegrityError):
        Product.objects.create(site=site, name="Parfum Duplicate", code="PARFUM-100ML")


@pytest.mark.django_db
def test_product_same_code_different_sites() -> None:
    site_a = Site.objects.create(code="lyon", name="Lyon")
    site_b = Site.objects.create(code="paris", name="Paris")
    p1 = Product.objects.create(site=site_a, name="Parfum A", code="PARFUM-100ML")
    p2 = Product.objects.create(site=site_b, name="Parfum B", code="PARFUM-100ML")
    assert p1.pk != p2.pk


@pytest.mark.django_db
def test_product_blank_optional_fields() -> None:
    site = Site.objects.create(code="lyon", name="Lyon")
    product = Product.objects.create(site=site, name="Parfum", code="P1")
    assert product.family == ""
    assert product.format_label == ""


@pytest.mark.django_db
def test_product_str() -> None:
    site = Site.objects.create(code="lyon", name="Lyon")
    product = Product.objects.create(site=site, name="Parfum 100mL", code="PARFUM-100ML")
    assert str(product) == "PARFUM-100ML - Parfum 100mL"


@pytest.mark.django_db
def test_delete_site_with_products_raises_protected_error() -> None:
    site = Site.objects.create(code="lyon", name="Lyon")
    Product.objects.create(site=site, name="Parfum", code="P1")

    with pytest.raises(ProtectedError):
        site.delete()

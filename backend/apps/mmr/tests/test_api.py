from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site


@pytest.fixture()
def site() -> Site:
    return Site.objects.create(code="lyon", name="Lyon")


@pytest.fixture()
def product(site: Site) -> Product:
    return Product.objects.create(site=site, name="Parfum 100mL", code="PARFUM-100ML")


@pytest.fixture()
def configurator(site: Site) -> Any:
    user = get_user_model().objects.create_user(username="configurator", password="testpass")
    SiteRoleAssignment.objects.create(
        user=user, site=site, role=SiteRole.INTERNAL_CONFIGURATOR
    )
    return user


@pytest.fixture()
def operator(site: Site) -> Any:
    user = get_user_model().objects.create_user(username="operator", password="testpass")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    return user


@pytest.fixture()
def mmr(site: Site, product: Product) -> MMR:
    return MMR.objects.create(
        site=site,
        product=product,
        name="Template Pilot",
        code="TPL-PILOT",
    )


# --- MMR Create ---


@pytest.mark.django_db
def test_create_mmr_as_configurator(
    configurator: Any, site: Site, product: Product
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": site.pk,
            "product_id": product.pk,
            "name": "New Template",
            "code": "NEW-TPL",
        },
        csrf_token=token,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "NEW-TPL"
    assert data["name"] == "New Template"
    assert data["site"] == site.pk
    assert data["product"] == product.pk
    assert data["is_active"] is True
    assert MMR.objects.filter(code="NEW-TPL").exists()


@pytest.mark.django_db
def test_create_mmr_as_operator_denied(
    operator: Any, site: Site, product: Product
) -> None:
    client, token = csrf_client(user=operator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": site.pk,
            "product_id": product.pk,
            "name": "New Template",
            "code": "NEW-TPL",
        },
        csrf_token=token,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_mmr_unauthenticated_denied(site: Site, product: Product) -> None:
    client, token = csrf_client()
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": site.pk,
            "product_id": product.pk,
            "name": "New Template",
            "code": "NEW-TPL",
        },
        csrf_token=token,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_mmr_duplicate_code_conflict(
    configurator: Any, site: Site, product: Product
) -> None:
    MMR.objects.create(site=site, product=product, name="Existing", code="SAME-CODE")
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": site.pk,
            "product_id": product.pk,
            "name": "Another",
            "code": "SAME-CODE",
        },
        csrf_token=token,
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_create_mmr_csrf_required(configurator: Any, site: Site, product: Product) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.post(
        "/api/v1/mmrs/",
        {"site_id": site.pk, "product_id": product.pk, "name": "T", "code": "C"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_mmr_invalid_site_returns_400(
    configurator: Any, product: Product
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {"site_id": 99999, "product_id": product.pk, "name": "T", "code": "C"},
        csrf_token=token,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_mmr_invalid_product_returns_400(
    configurator: Any, site: Site
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {"site_id": site.pk, "product_id": 99999, "name": "T", "code": "C"},
        csrf_token=token,
    )
    assert resp.status_code == 400


# --- MMR List ---


@pytest.mark.django_db
def test_list_mmrs_returns_site_scoped(
    configurator: Any, site: Site, product: Product
) -> None:
    MMR.objects.create(site=site, product=product, name="A", code="A-CODE")
    other_site = Site.objects.create(code="paris", name="Paris")
    other_product = Product.objects.create(site=other_site, name="P", code="P1")
    MMR.objects.create(site=other_site, product=other_product, name="B", code="B-CODE")

    client, _ = csrf_client(user=configurator)
    resp = client.get("/api/v1/mmrs/")
    assert resp.status_code == 200
    data = resp.json()
    codes = [m["code"] for m in data]
    assert "A-CODE" in codes
    assert "B-CODE" not in codes


# --- MMR Detail ---


@pytest.mark.django_db
def test_retrieve_mmr_as_configurator(
    configurator: Any, mmr: MMR
) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "TPL-PILOT"
    assert "version_count" in data


@pytest.mark.django_db
def test_retrieve_mmr_not_found() -> None:
    user = get_user_model().objects.create_user(username="u", password="p")
    client, _ = csrf_client(user=user)
    resp = client.get("/api/v1/mmrs/99999/")
    assert resp.status_code == 404


# --- Version Create ---


@pytest.mark.django_db
def test_create_version_as_configurator(
    configurator: Any, mmr: MMR
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        f"/api/v1/mmrs/{mmr.pk}/versions/",
        {"change_summary": "Initial draft"},
        csrf_token=token,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["version_number"] == 1
    assert data["status"] == "draft"
    assert data["created_by"] == configurator.pk
    assert data["change_summary"] == "Initial draft"


@pytest.mark.django_db
def test_create_version_auto_increments(
    configurator: Any, mmr: MMR
) -> None:
    client, token = csrf_client(user=configurator)
    r1 = post_json(client, f"/api/v1/mmrs/{mmr.pk}/versions/", {}, csrf_token=token)
    r2 = post_json(client, f"/api/v1/mmrs/{mmr.pk}/versions/", {}, csrf_token=token)
    assert r1.json()["version_number"] == 1
    assert r2.json()["version_number"] == 2


@pytest.mark.django_db
def test_create_version_as_operator_denied(
    operator: Any, mmr: MMR
) -> None:
    client, token = csrf_client(user=operator)
    resp = post_json(
        client,
        f"/api/v1/mmrs/{mmr.pk}/versions/",
        {"change_summary": "Nope"},
        csrf_token=token,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_version_csrf_required(
    configurator: Any, mmr: MMR
) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.post(
        f"/api/v1/mmrs/{mmr.pk}/versions/",
        {"change_summary": "No CSRF"},
        format="json",
    )
    assert resp.status_code == 403


# --- Version List ---


@pytest.mark.django_db
def test_list_versions_ordered_by_desc_version_number(
    configurator: Any, mmr: MMR
) -> None:
    MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=configurator)
    MMRVersion.objects.create(mmr=mmr, version_number=2, created_by=configurator)
    MMRVersion.objects.create(mmr=mmr, version_number=3, created_by=configurator)

    client, _ = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/")
    assert resp.status_code == 200
    data = resp.json()
    version_numbers = [v["version_number"] for v in data]
    assert version_numbers == [3, 2, 1]


# --- Version Detail ---


@pytest.mark.django_db
def test_retrieve_version(configurator: Any, mmr: MMR) -> None:
    version = MMRVersion.objects.create(
        mmr=mmr, version_number=1, created_by=configurator
    )
    client, _ = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/{version.pk}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version_number"] == 1
    assert data["status"] == "draft"


@pytest.mark.django_db
def test_retrieve_version_wrong_mmr_returns_404(
    configurator: Any, site: Site, product: Product, mmr: MMR
) -> None:
    other_mmr = MMR.objects.create(site=site, product=product, name="Other", code="OTHER")
    version = MMRVersion.objects.create(
        mmr=other_mmr, version_number=1, created_by=configurator
    )
    client, _ = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/{version.pk}/")
    assert resp.status_code == 404


# --- Audit events ---


@pytest.mark.django_db
def test_create_mmr_records_audit_event(
    configurator: Any, site: Site, product: Product
) -> None:
    client, token = csrf_client(user=configurator)
    post_json(
        client,
        "/api/v1/mmrs/",
        {"site_id": site.pk, "product_id": product.pk, "name": "T", "code": "C1"},
        csrf_token=token,
    )
    assert AuditEvent.objects.filter(event_type=AuditEventType.MMR_CREATED).exists()


@pytest.mark.django_db
def test_create_version_records_audit_event(
    configurator: Any, mmr: MMR
) -> None:
    client, token = csrf_client(user=configurator)
    post_json(client, f"/api/v1/mmrs/{mmr.pk}/versions/", {}, csrf_token=token)
    assert AuditEvent.objects.filter(
        event_type=AuditEventType.MMR_VERSION_CREATED
    ).exists()


# --- Cross-site isolation ---


@pytest.mark.django_db
def test_configurator_cannot_create_mmr_on_other_site(configurator: Any) -> None:
    other_site = Site.objects.create(code="paris", name="Paris")
    other_product = Product.objects.create(site=other_site, name="P", code="P1")
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": other_site.pk,
            "product_id": other_product.pk,
            "name": "T",
            "code": "C1",
        },
        csrf_token=token,
    )
    assert resp.status_code == 403


# --- RBAC: operator denied on list ---


@pytest.mark.django_db
def test_list_mmrs_as_operator_returns_empty(
    operator: Any, site: Site, product: Product
) -> None:
    MMR.objects.create(site=site, product=product, name="A", code="A-CODE")
    client, _ = csrf_client(user=operator)
    resp = client.get("/api/v1/mmrs/")
    assert resp.status_code == 200
    assert resp.json() == []


# --- Version: nonexistent MMR ---


@pytest.mark.django_db
def test_create_version_nonexistent_mmr_returns_404(configurator: Any) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/99999/versions/",
        {"change_summary": "Should fail"},
        csrf_token=token,
    )
    assert resp.status_code == 404


# --- Problem-details error format ---


@pytest.mark.django_db
def test_create_mmr_error_uses_problem_details_format(
    configurator: Any, site: Site, product: Product
) -> None:
    MMR.objects.create(site=site, product=product, name="Existing", code="DUP-CODE")
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        "/api/v1/mmrs/",
        {
            "site_id": site.pk,
            "product_id": product.pk,
            "name": "Another",
            "code": "DUP-CODE",
        },
        csrf_token=token,
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "type" in data
    assert "title" in data
    assert "detail" in data

from __future__ import annotations

import pytest
from django.contrib.admin.sites import AdminSite

from apps.mmr.admin import MMRAdmin, MMRVersionAdmin
from apps.mmr.models import MMR, MMRVersion
from apps.sites.admin import ProductAdmin
from apps.sites.models import Product


@pytest.mark.django_db
def test_mmr_admin_has_delete_permission_false() -> None:
    admin_instance = MMRAdmin(MMR, AdminSite())
    assert admin_instance.has_delete_permission(request=None) is False


@pytest.mark.django_db
def test_mmr_version_admin_has_delete_permission_false() -> None:
    admin_instance = MMRVersionAdmin(MMRVersion, AdminSite())
    assert admin_instance.has_delete_permission(request=None) is False


@pytest.mark.django_db
def test_mmr_version_admin_readonly_fields() -> None:
    admin_instance = MMRVersionAdmin(MMRVersion, AdminSite())
    assert "schema_json" in admin_instance.readonly_fields
    assert "activated_by" in admin_instance.readonly_fields
    assert "activated_at" in admin_instance.readonly_fields


@pytest.mark.django_db
def test_product_admin_has_delete_permission_false() -> None:
    admin_instance = ProductAdmin(Product, AdminSite())
    assert admin_instance.has_delete_permission(request=None) is False

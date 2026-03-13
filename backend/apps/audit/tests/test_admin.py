from __future__ import annotations

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.audit.admin import AuditEventAdmin
from apps.audit.models import AuditEvent


@pytest.fixture
def audit_admin() -> AuditEventAdmin:
    return AuditEventAdmin(AuditEvent, AdminSite())


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


def test_audit_admin_forbids_add(
    audit_admin: AuditEventAdmin,
    request_factory: RequestFactory,
) -> None:
    request = request_factory.get("/admin/audit/auditevent/add/")
    assert audit_admin.has_add_permission(request) is False


def test_audit_admin_forbids_change(
    audit_admin: AuditEventAdmin,
    request_factory: RequestFactory,
) -> None:
    request = request_factory.get("/admin/audit/auditevent/1/change/")
    assert audit_admin.has_change_permission(request) is False


def test_audit_admin_forbids_delete(
    audit_admin: AuditEventAdmin,
    request_factory: RequestFactory,
) -> None:
    request = request_factory.get("/admin/audit/auditevent/1/delete/")
    assert audit_admin.has_delete_permission(request) is False


def test_audit_admin_list_display_includes_target_fields(
    audit_admin: AuditEventAdmin,
) -> None:
    assert "target_type" in audit_admin.list_display
    assert "target_id" in audit_admin.list_display


def test_audit_admin_list_filter_includes_target_type(
    audit_admin: AuditEventAdmin,
) -> None:
    assert "target_type" in audit_admin.list_filter
    assert "target_id" in audit_admin.list_filter

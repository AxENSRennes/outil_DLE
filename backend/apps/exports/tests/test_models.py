"""Model tests for the exports app."""

from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.batches.models import Batch
from apps.exports.models import (
    ApplicabilityStatus,
    BatchDossierStructure,
    DossierElement,
    DossierElementType,
    DossierProfile,
)
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Site

User = get_user_model()


def _make_fixtures() -> dict[str, Any]:
    """Create minimal fixtures for model tests."""
    site = Site.objects.create(code="site-m", name="Model Test Site")
    user = User.objects.create_user(username="model-tester", password="testpass")
    mmr = MMR.objects.create(site=site, name="Test MMR", code="MMR-M1")
    version = MMRVersion.objects.create(
        mmr=mmr,
        version_number=1,
        schema_json={"schemaVersion": "v1"},
        created_by=user,
    )
    batch = Batch.objects.create(
        site=site,
        mmr_version=version,
        batch_number="BATCH-M001",
        batch_context_json={"line": "L1"},
        snapshot_json={},
        created_by=user,
    )
    profile = DossierProfile.objects.create(
        mmr_version=version,
        name="Test Profile",
        rules={"default_required": ["doc-a"], "conditions": []},
        elements=[{"identifier": "doc-a"}, {"identifier": "doc-b"}],
    )
    return {
        "site": site,
        "user": user,
        "mmr": mmr,
        "version": version,
        "batch": batch,
        "profile": profile,
    }


@pytest.mark.django_db
class TestDossierProfile:
    def test_jsonb_rules_store_and_retrieve(self) -> None:
        fx = _make_fixtures()
        profile = DossierProfile.objects.get(pk=fx["profile"].pk)
        assert profile.rules == {"default_required": ["doc-a"], "conditions": []}
        assert profile.elements == [{"identifier": "doc-a"}, {"identifier": "doc-b"}]

    def test_str(self) -> None:
        fx = _make_fixtures()
        assert "Test Profile" in str(fx["profile"])


@pytest.mark.django_db
class TestBatchDossierStructure:
    def test_fk_protect_prevents_batch_deletion(self) -> None:
        fx = _make_fixtures()
        structure = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={"line": "L1"},
        )
        assert structure.pk is not None
        with pytest.raises(IntegrityError):
            fx["batch"].delete()

    def test_fk_protect_prevents_profile_deletion(self) -> None:
        fx = _make_fixtures()
        BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
        )
        with pytest.raises(IntegrityError):
            fx["profile"].delete()

    def test_ordering_by_resolved_at_desc(self) -> None:
        fx = _make_fixtures()
        s1 = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
            is_active=False,
        )
        s2 = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
            is_active=True,
        )
        structures = list(
            BatchDossierStructure.objects.filter(batch=fx["batch"]).values_list(
                "pk", flat=True
            )
        )
        # s2 was created later → should appear first
        assert structures[0] == s2.pk
        assert structures[1] == s1.pk


@pytest.mark.django_db
class TestDossierElement:
    def test_ordering_by_display_order(self) -> None:
        fx = _make_fixtures()
        structure = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
        )
        DossierElement.objects.create(
            structure=structure,
            element_identifier="el-b",
            element_type=DossierElementType.SUB_DOCUMENT,
            display_order=2,
            applicability=ApplicabilityStatus.REQUIRED,
        )
        DossierElement.objects.create(
            structure=structure,
            element_identifier="el-a",
            element_type=DossierElementType.IN_PROCESS_CONTROL,
            display_order=1,
            applicability=ApplicabilityStatus.NOT_APPLICABLE,
        )
        elements = list(structure.elements.values_list("element_identifier", flat=True))
        assert elements == ["el-a", "el-b"]

    def test_unique_element_per_structure(self) -> None:
        fx = _make_fixtures()
        structure = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
        )
        DossierElement.objects.create(
            structure=structure,
            element_identifier="dup-el",
            element_type=DossierElementType.SUB_DOCUMENT,
            display_order=1,
            applicability=ApplicabilityStatus.REQUIRED,
        )
        with pytest.raises(IntegrityError):
            DossierElement.objects.create(
                structure=structure,
                element_identifier="dup-el",
                element_type=DossierElementType.SUB_DOCUMENT,
                display_order=2,
                applicability=ApplicabilityStatus.REQUIRED,
            )

    def test_fk_protect_prevents_structure_deletion(self) -> None:
        fx = _make_fixtures()
        structure = BatchDossierStructure.objects.create(
            batch=fx["batch"],
            dossier_profile=fx["profile"],
            context_snapshot={},
        )
        DossierElement.objects.create(
            structure=structure,
            element_identifier="protected-el",
            element_type=DossierElementType.CHECKLIST_ITEM,
            display_order=1,
            applicability=ApplicabilityStatus.REQUIRED,
        )
        with pytest.raises(IntegrityError):
            structure.delete()


@pytest.mark.django_db
class TestAdminPermissions:
    def test_batch_dossier_structure_admin_is_read_only(self) -> None:
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from apps.exports.admin import BatchDossierStructureAdmin

        admin_instance = BatchDossierStructureAdmin(BatchDossierStructure, AdminSite())
        request = RequestFactory().get("/admin/")

        assert admin_instance.has_add_permission(request) is False
        assert admin_instance.has_change_permission(request) is False
        assert admin_instance.has_delete_permission(request) is False

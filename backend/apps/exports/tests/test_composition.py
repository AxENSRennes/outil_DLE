"""Domain tests for the dossier composition service."""

from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, AuditEventType
from apps.batches.models import Batch
from apps.exports.domain.composition import (
    DossierCompositionError,
    _condition_matches,
    resolve_dossier_structure,
)
from apps.exports.models import (
    ApplicabilityStatus,
    BatchDossierStructure,
    DossierElementType,
    DossierProfile,
)
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Site

User = get_user_model()


def _make_profile_and_batch(
    *,
    batch_context: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    elements: list[Any] | None = None,
) -> dict[str, Any]:
    """Create a full set of fixtures for composition tests."""
    site = Site.objects.create(
        code=f"site-{Site.objects.count()}",
        name="Composition Test Site",
    )
    user = User.objects.create_user(
        username=f"comp-user-{User.objects.count()}",
        password="testpass",
    )
    mmr = MMR.objects.create(site=site, name="Test MMR", code=f"MMR-{MMR.objects.count()}")
    version = MMRVersion.objects.create(
        mmr=mmr,
        version_number=1,
        schema_json={"schemaVersion": "v1"},
        created_by=user,
    )

    default_elements: list[Any] = [
        {"identifier": "batch-header", "type": "sub_document", "title": "Batch Header"},
        {"identifier": "weighing-record", "type": "sub_document", "title": "Weighing Record"},
        {
            "identifier": "release-checklist",
            "type": "checklist_item",
            "title": "Release Checklist",
        },
        {
            "identifier": "paillette-control",
            "type": "in_process_control",
            "title": "Paillette Control",
        },
        {
            "identifier": "viscosity-control",
            "type": "in_process_control",
            "title": "Viscosity Control",
        },
    ]

    default_rules: dict[str, Any] = {
        "default_required": ["batch-header", "weighing-record", "release-checklist"],
        "conditions": [
            {
                "context_key": "paillette_present",
                "operator": "eq",
                "value": True,
                "include_elements": ["paillette-control"],
                "exclude_elements": [],
            },
            {
                "context_key": "format_family",
                "operator": "in",
                "value": ["CREAM", "GEL"],
                "include_elements": ["viscosity-control"],
                "exclude_elements": [],
            },
        ],
    }

    profile = DossierProfile.objects.create(
        mmr_version=version,
        name="Test Profile",
        rules=rules if rules is not None else default_rules,
        elements=elements if elements is not None else default_elements,
    )

    batch = Batch.objects.create(
        site=site,
        mmr_version=version,
        batch_number=f"BATCH-{Batch.objects.count():04d}",
        batch_context_json=batch_context or {},
        snapshot_json={},
        created_by=user,
    )

    return {
        "site": site,
        "user": user,
        "mmr": mmr,
        "version": version,
        "profile": profile,
        "batch": batch,
    }


@pytest.mark.django_db
class TestResolveFullContext:
    """Resolves correct elements for a batch with full context (all attributes present)."""

    def test_full_context_includes_all_matching_elements(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        structure = resolve_dossier_structure(fx["batch"])

        identifiers = [el.element_identifier for el in structure.elements.all()]
        # All 5 elements should be required
        assert "batch-header" in identifiers
        assert "weighing-record" in identifiers
        assert "release-checklist" in identifiers
        assert "paillette-control" in identifiers
        assert "viscosity-control" in identifiers

        # All should be required
        for el in structure.elements.all():
            assert el.applicability == ApplicabilityStatus.REQUIRED


@pytest.mark.django_db
class TestExcludesNonApplicable:
    """Excludes non-applicable elements based on context."""

    def test_paillette_excluded_when_not_present(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": False, "format_family": "POWDER"},
        )
        structure = resolve_dossier_structure(fx["batch"])

        el_map = {el.element_identifier: el for el in structure.elements.all()}

        # Default-required elements are always present
        assert el_map["batch-header"].applicability == ApplicabilityStatus.REQUIRED
        assert el_map["weighing-record"].applicability == ApplicabilityStatus.REQUIRED
        assert el_map["release-checklist"].applicability == ApplicabilityStatus.REQUIRED

        # paillette_present=False → paillette control not applicable
        assert el_map["paillette-control"].applicability == ApplicabilityStatus.NOT_APPLICABLE
        # format_family=POWDER not in [CREAM, GEL] → viscosity not applicable
        assert el_map["viscosity-control"].applicability == ApplicabilityStatus.NOT_APPLICABLE


@pytest.mark.django_db
class TestDefaultRequired:
    """Default-required elements always appear regardless of context."""

    def test_default_required_always_included(self) -> None:
        fx = _make_profile_and_batch(batch_context={})
        structure = resolve_dossier_structure(fx["batch"])

        identifiers = [el.element_identifier for el in structure.elements.all()]
        assert "batch-header" in identifiers
        assert "weighing-record" in identifiers
        assert "release-checklist" in identifiers

        # Check they are required
        for el in structure.elements.filter(
            element_identifier__in=["batch-header", "weighing-record", "release-checklist"]
        ):
            assert el.applicability == ApplicabilityStatus.REQUIRED


@pytest.mark.django_db
class TestCategoricalMatching:
    """Categorical matching produces correct element set."""

    def test_format_family_cream_includes_viscosity(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"format_family": "CREAM"},
        )
        structure = resolve_dossier_structure(fx["batch"])
        el_map = {el.element_identifier: el for el in structure.elements.all()}
        assert el_map["viscosity-control"].applicability == ApplicabilityStatus.REQUIRED

    def test_format_family_powder_excludes_viscosity(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"format_family": "POWDER"},
        )
        structure = resolve_dossier_structure(fx["batch"])
        el_map = {el.element_identifier: el for el in structure.elements.all()}
        assert el_map["viscosity-control"].applicability == ApplicabilityStatus.NOT_APPLICABLE


@pytest.mark.django_db
class TestIdempotency:
    """Second call returns existing structure without creating duplicates."""

    def test_second_call_returns_same_structure(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        s1 = resolve_dossier_structure(fx["batch"])
        s2 = resolve_dossier_structure(fx["batch"])

        assert s1.pk == s2.pk
        assert BatchDossierStructure.objects.filter(batch=fx["batch"]).count() == 1


@pytest.mark.django_db
class TestForceRegenerate:
    """Force-regenerate creates new structure while preserving old one."""

    def test_force_creates_new_deactivates_old(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        s1 = resolve_dossier_structure(fx["batch"])
        s2 = resolve_dossier_structure(fx["batch"], force=True)

        assert s1.pk != s2.pk
        assert BatchDossierStructure.objects.filter(batch=fx["batch"]).count() == 2

        # Old structure is deactivated
        s1.refresh_from_db()
        assert s1.is_active is False

        # New structure is active
        assert s2.is_active is True


@pytest.mark.django_db
class TestEdgeCases:
    """Edge cases: missing context, empty rules, all elements excluded."""

    def test_missing_context_attributes(self) -> None:
        """Batch with no context attributes should still include default-required."""
        fx = _make_profile_and_batch(batch_context={})
        structure = resolve_dossier_structure(fx["batch"])

        required = [
            el.element_identifier
            for el in structure.elements.all()
            if el.applicability == ApplicabilityStatus.REQUIRED
        ]
        assert "batch-header" in required
        assert "weighing-record" in required
        assert "release-checklist" in required

    def test_empty_rules(self) -> None:
        """Profile with empty rules produces no elements."""
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True},
            rules={},
            elements=[{"identifier": "doc-a"}],
        )
        structure = resolve_dossier_structure(fx["batch"])
        assert structure.elements.count() == 0

    def test_all_elements_excluded(self) -> None:
        """When conditions exclude all elements and none are default-required."""
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": False},
            rules={
                "default_required": [],
                "conditions": [
                    {
                        "context_key": "paillette_present",
                        "operator": "eq",
                        "value": True,
                        "include_elements": ["paillette-only"],
                        "exclude_elements": [],
                    },
                ],
            },
            elements=[{"identifier": "paillette-only"}],
        )
        structure = resolve_dossier_structure(fx["batch"])
        # paillette-only should be not_applicable since condition didn't match
        na_elements = [
            el
            for el in structure.elements.all()
            if el.applicability == ApplicabilityStatus.NOT_APPLICABLE
        ]
        assert len(na_elements) == 1
        assert na_elements[0].element_identifier == "paillette-only"

    def test_no_dossier_profile_raises_error(self) -> None:
        """No DossierProfile for the MMR version should raise DossierCompositionError."""
        site = Site.objects.create(code="site-no-profile", name="No Profile Site")
        user = User.objects.create_user(username="no-profile-user", password="testpass")
        mmr = MMR.objects.create(site=site, name="MMR NP", code="MMR-NP")
        version = MMRVersion.objects.create(
            mmr=mmr, version_number=1, schema_json={}, created_by=user
        )
        batch = Batch.objects.create(
            site=site,
            mmr_version=version,
            batch_number="BATCH-NP",
            snapshot_json={},
            created_by=user,
        )

        with pytest.raises(DossierCompositionError, match="No DossierProfile found"):
            resolve_dossier_structure(batch)


@pytest.mark.django_db
class TestContextSnapshot:
    """The resolved structure stores the context snapshot at resolution time."""

    def test_context_snapshot_captured(self) -> None:
        context = {"paillette_present": True, "format_family": "CREAM", "line": "L1"}
        fx = _make_profile_and_batch(batch_context=context)
        structure = resolve_dossier_structure(fx["batch"])
        assert structure.context_snapshot == context


@pytest.mark.django_db
class TestElementTypes:
    """Elements preserve their type from the profile catalog."""

    def test_element_types_preserved(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        structure = resolve_dossier_structure(fx["batch"])
        el_map = {el.element_identifier: el for el in structure.elements.all()}

        assert el_map["batch-header"].element_type == DossierElementType.SUB_DOCUMENT
        assert el_map["paillette-control"].element_type == DossierElementType.IN_PROCESS_CONTROL
        assert el_map["release-checklist"].element_type == DossierElementType.CHECKLIST_ITEM


class TestConditionMatchesNotIn:
    """not_in operator with non-list value returns False (bug fix)."""

    def test_not_in_with_non_list_value_returns_false(self) -> None:
        condition = {"context_key": "x", "operator": "not_in", "value": "not-a-list"}
        assert _condition_matches(condition, {"x": "anything"}) is False

    def test_not_in_with_list_value_works(self) -> None:
        condition = {"context_key": "x", "operator": "not_in", "value": ["a", "b"]}
        assert _condition_matches(condition, {"x": "c"}) is True
        assert _condition_matches(condition, {"x": "a"}) is False


@pytest.mark.django_db
class TestAuditEvent:
    """resolve_dossier_structure creates an audit event."""

    def test_audit_event_created_on_resolve(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        initial_count = AuditEvent.objects.filter(
            event_type=AuditEventType.DOSSIER_RESOLVED,
        ).count()

        resolve_dossier_structure(fx["batch"], actor=fx["user"], site=fx["site"])

        assert (
            AuditEvent.objects.filter(event_type=AuditEventType.DOSSIER_RESOLVED).count()
            == initial_count + 1
        )
        event = AuditEvent.objects.filter(
            event_type=AuditEventType.DOSSIER_RESOLVED,
        ).latest("occurred_at")
        assert event.actor == fx["user"]
        assert event.site == fx["site"]
        assert event.metadata["batch_id"] == fx["batch"].pk

    def test_idempotent_call_does_not_create_second_audit_event(self) -> None:
        fx = _make_profile_and_batch(
            batch_context={"paillette_present": True, "format_family": "CREAM"},
        )
        resolve_dossier_structure(fx["batch"], actor=fx["user"], site=fx["site"])
        count_after_first = AuditEvent.objects.filter(
            event_type=AuditEventType.DOSSIER_RESOLVED,
        ).count()

        # Second call is idempotent — returns existing, no new audit event.
        resolve_dossier_structure(fx["batch"], actor=fx["user"], site=fx["site"])

        assert (
            AuditEvent.objects.filter(event_type=AuditEventType.DOSSIER_RESOLVED).count()
            == count_after_first
        )

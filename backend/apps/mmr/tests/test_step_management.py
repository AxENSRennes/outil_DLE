from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, AuditEventType
from apps.mmr.domain.step_management import (
    add_step,
    get_step,
    get_steps,
    remove_step,
    reorder_steps,
    update_step,
)
from apps.mmr.models import MMR, MMRVersion, MMRVersionStatus
from apps.sites.models import Product, Site


@pytest.fixture()
def site() -> Site:
    return Site.objects.create(code="lyon", name="Lyon")


@pytest.fixture()
def product(site: Site) -> Product:
    return Product.objects.create(
        site=site,
        name="Parfum 100mL",
        code="PARFUM-100ML",
        family="Parfum",
        format_label="100mL",
    )


@pytest.fixture()
def user() -> Any:
    return get_user_model().objects.create_user(username="configurator", password="testpass")


@pytest.fixture()
def mmr(site: Site, product: Product) -> MMR:
    return MMR.objects.create(
        site=site,
        product=product,
        name="Chateau-Renard Parfum 100mL pilot",
        code="CHR-PARFUM-100ML-PILOT",
    )


@pytest.fixture()
def draft_version(mmr: MMR, user: Any) -> MMRVersion:
    return MMRVersion.objects.create(
        mmr=mmr,
        version_number=1,
        status=MMRVersionStatus.DRAFT,
        created_by=user,
        schema_json={},
    )


@pytest.fixture()
def active_version(mmr: MMR, user: Any) -> MMRVersion:
    return MMRVersion.objects.create(
        mmr=mmr,
        version_number=2,
        status=MMRVersionStatus.ACTIVE,
        created_by=user,
        schema_json={},
    )


@pytest.fixture()
def sample_step_data() -> dict:
    return {
        "key": "fabrication_bulk",
        "title": "Dossier de fabrication bulk",
        "kind": "manufacturing",
        "instructions": "Saisir et verifier les informations bulk.",
    }


# ---------------------------------------------------------------------------
# add_step tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_step_to_empty_schema_initializes_header(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    result = add_step(version=draft_version, step_data=sample_step_data, actor=user)

    assert result["key"] == "fabrication_bulk"
    assert result["title"] == "Dossier de fabrication bulk"
    assert result["kind"] == "manufacturing"
    assert result["instructions"] == "Saisir et verifier les informations bulk."
    assert result["required"] is True
    assert result["fields"] == []
    assert result["signature_policy"] == {"required": False, "meaning": "performed_by"}

    # Verify schema_json was initialized with header
    draft_version.refresh_from_db()
    schema = draft_version.schema_json
    assert schema["schemaVersion"] == "v1"
    assert schema["templateCode"] == "CHR-PARFUM-100ML-PILOT"
    assert schema["templateName"] == "Chateau-Renard Parfum 100mL pilot"
    assert schema["product"]["productCode"] == "PARFUM-100ML"
    assert schema["product"]["productName"] == "Parfum 100mL"
    assert schema["product"]["family"] == "Parfum"
    assert schema["product"]["formatLabel"] == "100mL"
    assert schema["stepOrder"] == ["fabrication_bulk"]
    assert "fabrication_bulk" in schema["steps"]


@pytest.mark.django_db
def test_add_second_step_appends_to_existing(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "weighing", "title": "Pesee", "kind": "weighing"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={
            "key": "packaging",
            "title": "Conditionnement",
            "kind": "packaging",
        },
        actor=user,
    )

    draft_version.refresh_from_db()
    assert draft_version.schema_json["stepOrder"] == ["weighing", "packaging"]
    assert set(draft_version.schema_json["steps"].keys()) == {
        "weighing",
        "packaging",
    }


@pytest.mark.django_db
def test_add_step_duplicate_key_raises(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    with pytest.raises(ValueError, match="already exists"):
        add_step(version=draft_version, step_data=sample_step_data, actor=user)


@pytest.mark.django_db
def test_add_step_invalid_kind_raises(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="Invalid step kind"):
        add_step(
            version=draft_version,
            step_data={"key": "bad", "title": "Bad", "kind": "invalid_kind"},
            actor=user,
        )


@pytest.mark.django_db
def test_add_step_non_draft_raises(
    active_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    with pytest.raises(ValueError, match="Only draft versions"):
        add_step(version=active_version, step_data=sample_step_data, actor=user)


@pytest.mark.django_db
def test_add_step_invalid_key_pattern_raises(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="Invalid step key"):
        add_step(
            version=draft_version,
            step_data={"key": "Bad-Key", "title": "T", "kind": "weighing"},
            actor=user,
        )


@pytest.mark.django_db
def test_add_step_reserved_key_raises(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="reserved and cannot be used"):
        add_step(
            version=draft_version,
            step_data={"key": "reorder", "title": "Reorder Step", "kind": "weighing"},
            actor=user,
        )


@pytest.mark.django_db
def test_add_step_records_audit_event(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    event = AuditEvent.objects.get(event_type=AuditEventType.MMR_VERSION_STEP_ADDED)
    assert event.actor == user
    assert event.site == draft_version.mmr.site
    assert event.metadata["step_key"] == "fabrication_bulk"
    assert event.metadata["version_id"] == draft_version.pk


@pytest.mark.django_db
def test_add_step_with_blocking_policy(draft_version: MMRVersion, user: Any) -> None:
    result = add_step(
        version=draft_version,
        step_data={
            "key": "fab",
            "title": "Fab",
            "kind": "manufacturing",
            "blocking_policy": {
                "blocks_step_completion": True,
                "blocks_signature": True,
                "blocks_pre_qa_handoff": True,
            },
        },
        actor=user,
    )
    assert result["blocking_policy"]["blocks_step_completion"] is True
    assert result["blocking_policy"]["blocks_signature"] is True
    assert result["blocking_policy"]["blocks_pre_qa_handoff"] is True

    # Verify camelCase storage in schema_json
    draft_version.refresh_from_db()
    stored = draft_version.schema_json["steps"]["fab"]["blockingPolicy"]
    assert stored["blocksStepCompletion"] is True
    assert stored["blocksSignature"] is True


@pytest.mark.django_db
def test_add_step_defaults_required_to_true(draft_version: MMRVersion, user: Any) -> None:
    result = add_step(
        version=draft_version,
        step_data={"key": "s1", "title": "Step 1", "kind": "preparation"},
        actor=user,
    )
    assert result["required"] is True


@pytest.mark.django_db
def test_add_step_rejects_attachment_kinds_without_support_flag(
    draft_version: MMRVersion, user: Any
) -> None:
    with pytest.raises(ValueError, match="supports_attachments"):
        add_step(
            version=draft_version,
            step_data={
                "key": "s1",
                "title": "Step 1",
                "kind": "preparation",
                "attachments_policy": {
                    "supports_attachments": False,
                    "attachment_kinds": ["photo"],
                },
            },
            actor=user,
        )


@pytest.mark.django_db
def test_add_step_rejects_repeat_policy_without_mode(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match=r"repeat_policy\.mode"):
        add_step(
            version=draft_version,
            step_data={
                "key": "s1",
                "title": "Step 1",
                "kind": "preparation",
                "repeat_policy": {"max_records": 3},
            },
            actor=user,
        )


# ---------------------------------------------------------------------------
# update_step tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_step_title_and_instructions(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    result = update_step(
        version=draft_version,
        step_key="fabrication_bulk",
        step_data={
            "title": "Updated Title",
            "instructions": "Updated instructions",
        },
        actor=user,
    )
    assert result["title"] == "Updated Title"
    assert result["instructions"] == "Updated instructions"
    assert result["kind"] == "manufacturing"  # unchanged


@pytest.mark.django_db
def test_update_step_partial_only_changes_specified(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    result = update_step(
        version=draft_version,
        step_key="fabrication_bulk",
        step_data={"title": "New Title"},
        actor=user,
    )
    assert result["title"] == "New Title"
    assert result["kind"] == "manufacturing"
    assert result["instructions"] == "Saisir et verifier les informations bulk."


@pytest.mark.django_db
def test_update_step_nonexistent_key_raises(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="not found"):
        update_step(
            version=draft_version,
            step_key="nonexistent",
            step_data={"title": "X"},
            actor=user,
        )


@pytest.mark.django_db
def test_update_step_non_draft_raises(active_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="Only draft versions"):
        update_step(
            version=active_version,
            step_key="any_key",
            step_data={"title": "X"},
            actor=user,
        )


@pytest.mark.django_db
def test_update_step_records_audit_event(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    update_step(
        version=draft_version,
        step_key="fabrication_bulk",
        step_data={"title": "Updated"},
        actor=user,
    )
    event = AuditEvent.objects.filter(event_type=AuditEventType.MMR_VERSION_STEP_UPDATED).first()
    assert event is not None
    assert event.metadata["step_key"] == "fabrication_bulk"


@pytest.mark.django_db
def test_update_step_blocking_policy(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    result = update_step(
        version=draft_version,
        step_key="fabrication_bulk",
        step_data={
            "blocking_policy": {
                "blocks_execution_progress": True,
                "blocks_step_completion": True,
            },
        },
        actor=user,
    )
    assert result["blocking_policy"]["blocks_execution_progress"] is True
    assert result["blocking_policy"]["blocks_step_completion"] is True


@pytest.mark.django_db
def test_update_step_partial_blocking_policy_preserves_existing(
    draft_version: MMRVersion, user: Any
) -> None:
    """Partial update of blocking_policy must merge, not replace."""
    add_step(
        version=draft_version,
        step_data={
            "key": "fab",
            "title": "Fab",
            "kind": "manufacturing",
            "blocking_policy": {
                "blocks_signature": True,
                "blocks_pre_qa_handoff": True,
            },
        },
        actor=user,
    )
    result = update_step(
        version=draft_version,
        step_key="fab",
        step_data={"blocking_policy": {"blocks_step_completion": True}},
        actor=user,
    )
    bp = result["blocking_policy"]
    assert bp["blocks_step_completion"] is True
    assert bp["blocks_signature"] is True
    assert bp["blocks_pre_qa_handoff"] is True
    assert bp["blocks_execution_progress"] is False  # default from normalize


@pytest.mark.django_db
def test_update_step_clear_optional_property(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    result = update_step(
        version=draft_version,
        step_key="fabrication_bulk",
        step_data={"instructions": None},
        actor=user,
    )
    assert result["instructions"] is None


@pytest.mark.django_db
def test_update_step_invalid_kind_raises(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    with pytest.raises(ValueError, match="Invalid step kind"):
        update_step(
            version=draft_version,
            step_key="fabrication_bulk",
            step_data={"kind": "invalid_kind"},
            actor=user,
        )


@pytest.mark.django_db
def test_update_step_rejects_contradictory_attachments_policy(
    draft_version: MMRVersion, user: Any
) -> None:
    add_step(
        version=draft_version,
        step_data={
            "key": "s1",
            "title": "Step 1",
            "kind": "preparation",
            "attachments_policy": {
                "supports_attachments": False,
                "attachment_kinds": [],
            },
        },
        actor=user,
    )
    with pytest.raises(ValueError, match="supports_attachments"):
        update_step(
            version=draft_version,
            step_key="s1",
            step_data={"attachments_policy": {"attachment_kinds": ["photo"]}},
            actor=user,
        )


@pytest.mark.django_db
def test_update_step_rejects_repeat_policy_without_mode_after_merge(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    with pytest.raises(ValueError, match=r"repeat_policy\.mode"):
        update_step(
            version=draft_version,
            step_key="fabrication_bulk",
            step_data={"repeat_policy": {"max_records": 3}},
            actor=user,
        )


# ---------------------------------------------------------------------------
# remove_step tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_remove_step_from_version(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    remove_step(version=draft_version, step_key="fabrication_bulk", actor=user)

    draft_version.refresh_from_db()
    assert draft_version.schema_json["stepOrder"] == []
    assert draft_version.schema_json["steps"] == {}


@pytest.mark.django_db
def test_remove_step_nonexistent_raises(draft_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="not found"):
        remove_step(version=draft_version, step_key="nonexistent", actor=user)


@pytest.mark.django_db
def test_remove_step_non_draft_raises(active_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="Only draft versions"):
        remove_step(version=active_version, step_key="any_key", actor=user)


@pytest.mark.django_db
def test_remove_step_records_audit_event(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    remove_step(version=draft_version, step_key="fabrication_bulk", actor=user)
    event = AuditEvent.objects.filter(event_type=AuditEventType.MMR_VERSION_STEP_REMOVED).first()
    assert event is not None
    assert event.metadata["step_key"] == "fabrication_bulk"


# ---------------------------------------------------------------------------
# reorder_steps tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reorder_steps_valid_permutation(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={"key": "b", "title": "B", "kind": "weighing"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={"key": "c", "title": "C", "kind": "packaging"},
        actor=user,
    )

    result = reorder_steps(
        version=draft_version,
        step_order=["c", "a", "b"],
        actor=user,
    )
    assert result == ["c", "a", "b"]

    draft_version.refresh_from_db()
    assert draft_version.schema_json["stepOrder"] == ["c", "a", "b"]


@pytest.mark.django_db
def test_reorder_steps_mismatched_set_raises(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=user,
    )
    with pytest.raises(ValueError, match="mismatch"):
        reorder_steps(
            version=draft_version,
            step_order=["a", "nonexistent"],
            actor=user,
        )


@pytest.mark.django_db
def test_reorder_steps_duplicate_keys_raises(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=user,
    )
    with pytest.raises(ValueError, match="duplicate"):
        reorder_steps(
            version=draft_version,
            step_order=["a", "a"],
            actor=user,
        )


@pytest.mark.django_db
def test_reorder_steps_non_draft_raises(active_version: MMRVersion, user: Any) -> None:
    with pytest.raises(ValueError, match="Only draft versions"):
        reorder_steps(
            version=active_version,
            step_order=[],
            actor=user,
        )


@pytest.mark.django_db
def test_reorder_steps_records_audit_event(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={"key": "b", "title": "B", "kind": "weighing"},
        actor=user,
    )
    reorder_steps(
        version=draft_version,
        step_order=["b", "a"],
        actor=user,
    )
    event = AuditEvent.objects.filter(event_type=AuditEventType.MMR_VERSION_STEPS_REORDERED).first()
    assert event is not None
    assert event.metadata["step_order"] == ["b", "a"]


# ---------------------------------------------------------------------------
# get_steps / get_step tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_steps_returns_ordered(draft_version: MMRVersion, user: Any) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={"key": "b", "title": "B", "kind": "weighing"},
        actor=user,
    )
    add_step(
        version=draft_version,
        step_data={"key": "c", "title": "C", "kind": "packaging"},
        actor=user,
    )

    steps = get_steps(version=draft_version)
    assert [s["key"] for s in steps] == ["a", "b", "c"]

    reorder_steps(version=draft_version, step_order=["c", "a", "b"], actor=user)
    steps = get_steps(version=draft_version)
    assert [s["key"] for s in steps] == ["c", "a", "b"]


@pytest.mark.django_db
def test_get_step_returns_single(
    draft_version: MMRVersion, sample_step_data: dict, user: Any
) -> None:
    add_step(version=draft_version, step_data=sample_step_data, actor=user)
    step = get_step(version=draft_version, step_key="fabrication_bulk")
    assert step["key"] == "fabrication_bulk"
    assert step["title"] == "Dossier de fabrication bulk"
    assert step["kind"] == "manufacturing"
    assert step["fields"] == []
    assert step["signature_policy"] == {"required": False, "meaning": "performed_by"}


@pytest.mark.django_db
def test_get_step_nonexistent_raises(draft_version: MMRVersion) -> None:
    with pytest.raises(ValueError, match="not found"):
        get_step(version=draft_version, step_key="nonexistent")


@pytest.mark.django_db
def test_get_steps_empty_version(draft_version: MMRVersion) -> None:
    assert get_steps(version=draft_version) == []


# ---------------------------------------------------------------------------
# Schema immutability across versions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_step_to_version_a_does_not_affect_version_b(mmr: MMR, user: Any) -> None:
    version_a = MMRVersion.objects.create(
        mmr=mmr,
        version_number=10,
        status=MMRVersionStatus.DRAFT,
        created_by=user,
        schema_json={},
    )
    version_b = MMRVersion.objects.create(
        mmr=mmr,
        version_number=11,
        status=MMRVersionStatus.DRAFT,
        created_by=user,
        schema_json={},
    )

    add_step(
        version=version_a,
        step_data={"key": "step_only_in_a", "title": "A only", "kind": "weighing"},
        actor=user,
    )

    version_b.refresh_from_db()
    assert version_b.schema_json == {}

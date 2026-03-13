from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from drf_spectacular.generators import SchemaGenerator

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.mmr.domain.step_management import add_step
from apps.mmr.models import MMR, MMRVersion, MMRVersionStatus
from apps.sites.models import Product, Site

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def configurator(site: Site) -> Any:
    user = get_user_model().objects.create_user(username="configurator", password="testpass")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.INTERNAL_CONFIGURATOR)
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


@pytest.fixture()
def draft_version(mmr: MMR, configurator: Any) -> MMRVersion:
    return MMRVersion.objects.create(
        mmr=mmr,
        version_number=1,
        status=MMRVersionStatus.DRAFT,
        created_by=configurator,
        schema_json={},
    )


@pytest.fixture()
def active_version(mmr: MMR, configurator: Any) -> MMRVersion:
    return MMRVersion.objects.create(
        mmr=mmr,
        version_number=2,
        status=MMRVersionStatus.ACTIVE,
        created_by=configurator,
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


def _steps_url(mmr: MMR, version: MMRVersion) -> str:
    return f"/api/v1/mmrs/{mmr.pk}/versions/{version.pk}/steps/"


def _step_detail_url(mmr: MMR, version: MMRVersion, step_key: str) -> str:
    return f"/api/v1/mmrs/{mmr.pk}/versions/{version.pk}/steps/{step_key}/"


def _reorder_url(mmr: MMR, version: MMRVersion) -> str:
    return f"/api/v1/mmrs/{mmr.pk}/versions/{version.pk}/steps/reorder/"


def _put_json(client: Any, path: str, payload: dict, *, csrf_token: str) -> Any:
    return client.put(path, payload, format="json", HTTP_X_CSRFTOKEN=csrf_token)


def _delete_json(client: Any, path: str, *, csrf_token: str) -> Any:
    return client.delete(path, HTTP_X_CSRFTOKEN=csrf_token)


# ---------------------------------------------------------------------------
# POST /steps/ — Add step
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_step_as_configurator(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"] == "fabrication_bulk"
    assert data["title"] == "Dossier de fabrication bulk"
    assert data["kind"] == "manufacturing"
    assert data["required"] is True
    assert data["fields"] == []
    assert data["signature_policy"] == {"required": False, "meaning": "performed_by"}


@pytest.mark.django_db
def test_add_step_as_operator_denied(
    operator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client(user=operator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_add_step_unauthenticated_denied(
    mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client()
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_add_step_csrf_required(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.post(
        _steps_url(mmr, draft_version),
        sample_step_data,
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_add_step_invalid_kind_returns_400(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        {"key": "s1", "title": "S1", "kind": "invalid_kind"},
        csrf_token=token,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_step_invalid_key_pattern_returns_400(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        {"key": "Bad-Key", "title": "T", "kind": "weighing"},
        csrf_token=token,
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_add_step_reserved_key_returns_409(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        {"key": "reorder", "title": "Reorder Step", "kind": "weighing"},
        csrf_token=token,
    )
    assert resp.status_code == 409
    assert "reserved" in resp.json()["detail"]


@pytest.mark.django_db
def test_add_step_rejects_contradictory_attachments_policy(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        {
            "key": "s1",
            "title": "Step 1",
            "kind": "weighing",
            "attachments_policy": {
                "supports_attachments": False,
                "attachment_kinds": ["photo"],
            },
        },
        csrf_token=token,
    )
    assert resp.status_code == 400
    assert "attachments_policy" in resp.json()["detail"]


@pytest.mark.django_db
def test_add_step_rejects_repeat_policy_without_mode(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        {
            "key": "s1",
            "title": "Step 1",
            "kind": "weighing",
            "repeat_policy": {"max_records": 3},
        },
        csrf_token=token,
    )
    assert resp.status_code == 400
    assert "repeat_policy" in resp.json()["detail"]


@pytest.mark.django_db
def test_add_step_duplicate_key_returns_409(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client(user=configurator)
    post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "type" in data
    assert "detail" in data


@pytest.mark.django_db
def test_add_step_non_draft_returns_409(
    configurator: Any, mmr: MMR, active_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _steps_url(mmr, active_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /steps/ — List steps
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_steps_returns_ordered(configurator: Any, mmr: MMR, draft_version: MMRVersion) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=configurator,
    )
    add_step(
        version=draft_version,
        step_data={"key": "b", "title": "B", "kind": "weighing"},
        actor=configurator,
    )
    client, _ = csrf_client(user=configurator)
    resp = client.get(_steps_url(mmr, draft_version))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["key"] == "a"
    assert data[1]["key"] == "b"
    # List serializer has minimal fields
    assert "instructions" not in data[0]
    assert "fields" not in data[0]


# ---------------------------------------------------------------------------
# GET /steps/{key}/ — Step detail
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_step_detail(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, _ = csrf_client(user=configurator)
    resp = client.get(_step_detail_url(mmr, draft_version, "fabrication_bulk"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "fabrication_bulk"
    assert data["instructions"] == "Saisir et verifier les informations bulk."
    assert data["fields"] == []
    assert data["signature_policy"] == {"required": False, "meaning": "performed_by"}


@pytest.mark.django_db
def test_get_step_not_found(configurator: Any, mmr: MMR, draft_version: MMRVersion) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.get(_step_detail_url(mmr, draft_version, "nonexistent"))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /steps/{key}/ — Update step
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_step_partial(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
        {"title": "Updated Title"},
        csrf_token=token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["kind"] == "manufacturing"  # unchanged


@pytest.mark.django_db
def test_update_step_csrf_required(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, _ = csrf_client(user=configurator)
    resp = client.put(
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
        {"title": "X"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_update_step_non_draft_returns_409(
    configurator: Any, mmr: MMR, active_version: MMRVersion
) -> None:
    # Active version with a step in schema_json
    active_version.schema_json = {
        "schemaVersion": "v1",
        "templateCode": "X",
        "templateName": "X",
        "product": {},
        "stepOrder": ["s1"],
        "steps": {"s1": {"key": "s1", "title": "S", "kind": "weighing"}},
    }
    active_version.save()

    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, active_version, "s1"),
        {"title": "X"},
        csrf_token=token,
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_update_step_partial_blocking_policy_preserves_existing_via_api(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    """End-to-end: partial blocking_policy update must merge, not replace."""
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
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fab"),
        {"blocking_policy": {"blocks_step_completion": True}},
        csrf_token=token,
    )
    assert resp.status_code == 200
    bp = resp.json()["blocking_policy"]
    assert bp["blocks_step_completion"] is True
    assert bp["blocks_signature"] is True
    assert bp["blocks_pre_qa_handoff"] is True
    assert bp["blocks_execution_progress"] is False


@pytest.mark.django_db
def test_update_step_ignores_key_in_payload(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
        {"key": "new_key", "title": "Updated"},
        csrf_token=token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "fabrication_bulk"
    assert data["title"] == "Updated"


@pytest.mark.django_db
def test_update_step_rejects_contradictory_attachments_policy_after_merge(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    add_step(
        version=draft_version,
        step_data={
            "key": "fab",
            "title": "Fab",
            "kind": "manufacturing",
            "attachments_policy": {
                "supports_attachments": False,
                "attachment_kinds": [],
            },
        },
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fab"),
        {"attachments_policy": {"attachment_kinds": ["photo"]}},
        csrf_token=token,
    )
    assert resp.status_code == 400
    assert "attachments_policy" in resp.json()["detail"]


@pytest.mark.django_db
def test_update_step_rejects_repeat_policy_without_mode_when_creating_new_policy(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
        {"repeat_policy": {"max_records": 3}},
        csrf_token=token,
    )
    assert resp.status_code == 400
    assert "repeat_policy" in resp.json()["detail"]


@pytest.mark.django_db
def test_update_step_allows_repeat_policy_partial_update_when_mode_already_exists(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    add_step(
        version=draft_version,
        step_data={
            "key": "fab",
            "title": "Fab",
            "kind": "manufacturing",
            "repeat_policy": {"mode": "single", "min_records": 1},
        },
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _put_json(
        client,
        _step_detail_url(mmr, draft_version, "fab"),
        {"repeat_policy": {"max_records": 3}},
        csrf_token=token,
    )
    assert resp.status_code == 200
    assert resp.json()["repeat_policy"] == {
        "mode": "single",
        "min_records": 1,
        "max_records": 3,
    }


# ---------------------------------------------------------------------------
# DELETE /steps/{key}/ — Remove step
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_step(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = _delete_json(
        client,
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
        csrf_token=token,
    )
    assert resp.status_code == 204


@pytest.mark.django_db
def test_delete_step_csrf_required(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    add_step(
        version=draft_version,
        step_data=sample_step_data,
        actor=configurator,
    )
    client, _ = csrf_client(user=configurator)
    resp = client.delete(
        _step_detail_url(mmr, draft_version, "fabrication_bulk"),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_step_non_draft_returns_409(
    configurator: Any, mmr: MMR, active_version: MMRVersion
) -> None:
    active_version.schema_json = {
        "schemaVersion": "v1",
        "templateCode": "X",
        "templateName": "X",
        "product": {},
        "stepOrder": ["s1"],
        "steps": {"s1": {"key": "s1", "title": "S", "kind": "weighing"}},
    }
    active_version.save()

    client, token = csrf_client(user=configurator)
    resp = _delete_json(
        client,
        _step_detail_url(mmr, active_version, "s1"),
        csrf_token=token,
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /steps/reorder/ — Reorder steps
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reorder_steps_valid(configurator: Any, mmr: MMR, draft_version: MMRVersion) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=configurator,
    )
    add_step(
        version=draft_version,
        step_data={"key": "b", "title": "B", "kind": "weighing"},
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _reorder_url(mmr, draft_version),
        {"step_order": ["b", "a"]},
        csrf_token=token,
    )
    assert resp.status_code == 200
    assert resp.json()["step_order"] == ["b", "a"]


@pytest.mark.django_db
def test_reorder_steps_mismatched_keys_returns_409(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "a", "title": "A", "kind": "preparation"},
        actor=configurator,
    )
    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _reorder_url(mmr, draft_version),
        {"step_order": ["a", "nonexistent"]},
        csrf_token=token,
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_reorder_steps_csrf_required(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, _ = csrf_client(user=configurator)
    resp = client.post(
        _reorder_url(mmr, draft_version),
        {"step_order": []},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_reorder_steps_non_draft_returns_409(
    configurator: Any, mmr: MMR, active_version: MMRVersion
) -> None:
    active_version.schema_json = {
        "schemaVersion": "v1",
        "templateCode": "X",
        "templateName": "X",
        "product": {},
        "stepOrder": ["s1", "s2"],
        "steps": {
            "s1": {"key": "s1", "title": "S1", "kind": "weighing"},
            "s2": {"key": "s2", "title": "S2", "kind": "packaging"},
        },
    }
    active_version.save()

    client, token = csrf_client(user=configurator)
    resp = post_json(
        client,
        _reorder_url(mmr, active_version),
        {"step_order": ["s2", "s1"]},
        csrf_token=token,
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Cross-site isolation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cross_site_configurator_denied(
    mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    other_site = Site.objects.create(code="paris", name="Paris")
    other_user = get_user_model().objects.create_user(username="other_config", password="testpass")
    SiteRoleAssignment.objects.create(
        user=other_user, site=other_site, role=SiteRole.INTERNAL_CONFIGURATOR
    )

    client, token = csrf_client(user=other_user)
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Problem-details error format
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_domain_error_uses_problem_details(
    configurator: Any, mmr: MMR, draft_version: MMRVersion, sample_step_data: dict
) -> None:
    client, token = csrf_client(user=configurator)
    post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    resp = post_json(
        client,
        _steps_url(mmr, draft_version),
        sample_step_data,
        csrf_token=token,
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "type" in data
    assert "title" in data
    assert "detail" in data


# ---------------------------------------------------------------------------
# Version detail includes step_count and has_steps
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_version_detail_includes_step_count(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    add_step(
        version=draft_version,
        step_data={"key": "s1", "title": "S1", "kind": "preparation"},
        actor=configurator,
    )
    add_step(
        version=draft_version,
        step_data={"key": "s2", "title": "S2", "kind": "weighing"},
        actor=configurator,
    )
    client, _ = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/{draft_version.pk}/")
    assert resp.status_code == 200
    assert resp.json()["step_count"] == 2


@pytest.mark.django_db
def test_version_list_includes_has_steps(
    configurator: Any, mmr: MMR, draft_version: MMRVersion
) -> None:
    client, _ = csrf_client(user=configurator)

    # Before adding steps
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/")
    data = resp.json()
    version_data = next(v for v in data if v["id"] == draft_version.pk)
    assert version_data["has_steps"] is False

    # After adding a step
    add_step(
        version=draft_version,
        step_data={"key": "s1", "title": "S1", "kind": "preparation"},
        actor=configurator,
    )
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/")
    data = resp.json()
    version_data = next(v for v in data if v["id"] == draft_version.pk)
    assert version_data["has_steps"] is True


# ---------------------------------------------------------------------------
# Nonexistent version/MMR returns 404
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_steps_nonexistent_version_returns_404(configurator: Any, mmr: MMR) -> None:
    client, _token = csrf_client(user=configurator)
    resp = client.get(f"/api/v1/mmrs/{mmr.pk}/versions/99999/steps/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_steps_nonexistent_mmr_returns_404(configurator: Any) -> None:
    client, _token = csrf_client(user=configurator)
    resp = client.get("/api/v1/mmrs/99999/versions/1/steps/")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Serializer unit tests (M2)
# ---------------------------------------------------------------------------


class TestStepCreateSerializerValidation:
    def test_rejects_invalid_kind(self) -> None:
        from apps.mmr.api.serializers import StepCreateSerializer

        s = StepCreateSerializer(data={"key": "s1", "title": "T", "kind": "bogus"})
        assert not s.is_valid()
        assert "kind" in s.errors

    def test_accepts_valid_kind(self) -> None:
        from apps.mmr.api.serializers import StepCreateSerializer

        s = StepCreateSerializer(data={"key": "s1", "title": "T", "kind": "weighing"})
        assert s.is_valid(), s.errors


class TestAttachmentsPolicySerializerShape:
    def test_valid_data(self) -> None:
        from apps.mmr.api.serializers import AttachmentsPolicySerializer

        s = AttachmentsPolicySerializer(
            data={"supports_attachments": True, "attachment_kinds": ["photo", "other"]}
        )
        assert s.is_valid(), s.errors

    def test_invalid_attachment_kind(self) -> None:
        from apps.mmr.api.serializers import AttachmentsPolicySerializer

        s = AttachmentsPolicySerializer(
            data={"supports_attachments": True, "attachment_kinds": ["invalid"]}
        )
        assert not s.is_valid()
        assert "attachment_kinds" in s.errors


class TestStepPolicyValidation:
    def test_create_serializer_rejects_attachment_kinds_without_supports(self) -> None:
        from apps.mmr.api.serializers import StepCreateSerializer

        s = StepCreateSerializer(
            data={
                "key": "s1",
                "title": "T",
                "kind": "weighing",
                "attachments_policy": {
                    "supports_attachments": False,
                    "attachment_kinds": ["photo"],
                },
            }
        )
        assert not s.is_valid()
        assert "attachments_policy" in s.errors

    def test_update_serializer_rejects_contradictory_attachments_after_merge(self) -> None:
        from apps.mmr.api.serializers import StepUpdateSerializer

        s = StepUpdateSerializer(
            data={"attachments_policy": {"attachment_kinds": ["photo"]}},
            partial=True,
            context={
                "current_step": {
                    "attachments_policy": {
                        "supports_attachments": False,
                        "attachment_kinds": [],
                    }
                }
            },
        )
        assert not s.is_valid()
        assert "attachments_policy" in s.errors

    def test_update_serializer_allows_attachment_kind_update_when_supports_enabled(self) -> None:
        from apps.mmr.api.serializers import StepUpdateSerializer

        s = StepUpdateSerializer(
            data={"attachments_policy": {"attachment_kinds": ["worksheet"]}},
            partial=True,
            context={
                "current_step": {
                    "attachments_policy": {
                        "supports_attachments": True,
                        "attachment_kinds": ["photo"],
                    }
                }
            },
        )
        assert s.is_valid(), s.errors

    def test_create_serializer_rejects_repeat_policy_without_mode(self) -> None:
        from apps.mmr.api.serializers import StepCreateSerializer

        s = StepCreateSerializer(
            data={
                "key": "s1",
                "title": "T",
                "kind": "weighing",
                "repeat_policy": {"max_records": 3},
            }
        )
        assert not s.is_valid()
        assert "repeat_policy" in s.errors

    def test_update_serializer_allows_repeat_policy_partial_update_when_mode_exists(self) -> None:
        from apps.mmr.api.serializers import StepUpdateSerializer

        s = StepUpdateSerializer(
            data={"repeat_policy": {"max_records": 3}},
            partial=True,
            context={"current_step": {"repeat_policy": {"mode": "single", "min_records": 1}}},
        )
        assert s.is_valid(), s.errors

    def test_update_serializer_rejects_repeat_policy_without_mode_after_merge(self) -> None:
        from apps.mmr.api.serializers import StepUpdateSerializer

        s = StepUpdateSerializer(
            data={"repeat_policy": {"max_records": 3}},
            partial=True,
            context={"current_step": {}},
        )
        assert not s.is_valid()
        assert "repeat_policy" in s.errors


class TestBlockingPolicySerializerShape:
    def test_valid_booleans(self) -> None:
        from apps.mmr.api.serializers import BlockingPolicySerializer

        s = BlockingPolicySerializer(
            data={
                "blocks_execution_progress": True,
                "blocks_step_completion": False,
                "blocks_signature": True,
                "blocks_pre_qa_handoff": False,
            }
        )
        assert s.is_valid(), s.errors


class TestRepeatPolicySerializerShape:
    def test_valid_data(self) -> None:
        from apps.mmr.api.serializers import RepeatPolicySerializer

        s = RepeatPolicySerializer(data={"mode": "per_shift", "min_records": 0, "max_records": 5})
        assert s.is_valid(), s.errors

    def test_invalid_mode(self) -> None:
        from apps.mmr.api.serializers import RepeatPolicySerializer

        s = RepeatPolicySerializer(data={"mode": "invalid_mode"})
        assert not s.is_valid()
        assert "mode" in s.errors


def test_step_openapi_schema_is_precise() -> None:
    schema = SchemaGenerator().get_schema(request=None, public=True)
    components = schema["components"]["schemas"]

    step_detail = components["StepDetail"]
    assert step_detail["properties"]["fields"]["items"]["$ref"] == "#/components/schemas/StepField"
    assert step_detail["properties"]["signature_policy"]["properties"]["meaning"]["enum"] == [
        "performed_by",
        "reviewed_by",
        "approved_by",
        "released_by",
    ]

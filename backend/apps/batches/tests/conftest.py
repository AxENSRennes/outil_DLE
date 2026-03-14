from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.batches.models import Batch
from apps.sites.models import Site

User = get_user_model()

REPO_ROOT = Path(__file__).resolve().parents[4]
PILOT_TEMPLATE_PATH = (
    REPO_ROOT / "_bmad-output" / "implementation-artifacts" / "mmr-version-example.json"
)


def load_pilot_template() -> dict[str, Any]:
    return dict(json.loads(PILOT_TEMPLATE_PATH.read_text()))


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="chr", name="Chateau-Renard")


@pytest.fixture()
def user(db: None) -> Any:
    return User.objects.create_user(username="operator1", password="testpass")


@pytest.fixture()
def pilot_snapshot() -> dict[str, Any]:
    return load_pilot_template()


@pytest.fixture()
def batch_pms_glitter(site: Site, user: Any, pilot_snapshot: dict[str, Any]) -> Batch:
    """Batch with PMS machine + with_glitter context."""
    return Batch.objects.create(
        site=site,
        batch_number="LOT-PMS-001",
        snapshot_json=pilot_snapshot,
        batch_context_json={
            "line_code": "PMS",
            "machine_code": "PMS",
            "format_family": "100mL",
            "glitter_mode": "with_glitter",
        },
        created_by=user,
    )


@pytest.fixture()
def operator_role(user: Any, site: Site) -> SiteRoleAssignment:
    return SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)


@pytest.fixture()
def batch_uni2(site: Site, user: Any, pilot_snapshot: dict[str, Any]) -> Batch:
    """Batch with UNI2 machine context."""
    return Batch.objects.create(
        site=site,
        batch_number="LOT-UNI2-001",
        snapshot_json=pilot_snapshot,
        batch_context_json={
            "line_code": "UNI2",
            "machine_code": "UNI2",
            "format_family": "100mL",
            "glitter_mode": "without_glitter",
        },
        created_by=user,
    )

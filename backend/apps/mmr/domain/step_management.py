from __future__ import annotations

import logging
import re
from typing import Any

from django.db import transaction

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.mmr.models import MMRVersion, MMRVersionStatus

logger = logging.getLogger(__name__)

VALID_STEP_KINDS = frozenset(
    {
        "preparation",
        "material_confirmation",
        "weighing",
        "manufacturing",
        "pre_qa_review",
        "in_process_control",
        "bulk_handover",
        "packaging",
        "finished_product_control",
        "review",
    }
)

STEP_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

_OPTIONAL_STEP_PROPERTIES = (
    "instructions",
    "attachments_policy",
    "applicability",
    "repeat_policy",
    "blocking_policy",
)


# ---------------------------------------------------------------------------
# Case-conversion helpers (snake_case ↔ camelCase for schema_json storage)
# ---------------------------------------------------------------------------


def _to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _to_snake_case(camel_str: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


def _dict_keys_to_camel(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively convert dict keys from snake_case to camelCase."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        camel_key = _to_camel_case(key)
        if isinstance(value, dict):
            result[camel_key] = _dict_keys_to_camel(value)
        elif isinstance(value, list):
            result[camel_key] = [
                _dict_keys_to_camel(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[camel_key] = value
    return result


def _dict_keys_to_snake(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively convert dict keys from camelCase to snake_case."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        snake_key = _to_snake_case(key)
        if isinstance(value, dict):
            result[snake_key] = _dict_keys_to_snake(value)
        elif isinstance(value, list):
            result[snake_key] = [
                _dict_keys_to_snake(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[snake_key] = value
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_schema_initialized(version: MMRVersion) -> dict[str, Any]:
    """Initialize schema_json header from parent MMR and Product if empty."""
    schema: dict[str, Any] = version.schema_json
    if schema and "schemaVersion" in schema:
        return schema

    mmr = version.mmr
    product = mmr.product
    return {
        "schemaVersion": "v1",
        "templateCode": mmr.code,
        "templateName": mmr.name,
        "product": {
            "productCode": product.code,
            "productName": product.name,
            "family": product.family,
            "formatLabel": product.format_label,
        },
        "stepOrder": [],
        "steps": {},
    }


def _validate_draft(version: MMRVersion) -> None:
    if version.status != MMRVersionStatus.DRAFT:
        raise ValueError(
            f"Cannot modify a {version.status} version. Only draft versions can be edited."
        )


def _validate_step_key(key: str) -> None:
    if len(key) > 100:
        raise ValueError(f"Step key must be at most 100 characters, got {len(key)}.")
    if not STEP_KEY_PATTERN.match(key):
        raise ValueError(
            f"Invalid step key '{key}'. Must start with a lowercase letter "
            f"and contain only lowercase letters, digits, or underscores."
        )


def _validate_step_kind(kind: str) -> None:
    if kind not in VALID_STEP_KINDS:
        raise ValueError(
            f"Invalid step kind '{kind}'. Must be one of: {', '.join(sorted(VALID_STEP_KINDS))}."
        )


def _audit_metadata(version: MMRVersion, **extra: Any) -> dict:
    return {
        "mmr_id": version.mmr.pk,
        "mmr_code": version.mmr.code,
        "version_id": version.pk,
        "version_number": version.version_number,
        **extra,
    }


def _normalize_step_output(step_dict: dict[str, Any]) -> dict[str, Any]:
    """Ensure all expected properties are present in the snake_case output."""
    defaults: dict[str, Any] = {
        "instructions": None,
        "attachments_policy": None,
        "applicability": None,
        "repeat_policy": None,
        "blocking_policy": None,
        "signature_policy": {"required": False, "meaning": "performed_by"},
        "fields": [],
        "required": True,
    }
    for key, default in defaults.items():
        step_dict.setdefault(key, default)
    return step_dict


# ---------------------------------------------------------------------------
# Public domain API
# ---------------------------------------------------------------------------


def add_step(*, version: MMRVersion, step_data: dict, actor: Any) -> dict:
    """Add step to draft version.

    ``step_data`` uses snake_case keys (from the API serializer).
    Auto-injects ``fields: []`` and default ``signaturePolicy``
    since those are out of scope for this story.
    """
    with transaction.atomic():
        version = (
            MMRVersion.objects.select_for_update()
            .select_related("mmr", "mmr__site", "mmr__product")
            .get(pk=version.pk)
        )
        _validate_draft(version)

        key = step_data["key"]
        _validate_step_key(key)
        _validate_step_kind(step_data["kind"])

        schema = _ensure_schema_initialized(version)

        if key in schema.get("steps", {}):
            raise ValueError(f"Step key '{key}' already exists in this version.")

        # Build step definition with camelCase keys for schema_json
        step_def: dict[str, Any] = {
            "key": key,
            "title": step_data["title"],
            "kind": step_data["kind"],
            "required": step_data.get("required", True),
        }

        # Add optional properties
        for prop in _OPTIONAL_STEP_PROPERTIES:
            if prop in step_data and step_data[prop] is not None:
                step_def[prop] = step_data[prop]

        # Convert all keys to camelCase for schema_json storage
        step_def = _dict_keys_to_camel(step_def)

        # Auto-inject out-of-scope defaults
        step_def["fields"] = []
        step_def["signaturePolicy"] = {"required": False, "meaning": "performed_by"}

        schema["stepOrder"].append(key)
        schema["steps"][key] = step_def

        version.schema_json = schema
        version.save(update_fields=["schema_json", "updated_at"])

        record_audit_event(
            AuditEventType.MMR_VERSION_STEP_ADDED,
            actor=actor,
            site=version.mmr.site,
            metadata=_audit_metadata(version, step_key=key),
        )

    return _normalize_step_output(_dict_keys_to_snake(step_def))


def update_step(*, version: MMRVersion, step_key: str, step_data: dict, actor: Any) -> dict:
    """Update existing step. ``step_data`` is partial (only changed fields)."""
    with transaction.atomic():
        version = (
            MMRVersion.objects.select_for_update()
            .select_related("mmr", "mmr__site", "mmr__product")
            .get(pk=version.pk)
        )
        _validate_draft(version)

        schema = version.schema_json or {}
        steps = schema.get("steps", {})

        if step_key not in steps:
            raise ValueError(f"Step '{step_key}' not found in this version.")

        if "kind" in step_data:
            _validate_step_kind(step_data["kind"])

        step_def = steps[step_key]

        # Merge updated properties (convert snake_case input to camelCase)
        for prop, value in step_data.items():
            if prop == "key":
                continue  # Step key is immutable
            camel_prop = _to_camel_case(prop)
            if value is not None:
                if isinstance(value, dict):
                    step_def[camel_prop] = _dict_keys_to_camel(value)
                else:
                    step_def[camel_prop] = value
            else:
                # Setting to null removes the optional property
                step_def.pop(camel_prop, None)

        schema["steps"][step_key] = step_def
        version.schema_json = schema
        version.save(update_fields=["schema_json", "updated_at"])

        record_audit_event(
            AuditEventType.MMR_VERSION_STEP_UPDATED,
            actor=actor,
            site=version.mmr.site,
            metadata=_audit_metadata(version, step_key=step_key),
        )

    return _normalize_step_output(_dict_keys_to_snake(step_def))


def remove_step(*, version: MMRVersion, step_key: str, actor: Any) -> None:
    """Remove step from draft version."""
    with transaction.atomic():
        version = (
            MMRVersion.objects.select_for_update()
            .select_related("mmr", "mmr__site")
            .get(pk=version.pk)
        )
        _validate_draft(version)

        schema = version.schema_json or {}
        steps = schema.get("steps", {})
        step_order = schema.get("stepOrder", [])

        if step_key not in steps:
            raise ValueError(f"Step '{step_key}' not found in this version.")

        del steps[step_key]
        step_order.remove(step_key)

        schema["steps"] = steps
        schema["stepOrder"] = step_order
        version.schema_json = schema
        version.save(update_fields=["schema_json", "updated_at"])

        record_audit_event(
            AuditEventType.MMR_VERSION_STEP_REMOVED,
            actor=actor,
            site=version.mmr.site,
            metadata=_audit_metadata(version, step_key=step_key),
        )


def reorder_steps(*, version: MMRVersion, step_order: list[str], actor: Any) -> list[str]:
    """Replace ``stepOrder``. Must contain exactly the same set of keys."""
    with transaction.atomic():
        version = (
            MMRVersion.objects.select_for_update()
            .select_related("mmr", "mmr__site")
            .get(pk=version.pk)
        )
        _validate_draft(version)

        schema = version.schema_json or {}
        existing_keys = set(schema.get("steps", {}).keys())
        new_keys = set(step_order)

        if len(step_order) != len(set(step_order)):
            raise ValueError("Step order contains duplicate keys.")

        if existing_keys != new_keys:
            missing = existing_keys - new_keys
            extra = new_keys - existing_keys
            parts = []
            if missing:
                parts.append(f"missing keys: {sorted(missing)}")
            if extra:
                parts.append(f"unknown keys: {sorted(extra)}")
            raise ValueError(f"Step order mismatch: {', '.join(parts)}.")

        schema["stepOrder"] = step_order
        version.schema_json = schema
        version.save(update_fields=["schema_json", "updated_at"])

        record_audit_event(
            AuditEventType.MMR_VERSION_STEPS_REORDERED,
            actor=actor,
            site=version.mmr.site,
            metadata=_audit_metadata(version, step_order=step_order),
        )

    return step_order


def get_steps(*, version: MMRVersion) -> list[dict]:
    """Return steps ordered by ``stepOrder``. Output uses snake_case keys."""
    version.refresh_from_db(fields=["schema_json"])
    schema = version.schema_json or {}
    step_order = schema.get("stepOrder", [])
    steps = schema.get("steps", {})
    orphaned = [key for key in step_order if key not in steps]
    if orphaned:
        logger.warning(
            "MMRVersion %s: stepOrder references keys not in steps: %s",
            version.pk,
            orphaned,
        )
    return [
        _normalize_step_output(_dict_keys_to_snake(steps[key]))
        for key in step_order
        if key in steps
    ]


def get_step(*, version: MMRVersion, step_key: str) -> dict:
    """Return single step. Raises ``ValueError`` if not found."""
    version.refresh_from_db(fields=["schema_json"])
    schema = version.schema_json or {}
    steps = schema.get("steps", {})
    if step_key not in steps:
        raise ValueError(f"Step '{step_key}' not found in this version.")
    return _normalize_step_output(_dict_keys_to_snake(steps[step_key]))

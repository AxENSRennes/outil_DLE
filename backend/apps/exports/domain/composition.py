"""Dossier composition domain service.

Resolves which sub-documents and controls are required for a specific batch
based on its operational context and the associated DossierProfile rules.
"""

from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.batches.models import Batch
from apps.exports.models import (
    ApplicabilityStatus,
    BatchDossierStructure,
    DossierElement,
    DossierElementType,
    DossierProfile,
)


class DossierCompositionError(Exception):
    """Raised when dossier composition fails due to invalid configuration."""


SUPPORTED_OPERATORS = {"eq", "neq", "in", "not_in", "truthy", "falsy"}
ACTIVE_STRUCTURE_CONSTRAINT = "exports_bds_one_active_per_batch"


def resolve_dossier_structure(
    batch: Batch,
    *,
    force: bool = False,
    actor: Any | None = None,
    site: Any | None = None,
) -> BatchDossierStructure:
    """Resolve the dossier structure for a batch from its context and profile.

    Idempotent: returns the existing active structure if one exists, unless
    ``force=True`` is passed to trigger a fresh resolution (the old structure
    is deactivated but preserved for audit).

    Args:
        batch: The batch to resolve the dossier structure for.
        force: If True, deactivate existing structure and create a new one.
        actor: Optional user for audit trail.
        site: Optional site for audit trail.

    Returns:
        The resolved (or existing) ``BatchDossierStructure`` with its elements.

    Raises:
        DossierCompositionError: If no ``DossierProfile`` is associated with
            the batch's MMR version.
    """
    if not force:
        existing = (
            BatchDossierStructure.objects.filter(batch=batch, is_active=True)
            .select_related("dossier_profile")
            .prefetch_related("elements")
            .first()
        )
        if existing is not None:
            return existing

    profile = _get_dossier_profile(batch)
    context = _extract_batch_context(batch)
    element_catalog = _build_element_catalog(profile)
    known_identifiers = {entry["identifier"] for entry in element_catalog}

    _validate_profile_configuration(profile, known_identifiers)
    required_ids, not_applicable_ids = _evaluate_rules(profile, context)

    try:
        with transaction.atomic():
            if force:
                BatchDossierStructure.objects.filter(batch=batch, is_active=True).update(
                    is_active=False,
                )

            structure = BatchDossierStructure.objects.create(
                batch=batch,
                dossier_profile=profile,
                context_snapshot=context,
                is_active=True,
            )

            elements_to_create: list[DossierElement] = []
            for order, entry in enumerate(element_catalog, start=1):
                identifier = entry["identifier"]
                if identifier in not_applicable_ids:
                    applicability = ApplicabilityStatus.NOT_APPLICABLE
                elif identifier in required_ids:
                    applicability = ApplicabilityStatus.REQUIRED
                else:
                    # Elements not mentioned in any rule are excluded entirely
                    continue

                elements_to_create.append(
                    DossierElement(
                        structure=structure,
                        element_identifier=identifier,
                        element_type=entry.get("type", DossierElementType.SUB_DOCUMENT),
                        display_order=order,
                        applicability=applicability,
                        title=entry.get("title", ""),
                        metadata=entry.get("metadata", {}),
                    )
                )

            DossierElement.objects.bulk_create(elements_to_create)

            record_audit_event(
                AuditEventType.DOSSIER_RESOLVED,
                actor=actor,
                site=site,
                metadata={
                    "batch_id": batch.pk,
                    "profile_id": profile.pk,
                    "structure_id": structure.pk,
                    "force": force,
                },
            )
    except IntegrityError as exc:
        # Unique constraint race: another request resolved concurrently.
        # Fail-closed to idempotent — return the winning row.
        if _is_active_structure_race(exc):
            existing = (
                BatchDossierStructure.objects.filter(batch=batch, is_active=True)
                .select_related("dossier_profile")
                .prefetch_related("elements")
                .first()
            )
            if existing is not None:
                return existing
        raise  # pragma: no cover - unexpected state

    # Re-fetch with prefetched elements for a consistent return value.
    return (
        BatchDossierStructure.objects.filter(pk=structure.pk)
        .select_related("dossier_profile")
        .prefetch_related("elements")
        .get()
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_dossier_profile(batch: Batch) -> DossierProfile:
    """Load the DossierProfile linked to the batch's MMR version."""
    try:
        return DossierProfile.objects.select_related("mmr_version").get(
            mmr_version_id=batch.mmr_version_id,
        )
    except DossierProfile.DoesNotExist:
        raise DossierCompositionError(
            f"No DossierProfile found for MMRVersion {batch.mmr_version_id}. "
            "Cannot resolve dossier structure without composition rules."
        ) from None


def _extract_batch_context(batch: Batch) -> dict[str, Any]:
    """Extract contextual attributes from the batch for rule evaluation."""
    ctx: dict[str, Any] = batch.batch_context_json or {}
    return dict(ctx)  # Return a shallow copy to avoid mutation.


def _evaluate_rules(
    profile: DossierProfile,
    context: dict[str, Any],
) -> tuple[set[str], set[str]]:
    """Evaluate composition rules and return (required_ids, not_applicable_ids).

    The rule engine supports:
    - ``default_required``: elements always required regardless of context.
    - ``conditions``: list of conditional rules with operators ``eq``, ``neq``,
      ``in``, ``not_in``, ``truthy``, ``falsy``.

    Elements explicitly excluded by a rule become not-applicable.
    Elements included by a default or condition become required.
    """
    rules: dict[str, Any] = profile.rules or {}

    required: set[str] = set()
    not_applicable: set[str] = set()

    # Default-required elements — always included.
    default_required: list[str] = rules.get("default_required", [])
    required.update(default_required)

    # Conditional rules.
    conditions: list[dict[str, Any]] = rules.get("conditions", [])
    for condition in conditions:
        if _condition_matches(condition, context):
            include: list[str] = condition.get("include_elements", [])
            exclude: list[str] = condition.get("exclude_elements", [])
            required.update(include)
            not_applicable.update(exclude)
        else:
            # When a condition does NOT match, its include_elements are
            # marked not-applicable (they only apply when condition is true).
            include_when_true: list[str] = condition.get("include_elements", [])
            not_applicable.update(include_when_true)

    # If an element is both required (default or matched condition) and
    # not-applicable (failed condition), required wins.
    not_applicable -= required

    return required, not_applicable


def _condition_matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluate a single condition against the batch context."""
    context_key: str = condition.get("context_key", "")
    operator: str = condition.get("operator", "eq")
    expected = condition.get("value")
    key_present = context_key in context
    actual = context.get(context_key)

    # Absent keys must not silently satisfy any operator.
    if not key_present:
        return False

    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        if not isinstance(expected, list):
            return False
        return actual in expected
    if operator == "not_in":
        if not isinstance(expected, list):
            return False
        return actual not in expected
    if operator == "truthy":
        return bool(actual)
    if operator == "falsy":
        return not bool(actual)

    return False


def _validate_profile_configuration(
    profile: DossierProfile,
    known_identifiers: set[str],
) -> None:
    """Validate catalog/rule consistency before any write happens."""
    rules: dict[str, Any] = profile.rules or {}

    _validate_identifier_list(
        rules.get("default_required", []),
        field_name="default_required",
        known_identifiers=known_identifiers,
    )

    conditions = rules.get("conditions", [])
    if not isinstance(conditions, list):
        raise DossierCompositionError(
            f"DossierProfile {profile.pk} has invalid 'conditions'; expected a list.",
        )

    for index, condition in enumerate(conditions, start=1):
        if not isinstance(condition, dict):
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} condition #{index} must be an object.",
            )

        context_key = condition.get("context_key")
        if not isinstance(context_key, str) or not context_key.strip():
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} condition #{index} has an invalid context_key.",
            )

        operator = condition.get("operator", "eq")
        if operator not in SUPPORTED_OPERATORS:
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} condition #{index} uses unsupported operator "
                f"'{operator}'.",
            )

        expected = condition.get("value")
        if operator in {"in", "not_in"} and not isinstance(expected, list):
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} condition #{index} requires a list value for "
                f"operator '{operator}'.",
            )

        _validate_identifier_list(
            condition.get("include_elements", []),
            field_name=f"conditions[{index}].include_elements",
            known_identifiers=known_identifiers,
        )
        _validate_identifier_list(
            condition.get("exclude_elements", []),
            field_name=f"conditions[{index}].exclude_elements",
            known_identifiers=known_identifiers,
        )


def _validate_identifier_list(
    raw_value: Any,
    *,
    field_name: str,
    known_identifiers: set[str],
) -> list[str]:
    """Validate a list of catalog identifiers and fail closed on bad config."""
    if not isinstance(raw_value, list):
        raise DossierCompositionError(f"DossierProfile field '{field_name}' must be a list.")

    identifiers: list[str] = []
    unknown_identifiers: list[str] = []
    for item in raw_value:
        if not isinstance(item, str) or not item.strip():
            raise DossierCompositionError(
                f"DossierProfile field '{field_name}' must contain non-empty string identifiers.",
            )
        identifiers.append(item)
        if item not in known_identifiers:
            unknown_identifiers.append(item)

    if unknown_identifiers:
        formatted = ", ".join(sorted(unknown_identifiers))
        raise DossierCompositionError(
            f"DossierProfile field '{field_name}' references unknown elements: {formatted}.",
        )

    return identifiers


def _build_element_catalog(profile: DossierProfile) -> list[dict[str, Any]]:
    """Build an ordered list of all possible elements from the profile.

    Each entry has at minimum ``identifier`` and optionally ``type``, ``title``,
    and ``metadata`` keys.
    """
    elements: list[Any] = profile.elements or []
    catalog: list[dict[str, Any]] = []
    seen_identifiers: set[str] = set()

    for index, entry in enumerate(elements, start=1):
        if isinstance(entry, str):
            identifier = entry
            normalized_entry = {"identifier": identifier}
        elif isinstance(entry, dict) and "identifier" in entry:
            identifier = entry["identifier"]
            normalized_entry = entry
        else:
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} element #{index} must be a string or object "
                "with an identifier.",
            )

        if not isinstance(identifier, str) or not identifier.strip():
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} element #{index} has an invalid identifier.",
            )

        if identifier in seen_identifiers:
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} defines duplicate element identifier '{identifier}'.",
            )

        element_type = normalized_entry.get("type", DossierElementType.SUB_DOCUMENT)
        if element_type not in DossierElementType.values:
            raise DossierCompositionError(
                f"DossierProfile {profile.pk} element '{identifier}' uses unsupported type "
                f"'{element_type}'.",
            )

        seen_identifiers.add(identifier)
        catalog.append(normalized_entry)

    return catalog


def _is_active_structure_race(exc: IntegrityError) -> bool:
    """Detect the expected concurrent create race on the active-structure constraint."""
    cause = exc.__cause__
    diag = getattr(cause, "diag", None)
    constraint_name = getattr(diag, "constraint_name", None)
    if constraint_name == ACTIVE_STRUCTURE_CONSTRAINT:
        return True

    # Fallback: require unique-violation sqlstate AND constraint name in message.
    sqlstate = getattr(cause, "sqlstate", None)
    return sqlstate == "23505" and ACTIVE_STRUCTURE_CONSTRAINT in str(exc)

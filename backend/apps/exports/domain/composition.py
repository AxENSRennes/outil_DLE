"""Dossier composition domain service.

Resolves which sub-documents and controls are required for a specific batch
based on its operational context and the associated DossierProfile rules.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

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


def resolve_dossier_structure(
    batch: Batch,
    *,
    force: bool = False,
) -> BatchDossierStructure:
    """Resolve the dossier structure for a batch from its context and profile.

    Idempotent: returns the existing active structure if one exists, unless
    ``force=True`` is passed to trigger a fresh resolution (the old structure
    is deactivated but preserved for audit).

    Args:
        batch: The batch to resolve the dossier structure for.
        force: If True, deactivate existing structure and create a new one.

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

    required_ids, not_applicable_ids = _evaluate_rules(profile, context)
    element_catalog = _build_element_catalog(profile)

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
            mmr_version=batch.mmr_version,
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
    actual = context.get(context_key)

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
            return True
        return actual not in expected
    if operator == "truthy":
        return bool(actual)
    if operator == "falsy":
        return not bool(actual)

    return False


def _build_element_catalog(profile: DossierProfile) -> list[dict[str, Any]]:
    """Build an ordered list of all possible elements from the profile.

    Each entry has at minimum ``identifier`` and optionally ``type``, ``title``,
    and ``metadata`` keys.
    """
    elements: list[Any] = profile.elements or []
    catalog: list[dict[str, Any]] = []

    for entry in elements:
        if isinstance(entry, str):
            catalog.append({"identifier": entry})
        elif isinstance(entry, dict) and "identifier" in entry:
            catalog.append(entry)

    return catalog

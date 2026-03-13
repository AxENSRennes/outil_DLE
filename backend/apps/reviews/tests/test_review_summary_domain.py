"""Unit tests for review summary domain logic (severity, completeness, flags)."""

from __future__ import annotations

from apps.reviews.domain.review_summary import (
    FlagCounts,
    StepSummary,
    build_flagged_steps,
    derive_traffic_light_severity,
    evaluate_checklist,
    evaluate_flag_counts,
    evaluate_integrity_flags,
    evaluate_signature_completeness,
    evaluate_step_completeness,
)

# ---------------------------------------------------------------------------
# evaluate_step_completeness
# ---------------------------------------------------------------------------


def test_step_completeness_all_signed() -> None:
    steps = [
        {"status": "signed"},
        {"status": "signed"},
        {"status": "signed"},
    ]
    result = evaluate_step_completeness(steps)
    assert result == StepSummary(total=3, not_started=0, in_progress=0, complete=0, signed=3)


def test_step_completeness_mixed() -> None:
    steps = [
        {"status": "not_started"},
        {"status": "in_progress"},
        {"status": "complete"},
        {"status": "signed"},
    ]
    result = evaluate_step_completeness(steps)
    assert result == StepSummary(total=4, not_started=1, in_progress=1, complete=1, signed=1)


def test_step_completeness_empty() -> None:
    result = evaluate_step_completeness([])
    assert result == StepSummary(total=0, not_started=0, in_progress=0, complete=0, signed=0)


def test_step_completeness_all_complete() -> None:
    steps = [{"status": "complete"}, {"status": "complete"}]
    result = evaluate_step_completeness(steps)
    assert result == StepSummary(total=2, not_started=0, in_progress=0, complete=2, signed=0)


# ---------------------------------------------------------------------------
# evaluate_signature_completeness / evaluate_integrity_flags
# ---------------------------------------------------------------------------


def test_signature_completeness_counts_missing_required_signatures() -> None:
    steps = [
        {"requires_signature": True, "has_signature": False},
        {"requires_signature": True, "has_signature": True},
        {"requires_signature": False, "has_signature": False},
    ]
    assert evaluate_signature_completeness(steps) == 1


def test_integrity_flags_count_review_required_and_blocking_exceptions() -> None:
    steps = [
        {
            "changed_since_review": True,
            "changed_since_signature": False,
            "review_required": True,
            "has_open_exception": True,
            "open_exception_is_blocking": True,
        },
        {
            "changed_since_review": False,
            "changed_since_signature": True,
            "review_required": False,
            "has_open_exception": True,
            "open_exception_is_blocking": False,
        },
    ]
    result = evaluate_integrity_flags(steps)
    assert result == {
        "changed_since_review": 1,
        "changed_since_signature": 1,
        "review_required": 1,
        "open_exceptions": 2,
        "blocking_open_exceptions": 1,
    }


# ---------------------------------------------------------------------------
# evaluate_flag_counts
# ---------------------------------------------------------------------------


def test_flag_counts_no_issues() -> None:
    steps = [
        {
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "has_open_exception": False,
        },
    ]
    result = evaluate_flag_counts(steps)
    assert result == FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
        review_required=0,
        blocking_open_exceptions=0,
    )


def test_flag_counts_missing_data() -> None:
    steps = [
        {"required_data_complete": False},
        {"required_data_complete": True},
        {"required_data_complete": False},
    ]
    result = evaluate_flag_counts(steps)
    assert result.missing_required_data == 2


def test_flag_counts_missing_signatures() -> None:
    steps = [
        {"requires_signature": True, "has_signature": False},
        {"requires_signature": True, "has_signature": True},
        {"requires_signature": False, "has_signature": False},
    ]
    result = evaluate_flag_counts(steps)
    assert result.missing_required_signatures == 1


def test_flag_counts_changed_since_review() -> None:
    steps = [
        {"changed_since_review": True},
        {"changed_since_review": False},
    ]
    result = evaluate_flag_counts(steps)
    assert result.changed_since_review == 1


def test_flag_counts_changed_since_signature() -> None:
    steps = [
        {"changed_since_signature": True},
        {"changed_since_signature": True},
    ]
    result = evaluate_flag_counts(steps)
    assert result.changed_since_signature == 2


def test_flag_counts_open_exceptions() -> None:
    steps = [{"has_open_exception": True, "open_exception_is_blocking": True}]
    result = evaluate_flag_counts(steps)
    assert result.open_exceptions == 1
    assert result.blocking_open_exceptions == 1


def test_flag_counts_review_required() -> None:
    steps = [{"review_required": True}, {"review_required": False}]
    result = evaluate_flag_counts(steps)
    assert result.review_required == 1


# ---------------------------------------------------------------------------
# evaluate_checklist
# ---------------------------------------------------------------------------


def test_checklist_all_present() -> None:
    items = [
        {"document_name": "doc-a", "is_present": True},
        {"document_name": "doc-b", "is_present": True},
    ]
    result = evaluate_checklist(items)
    assert result.expected_documents == 2
    assert result.present_documents == 2
    assert result.missing_documents == ()


def test_checklist_some_missing() -> None:
    items = [
        {"document_name": "doc-a", "is_present": True},
        {"document_name": "doc-b", "is_present": False},
        {"document_name": "doc-c", "is_present": False},
    ]
    result = evaluate_checklist(items)
    assert result.expected_documents == 3
    assert result.present_documents == 1
    assert result.missing_documents == ("doc-b", "doc-c")


def test_checklist_empty() -> None:
    result = evaluate_checklist([])
    assert result.expected_documents == 0
    assert result.present_documents == 0
    assert result.missing_documents == ()


# ---------------------------------------------------------------------------
# build_flagged_steps
# ---------------------------------------------------------------------------


def test_flagged_steps_no_flags() -> None:
    steps = [
        {
            "id": 1,
            "reference": "Step 1",
            "status": "complete",
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "has_open_exception": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert result == ()


def test_flagged_steps_red_severity() -> None:
    steps = [
        {
            "id": 7,
            "reference": "Step 7 - Weighing",
            "status": "in_progress",
            "required_data_complete": False,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "has_open_exception": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].step_id == 7
    assert result[0].severity == "red"
    assert "missing_required_data" in result[0].flags


def test_flagged_steps_amber_severity() -> None:
    steps = [
        {
            "id": 5,
            "reference": "Step 5 - Filling",
            "status": "signed",
            "required_data_complete": True,
            "requires_signature": True,
            "has_signature": True,
            "changed_since_review": True,
            "changed_since_signature": False,
            "has_open_exception": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "amber"
    assert "step_incomplete" not in result[0].flags
    assert "changed_since_review" in result[0].flags


def test_flagged_steps_review_required_is_amber() -> None:
    steps = [
        {
            "id": 9,
            "reference": "Step 9 - Review",
            "status": "complete",
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "review_required": True,
            "has_open_exception": False,
            "open_exception_is_blocking": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "amber"
    assert "review_required" in result[0].flags


def test_flagged_steps_not_started_is_amber_and_visible() -> None:
    steps = [
        {
            "id": 10,
            "reference": "Step 10 - Preparation",
            "status": "not_started",
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "review_required": False,
            "has_open_exception": False,
            "open_exception_is_blocking": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "amber"
    assert result[0].flags == ("step_incomplete",)


def test_flagged_steps_in_progress_is_amber_and_visible() -> None:
    steps = [
        {
            "id": 11,
            "reference": "Step 11 - Mixing",
            "status": "in_progress",
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "review_required": False,
            "has_open_exception": False,
            "open_exception_is_blocking": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "amber"
    assert result[0].flags == ("step_incomplete",)


def test_flagged_steps_missing_signature_is_red() -> None:
    steps = [
        {
            "id": 3,
            "reference": "Step 3 - Mixing",
            "status": "complete",
            "required_data_complete": True,
            "requires_signature": True,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "has_open_exception": False,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "red"
    assert "missing_required_signature" in result[0].flags


def test_flagged_steps_blocking_exception_is_red() -> None:
    steps = [
        {
            "id": 4,
            "reference": "Step 4 - Exception",
            "status": "complete",
            "required_data_complete": True,
            "requires_signature": False,
            "has_signature": False,
            "changed_since_review": False,
            "changed_since_signature": False,
            "review_required": False,
            "has_open_exception": True,
            "open_exception_is_blocking": True,
        },
    ]
    result = build_flagged_steps(steps)
    assert len(result) == 1
    assert result[0].severity == "red"
    assert "open_exception" in result[0].flags


# ---------------------------------------------------------------------------
# derive_traffic_light_severity
# ---------------------------------------------------------------------------


def test_severity_green() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=0, signed=3)
    assert derive_traffic_light_severity(flags, step_summary) == "green"


def test_severity_red_missing_data() -> None:
    flags = FlagCounts(
        missing_required_data=1,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=3, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "red"


def test_severity_red_missing_signatures() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=2,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=3, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "red"


def test_severity_red_open_exceptions() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=1,
        blocking_open_exceptions=1,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=3, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "red"


def test_severity_amber_non_blocking_open_exceptions() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=1,
        blocking_open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=3, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_amber_changed_since_review() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=1,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=0, signed=3)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_amber_review_required() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
        review_required=1,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=0, signed=3)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_amber_changed_since_signature() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=1,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=0, complete=0, signed=3)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_amber_steps_in_progress() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=0, in_progress=1, complete=2, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_amber_steps_not_started() -> None:
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=3, not_started=1, in_progress=0, complete=2, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "amber"


def test_severity_green_empty_batch() -> None:
    """Edge case: batch with no steps returns green."""
    flags = FlagCounts(
        missing_required_data=0,
        missing_required_signatures=0,
        changed_since_review=0,
        changed_since_signature=0,
        open_exceptions=0,
    )
    step_summary = StepSummary(total=0, not_started=0, in_progress=0, complete=0, signed=0)
    assert derive_traffic_light_severity(flags, step_summary) == "green"

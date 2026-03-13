from __future__ import annotations

from rest_framework import serializers


class StepSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    not_started = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    complete = serializers.IntegerField()
    signed = serializers.IntegerField()


class FlagCountsSerializer(serializers.Serializer):
    missing_required_data = serializers.IntegerField()
    missing_required_signatures = serializers.IntegerField()
    changed_since_review = serializers.IntegerField()
    changed_since_signature = serializers.IntegerField()
    open_exceptions = serializers.IntegerField()
    review_required = serializers.IntegerField()
    blocking_open_exceptions = serializers.IntegerField()


class ChecklistSummarySerializer(serializers.Serializer):
    expected_documents = serializers.IntegerField()
    present_documents = serializers.IntegerField()
    missing_documents = serializers.ListField(child=serializers.CharField())


class FlaggedStepSerializer(serializers.Serializer):
    step_id = serializers.IntegerField()
    step_reference = serializers.CharField()
    step_status = serializers.CharField()
    flags = serializers.ListField(child=serializers.CharField())
    severity = serializers.ChoiceField(choices=["green", "amber", "red"])


class ReviewSummarySerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    batch_reference = serializers.CharField()
    batch_status = serializers.CharField()
    severity = serializers.ChoiceField(choices=["green", "amber", "red"])
    step_summary = StepSummarySerializer()
    flags = FlagCountsSerializer()
    checklist = ChecklistSummarySerializer()
    flagged_steps = FlaggedStepSerializer(many=True)

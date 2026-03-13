from __future__ import annotations

from rest_framework import serializers


class CorrectionEntrySerializer(serializers.Serializer):
    field_name = serializers.CharField(required=True, min_length=1, max_length=200)
    new_value = serializers.JSONField(required=True)


class CorrectionRequestSerializer(serializers.Serializer):
    corrections = serializers.ListField(
        child=CorrectionEntrySerializer(),
        allow_empty=False,
    )
    reason_for_change = serializers.CharField(required=True, min_length=1, max_length=2000)


class CorrectionAppliedEntrySerializer(serializers.Serializer):
    field_name = serializers.CharField()
    old_value = serializers.JSONField()
    new_value = serializers.JSONField()


class CorrectionResponseSerializer(serializers.Serializer):
    correction_id = serializers.IntegerField()
    step_id = serializers.IntegerField()
    corrected_at = serializers.DateTimeField()
    corrected_by = serializers.IntegerField()
    corrections_applied = CorrectionAppliedEntrySerializer(many=True)
    reason_for_change = serializers.CharField()

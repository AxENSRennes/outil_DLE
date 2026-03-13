from __future__ import annotations

from typing import ClassVar

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(
    {
        "oneOf": [
            {"type": "string"},
            {"type": "number"},
            {"type": "integer"},
            {"type": "boolean"},
            {"type": "null"},
        ]
    }
)
class CorrectionScalarField(serializers.Field):
    default_error_messages: ClassVar[dict[str, str]] = {
        "invalid": "Must be a string, number, boolean, or null.",
    }

    def to_internal_value(self, data: object) -> object:
        if data is None or isinstance(data, str | int | float | bool):
            return data
        raise serializers.ValidationError(self.error_messages["invalid"])

    def to_representation(self, value: object) -> object:
        return value


class CorrectionEntrySerializer(serializers.Serializer):
    field_name = serializers.CharField(required=True, min_length=1, max_length=200)
    new_value = CorrectionScalarField(required=True, allow_null=True)


class CorrectionRequestSerializer(serializers.Serializer):
    corrections = serializers.ListField(
        child=CorrectionEntrySerializer(),
        allow_empty=False,
    )
    reason_for_change = serializers.CharField(required=True, min_length=1, max_length=2000)


class CorrectionAppliedEntrySerializer(serializers.Serializer):
    field_name = serializers.CharField()
    old_value = CorrectionScalarField(allow_null=True)
    new_value = CorrectionScalarField(allow_null=True)


class CorrectionResponseSerializer(serializers.Serializer):
    correction_id = serializers.IntegerField()
    step_id = serializers.IntegerField()
    corrected_at = serializers.DateTimeField()
    corrected_by = serializers.IntegerField()
    corrections_applied = CorrectionAppliedEntrySerializer(many=True)
    reason_for_change = serializers.CharField()

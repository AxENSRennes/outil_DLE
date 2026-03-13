from __future__ import annotations

from rest_framework import serializers

from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
)


class BatchStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchStep
        fields = (
            "id",
            "step_key",
            "occurrence_key",
            "occurrence_index",
            "title",
            "sequence_order",
            "source_document_code",
            "is_applicable",
            "applicability_basis_json",
            "status",
            "review_state",
            "signature_state",
            "blocks_execution_progress",
            "blocks_step_completion",
            "blocks_signature",
            "blocks_pre_qa_handoff",
            "data_json",
            "meta_json",
            "started_at",
            "completed_at",
            "signed_at",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class BatchDocumentRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchDocumentRequirement
        fields = (
            "id",
            "document_code",
            "title",
            "source_step_key",
            "is_required",
            "is_applicable",
            "repeat_mode",
            "expected_count",
            "actual_count",
            "status",
            "applicability_basis_json",
            "meta_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class BatchSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = (
            "id",
            "batch_number",
            "status",
            "review_state",
            "signature_state",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class StepGroupSerializer(serializers.Serializer):
    step_key = serializers.CharField()
    title = serializers.CharField()
    repeat_mode = serializers.CharField()
    is_applicable = serializers.BooleanField()
    occurrences = BatchStepSerializer(many=True)


class CompositionResponseSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    batch_number = serializers.CharField()
    steps_created = serializers.IntegerField()
    document_requirements_created = serializers.IntegerField()

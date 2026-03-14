from __future__ import annotations

from rest_framework import serializers

from apps.batches.models import (
    Batch,
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


class DocumentRequirementReadModelSerializer(serializers.Serializer):
    document_code = serializers.CharField()
    title = serializers.CharField()
    source_step_key = serializers.CharField()
    is_required = serializers.BooleanField()
    is_applicable = serializers.BooleanField()
    repeat_mode = serializers.CharField()
    expected_count = serializers.IntegerField()
    actual_count = serializers.IntegerField()
    is_complete = serializers.BooleanField()
    is_blocking = serializers.BooleanField()
    applicability_basis_json = serializers.JSONField()


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
    batch = BatchSummarySerializer()
    steps_created = serializers.IntegerField()
    document_requirements_created = serializers.IntegerField()
    step_groups = StepGroupSerializer(many=True)
    document_requirements = DocumentRequirementReadModelSerializer(many=True)

from __future__ import annotations

from rest_framework import serializers


class SiteBriefSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()


class StepSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    step_key = serializers.CharField()
    sequence_order = serializers.IntegerField()
    title = serializers.CharField()
    kind = serializers.CharField()
    status = serializers.CharField()
    is_applicable = serializers.BooleanField()
    signature_state = serializers.CharField()
    requires_signature = serializers.BooleanField()


class ProgressSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    applicable = serializers.IntegerField()


class BatchExecutionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    batch_number = serializers.CharField()
    status = serializers.CharField()
    product_name = serializers.CharField()
    product_code = serializers.CharField()
    site = SiteBriefSerializer()
    template_name = serializers.CharField()
    template_code = serializers.CharField()
    steps = StepSummarySerializer(many=True)
    current_step_id = serializers.IntegerField(allow_null=True)
    progress = ProgressSerializer()


class BlockingPolicySerializer(serializers.Serializer):
    blocks_execution_progress = serializers.BooleanField()
    blocks_step_completion = serializers.BooleanField()
    blocks_signature = serializers.BooleanField()
    blocks_pre_qa_handoff = serializers.BooleanField()


class FieldOptionSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class FieldDefinitionSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.CharField()
    label = serializers.CharField()
    required = serializers.BooleanField(required=False, default=False)
    options = FieldOptionSerializer(many=True, required=False)
    unit = serializers.CharField(required=False, allow_blank=True)
    validation = serializers.DictField(required=False)


class SignaturePolicySerializer(serializers.Serializer):
    required = serializers.BooleanField(default=False)
    meaning = serializers.CharField(default="", allow_blank=True)


class BatchStepDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    step_key = serializers.CharField()
    sequence_order = serializers.IntegerField()
    title = serializers.CharField()
    kind = serializers.CharField()
    status = serializers.CharField()
    is_applicable = serializers.BooleanField()
    instructions = serializers.CharField(allow_blank=True)
    fields = FieldDefinitionSerializer(many=True)
    signature_policy = SignaturePolicySerializer()
    blocking_policy = BlockingPolicySerializer()
    data = serializers.DictField()
    meta = serializers.DictField()

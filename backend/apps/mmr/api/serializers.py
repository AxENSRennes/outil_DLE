from __future__ import annotations

from rest_framework import serializers

from apps.mmr.models import MMR, MMRVersion

# ---------------------------------------------------------------------------
# MMR serializers (existing)
# ---------------------------------------------------------------------------


class MMRCreateSerializer(serializers.Serializer):
    site_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, default="", allow_blank=True)


class MMRDetailSerializer(serializers.ModelSerializer):
    version_count = serializers.SerializerMethodField()

    class Meta:
        model = MMR
        fields = (
            "id",
            "site",
            "product",
            "name",
            "code",
            "description",
            "is_active",
            "version_count",
            "created_at",
            "updated_at",
        )

    def get_version_count(self, obj: MMR) -> int:
        return obj.versions.count()


class MMRListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MMR
        fields = (
            "id",
            "site",
            "product",
            "name",
            "code",
            "is_active",
            "created_at",
            "updated_at",
        )


class MMRVersionCreateSerializer(serializers.Serializer):
    change_summary = serializers.CharField(required=False, default="", allow_blank=True)


class MMRVersionDetailSerializer(serializers.ModelSerializer):
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = MMRVersion
        fields = (
            "id",
            "mmr",
            "version_number",
            "status",
            "schema_json",
            "change_summary",
            "created_by",
            "activated_by",
            "activated_at",
            "step_count",
            "created_at",
            "updated_at",
        )

    def get_step_count(self, obj: MMRVersion) -> int:
        schema = obj.schema_json or {}
        return len(schema.get("stepOrder", []))


class MMRVersionListSerializer(serializers.ModelSerializer):
    has_steps = serializers.SerializerMethodField()

    class Meta:
        model = MMRVersion
        fields = (
            "id",
            "mmr",
            "version_number",
            "status",
            "change_summary",
            "created_by",
            "has_steps",
            "created_at",
        )

    def get_has_steps(self, obj: MMRVersion) -> bool:
        schema = obj.schema_json or {}
        return len(schema.get("stepOrder", [])) > 0


# ---------------------------------------------------------------------------
# Step nested policy serializers (typed — never use raw DictField)
# ---------------------------------------------------------------------------

STEP_KIND_CHOICES = [
    ("preparation", "Preparation"),
    ("material_confirmation", "Material Confirmation"),
    ("weighing", "Weighing"),
    ("manufacturing", "Manufacturing"),
    ("pre_qa_review", "Pre QA Review"),
    ("in_process_control", "In Process Control"),
    ("bulk_handover", "Bulk Handover"),
    ("packaging", "Packaging"),
    ("finished_product_control", "Finished Product Control"),
    ("review", "Review"),
]


class AttachmentsPolicySerializer(serializers.Serializer):
    supports_attachments = serializers.BooleanField(required=False, default=False)
    attachment_kinds = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["checklist", "worksheet", "label_scan", "photo", "other"]
        ),
        required=False,
        default=list,
    )


class ApplicabilitySerializer(serializers.Serializer):
    site_codes = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    line_codes = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    machine_codes = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False
    )
    format_families = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False
    )
    glitter_mode = serializers.ChoiceField(
        choices=["with_glitter", "without_glitter", "any"], required=False
    )
    when_not_applicable = serializers.ChoiceField(choices=["hidden", "mark_na"], required=False)


class RepeatPolicySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        choices=["single", "per_shift", "per_team", "per_box", "per_event"],
        required=False,
    )
    min_records = serializers.IntegerField(min_value=0, required=False)
    max_records = serializers.IntegerField(min_value=1, required=False)


class BlockingPolicySerializer(serializers.Serializer):
    blocks_execution_progress = serializers.BooleanField(required=False, default=False)
    blocks_step_completion = serializers.BooleanField(required=False, default=False)
    blocks_signature = serializers.BooleanField(required=False, default=False)
    blocks_pre_qa_handoff = serializers.BooleanField(required=False, default=False)


class SignaturePolicySerializer(serializers.Serializer):
    required = serializers.BooleanField()
    meaning = serializers.CharField()


# ---------------------------------------------------------------------------
# Step input serializers
# ---------------------------------------------------------------------------


class StepCreateSerializer(serializers.Serializer):
    key = serializers.RegexField(
        r"^[a-z][a-z0-9_]*$",
        max_length=100,
        help_text="Unique step identifier (snake_case slug).",
    )
    title = serializers.CharField(max_length=255)
    kind = serializers.ChoiceField(choices=STEP_KIND_CHOICES)
    instructions = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=10000
    )
    attachments_policy = AttachmentsPolicySerializer(required=False, allow_null=True)
    required = serializers.BooleanField(required=False, default=True)
    applicability = ApplicabilitySerializer(required=False, allow_null=True)
    repeat_policy = RepeatPolicySerializer(required=False, allow_null=True)
    blocking_policy = BlockingPolicySerializer(required=False, allow_null=True)


class StepUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    kind = serializers.ChoiceField(choices=STEP_KIND_CHOICES, required=False)
    instructions = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=10000
    )
    attachments_policy = AttachmentsPolicySerializer(required=False, allow_null=True)
    required = serializers.BooleanField(required=False)
    applicability = ApplicabilitySerializer(required=False, allow_null=True)
    repeat_policy = RepeatPolicySerializer(required=False, allow_null=True)
    blocking_policy = BlockingPolicySerializer(required=False, allow_null=True)


class StepReorderSerializer(serializers.Serializer):
    step_order = serializers.ListField(
        child=serializers.CharField(max_length=100),
    )


# ---------------------------------------------------------------------------
# Step output serializers
# ---------------------------------------------------------------------------


class StepDetailSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    kind = serializers.ChoiceField(choices=STEP_KIND_CHOICES)
    instructions = serializers.CharField(default=None, allow_null=True)
    required = serializers.BooleanField(default=True)
    attachments_policy = AttachmentsPolicySerializer(default=None, allow_null=True)
    applicability = ApplicabilitySerializer(default=None, allow_null=True)
    repeat_policy = RepeatPolicySerializer(default=None, allow_null=True)
    blocking_policy = BlockingPolicySerializer(default=None, allow_null=True)
    signature_policy = SignaturePolicySerializer()
    fields = serializers.ListField(default=list)


class StepListSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    kind = serializers.ChoiceField(choices=STEP_KIND_CHOICES)
    required = serializers.BooleanField(default=True)

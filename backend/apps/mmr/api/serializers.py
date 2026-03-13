from __future__ import annotations

from typing import Any, cast

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.mmr.domain.step_management import VALID_STEP_KINDS
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

STEP_KIND_CHOICES = [(k, k.replace("_", " ").title()) for k in sorted(VALID_STEP_KINDS)]
SIGNATURE_MEANINGS = [
    "performed_by",
    "reviewed_by",
    "approved_by",
    "released_by",
]
SIGNATURE_MEANING_CHOICES = [
    ("performed_by", "Performed By"),
    ("reviewed_by", "Reviewed By"),
    ("approved_by", "Approved By"),
    ("released_by", "Released By"),
]
SIGNATURE_POLICY_SCHEMA = {
    "type": "object",
    "properties": {
        "required": {"type": "boolean"},
        "meaning": {"type": "string", "enum": SIGNATURE_MEANINGS},
    },
    "required": ["required", "meaning"],
}
STEP_FIELD_TYPE_CHOICES = [
    ("text", "Text"),
    ("number", "Number"),
    ("decimal", "Decimal"),
    ("number_series", "Number Series"),
    ("boolean", "Boolean"),
    ("datetime", "Datetime"),
    ("select", "Select"),
    ("material_lot_ref", "Material Lot Ref"),
    ("equipment_ref", "Equipment Ref"),
    ("checklist_ref", "Checklist Ref"),
    ("label_ref", "Label Ref"),
    ("calculated", "Calculated"),
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        min_r = attrs.get("min_records")
        max_r = attrs.get("max_records")
        if min_r is not None and max_r is not None and min_r > max_r:
            raise serializers.ValidationError(
                "min_records must be less than or equal to max_records."
            )
        return attrs


class BlockingPolicySerializer(serializers.Serializer):
    blocks_execution_progress = serializers.BooleanField(required=False, default=False)
    blocks_step_completion = serializers.BooleanField(required=False, default=False)
    blocks_signature = serializers.BooleanField(required=False, default=False)
    blocks_pre_qa_handoff = serializers.BooleanField(required=False, default=False)


@extend_schema_field(SIGNATURE_POLICY_SCHEMA)
class SignaturePolicyField(serializers.Field):
    def to_representation(self, value: Any) -> Any:
        return value


class StepFieldOptionSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=100)
    label = serializers.CharField(max_length=255)


class StepFieldValidationSerializer(serializers.Serializer):
    min = serializers.FloatField(required=False)
    max = serializers.FloatField(required=False)
    min_items = serializers.IntegerField(min_value=1, required=False)
    max_items = serializers.IntegerField(min_value=1, required=False)
    pattern = serializers.CharField(required=False)


class StepFieldSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=100)
    type = serializers.ChoiceField(choices=STEP_FIELD_TYPE_CHOICES)
    label = serializers.CharField(max_length=255)
    unit = serializers.CharField(max_length=50, required=False)
    required = serializers.BooleanField(required=False)
    options = StepFieldOptionSerializer(many=True, required=False)
    validation = StepFieldValidationSerializer(required=False)
    expression_ref = serializers.CharField(max_length=100, required=False)
    visible_if = serializers.CharField(max_length=255, required=False)
    required_if = serializers.CharField(max_length=255, required=False)
    optional_in_v1 = serializers.BooleanField(required=False)


class _StepPolicyValidationMixin:
    def _validate_attachments_policy(self, policy: dict[str, Any]) -> None:
        attachment_kinds = policy.get("attachment_kinds") or []
        supports_attachments = policy.get("supports_attachments", False)
        if attachment_kinds and not supports_attachments:
            raise serializers.ValidationError(
                {
                    "attachments_policy": {
                        "attachment_kinds": (
                            "attachment_kinds requires supports_attachments to be true."
                        )
                    }
                }
            )

    def _validate_repeat_policy(self, policy: dict[str, Any]) -> None:
        if "mode" not in policy:
            raise serializers.ValidationError(
                {
                    "repeat_policy": {
                        "mode": "This field is required when repeat_policy is provided."
                    }
                }
            )

    def _merged_nested_policy(
        self,
        attrs: dict[str, Any],
        *,
        field_name: str,
    ) -> dict[str, Any] | None:
        incoming = attrs.get(field_name)
        if incoming is None:
            return None

        if not isinstance(incoming, dict):
            return None

        current_step = cast(
            dict[str, Any],
            getattr(self, "context", {}).get("current_step") or {},
        )
        current_value = current_step.get(field_name)
        if isinstance(current_value, dict):
            return {**current_value, **incoming}
        return incoming


# ---------------------------------------------------------------------------
# Step input serializers
# ---------------------------------------------------------------------------


class StepCreateSerializer(_StepPolicyValidationMixin, serializers.Serializer):
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("attachments_policy") is not None:
            self._validate_attachments_policy(attrs["attachments_policy"])
        if attrs.get("repeat_policy") is not None:
            self._validate_repeat_policy(attrs["repeat_policy"])
        return attrs


class StepUpdateSerializer(_StepPolicyValidationMixin, serializers.Serializer):
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if "attachments_policy" in attrs:
            merged_policy = self._merged_nested_policy(attrs, field_name="attachments_policy")
            if merged_policy is not None:
                self._validate_attachments_policy(merged_policy)
        if "repeat_policy" in attrs:
            merged_policy = self._merged_nested_policy(attrs, field_name="repeat_policy")
            if merged_policy is not None:
                self._validate_repeat_policy(merged_policy)
        return attrs


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
    signature_policy = SignaturePolicyField()
    fields = StepFieldSerializer(many=True, default=list)


class StepListSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    kind = serializers.ChoiceField(choices=STEP_KIND_CHOICES)
    required = serializers.BooleanField(default=True)

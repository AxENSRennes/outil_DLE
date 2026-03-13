"""Request and response serializers for pre-QA review actions."""

from __future__ import annotations

from rest_framework import serializers


class ConfirmPreQaReviewRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, default="", allow_blank=True)


class PreQaReviewConfirmationSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    batch_reference = serializers.CharField()
    batch_status = serializers.CharField()
    confirmed_at = serializers.DateTimeField()
    reviewer_note = serializers.CharField()


class MarkStepReviewedRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, default="", allow_blank=True)


class MarkStepReviewedResponseSerializer(serializers.Serializer):
    step_id = serializers.IntegerField()
    step_reference = serializers.CharField()
    review_status = serializers.CharField()
    flags_cleared = serializers.ListField(child=serializers.CharField())
    batch_status = serializers.CharField()

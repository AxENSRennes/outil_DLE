from __future__ import annotations

from rest_framework import serializers


class DossierElementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    element_identifier = serializers.CharField()
    element_type = serializers.CharField()
    display_order = serializers.IntegerField()
    applicability = serializers.CharField()
    title = serializers.CharField()
    metadata = serializers.DictField()


class DossierStructureSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    dossier_profile_id = serializers.IntegerField()
    context_snapshot = serializers.DictField()
    is_active = serializers.BooleanField()
    resolved_at = serializers.DateTimeField()
    elements = DossierElementSerializer(many=True)

from __future__ import annotations

from rest_framework import serializers

from apps.mmr.models import MMR, MMRVersion


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
            "created_at",
            "updated_at",
        )


class MMRVersionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MMRVersion
        fields = (
            "id",
            "mmr",
            "version_number",
            "status",
            "change_summary",
            "created_by",
            "created_at",
        )

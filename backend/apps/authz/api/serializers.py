from __future__ import annotations

from rest_framework import serializers


class AuthenticatedUserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class SiteSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()


class SiteAccessAssignmentSerializer(serializers.Serializer):
    site = SiteSummarySerializer()
    roles = serializers.ListField(child=serializers.CharField())


class AuthContextSerializer(serializers.Serializer):
    user = AuthenticatedUserSummarySerializer()
    site_assignments = SiteAccessAssignmentSerializer(many=True)


class SiteRoleAccessProbeSerializer(serializers.Serializer):
    site = SiteSummarySerializer()
    required_role = serializers.CharField()
    status = serializers.CharField()

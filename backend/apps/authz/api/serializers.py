from __future__ import annotations

from rest_framework import serializers

from apps.authz.models import SiteRole


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


class WorkstationIdentifyRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    pin = serializers.CharField(min_length=4, max_length=32, trim_whitespace=False)


class WorkstationIdentifyResponseSerializer(AuthContextSerializer):
    status = serializers.CharField()
    event = serializers.CharField()
    previous_user = AuthenticatedUserSummarySerializer(allow_null=True)


class WorkstationLockResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class SignatureReauthRequestSerializer(serializers.Serializer):
    site_code = serializers.SlugField(max_length=64)
    required_roles = serializers.ListField(
        child=serializers.ChoiceField(choices=SiteRole.choices),
        allow_empty=False,
    )
    pin = serializers.CharField(min_length=4, max_length=32, trim_whitespace=False)


class SignatureReauthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    site = SiteSummarySerializer()
    signer = AuthenticatedUserSummarySerializer()
    authorized_roles = serializers.ListField(child=serializers.CharField())

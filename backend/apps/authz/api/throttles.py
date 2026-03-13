from __future__ import annotations

import logging
from typing import Any, cast

from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import NotFound
from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle
from shared.http import get_client_ip
from shared.permissions.site_roles import get_active_site_by_code

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event

logger = logging.getLogger(__name__)


class AuditEventThrottle(SimpleRateThrottle):
    failure_event_type: str

    def allow_request(self, request: Any, view: Any) -> bool:
        self.request = request
        self.view = view
        return cast(bool, super().allow_request(request, view))

    def get_rate(self) -> str:
        if not self.scope:
            raise ImproperlyConfigured("AuditEventThrottle requires a scope.")
        rates = api_settings.DEFAULT_THROTTLE_RATES
        if self.scope not in rates:
            raise ImproperlyConfigured(
                f"No default throttle rate configured for scope '{self.scope}'."
            )
        return str(rates[self.scope])

    def get_ident_key(self, request: Any) -> str:
        if getattr(request.user, "is_authenticated", False):
            return f"user:{request.user.pk}"
        return f"ip:{self.get_ident(request)}"

    def get_cache_key(self, request: Any, view: Any) -> str | None:
        return cast(
            str,
            self.cache_format
            % {
                "scope": self.scope,
                "ident": self.get_ident_key(request),
            },
        )

    def throttle_failure(self) -> bool:
        try:
            self._record_failure()
        except Exception:
            # Audit write failure must not disable throttle rejection.
            logger.exception("Failed to record throttle audit event")
        return cast(bool, super().throttle_failure())

    def _record_failure(self) -> None:
        raise NotImplementedError


class WorkstationIdentifyThrottle(AuditEventThrottle):
    scope = "workstation_identify"
    failure_event_type = AuditEventType.IDENTIFY_FAILED

    def get_ident_key(self, request: Any) -> str:
        base_ident = super().get_ident_key(request)
        username = None
        if isinstance(getattr(request, "data", None), dict):
            username = request.data.get("username")
        return f"{base_ident}:username:{username or 'unknown'}"

    def _record_failure(self) -> None:
        username = None
        if isinstance(getattr(self.request, "data", None), dict):
            username = self.request.data.get("username")
        record_audit_event(
            self.failure_event_type,
            metadata={
                "reason": "rate_limited",
                "attempted_username": username,
                "ip_address": get_client_ip(self.request),
            },
        )


class SignatureReauthThrottle(AuditEventThrottle):
    scope = "signature_reauth"
    failure_event_type = AuditEventType.SIGNATURE_REAUTH_FAILED

    def get_ident_key(self, request: Any) -> str:
        base_ident = super().get_ident_key(request)
        site_code = None
        if isinstance(getattr(request, "data", None), dict):
            site_code = request.data.get("site_code")
        return f"{base_ident}:site:{site_code or 'unknown'}"

    def _record_failure(self) -> None:
        site = None
        required_roles: list[str] = []
        if isinstance(getattr(self.request, "data", None), dict):
            site_code = self.request.data.get("site_code")
            if isinstance(site_code, str):
                try:
                    site = get_active_site_by_code(site_code)
                except NotFound:
                    site = None
            roles = self.request.data.get("required_roles", [])
            if isinstance(roles, list):
                required_roles = [str(role) for role in roles]
        record_audit_event(
            self.failure_event_type,
            actor=(
                self.request.user if getattr(self.request.user, "is_authenticated", False) else None
            ),
            site=site,
            metadata={
                "reason": "rate_limited",
                "required_roles": required_roles,
                "ip_address": get_client_ip(self.request),
            },
        )

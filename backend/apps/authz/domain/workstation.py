from __future__ import annotations

from typing import Any

from django.contrib.auth import login, logout
from rest_framework.exceptions import PermissionDenied
from shared.permissions.site_roles import get_active_site_by_code

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.authz.domain.policies import get_user_site_roles
from apps.authz.models import User
from apps.authz.selectors.access_context import list_site_access_contexts
from apps.sites.models import Site


def summarize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.get_username(),
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


def summarize_site(site: Site) -> dict[str, Any]:
    return {
        "id": site.id,
        "code": site.code,
        "name": site.name,
    }


def build_auth_context_payload(user: User) -> dict[str, Any]:
    return {
        "user": summarize_user(user),
        "site_assignments": [
            {
                "site": {
                    "id": access.site_id,
                    "code": access.site_code,
                    "name": access.site_name,
                },
                "roles": list(access.roles),
            }
            for access in list_site_access_contexts(user)
        ],
    }


def _get_user_by_username(username: str) -> User | None:
    return User.objects.filter(username=username, is_active=True).first()


def identify_workstation_user(request: Any, *, username: str, pin: str) -> dict[str, Any]:
    user = _get_user_by_username(username)
    if user is None or not user.check_workstation_pin(pin):
        record_audit_event(
            AuditEventType.IDENTIFY_FAILED,
            metadata={
                "attempted_username": username,
                "reason": "invalid_credentials",
            },
        )
        raise PermissionDenied(
            detail="Invalid workstation credentials.",
            code="invalid_workstation_credentials",
        )

    previous_user = request.user if getattr(request.user, "is_authenticated", False) else None
    switched_user = isinstance(previous_user, User) and previous_user.pk != user.pk

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    event_metadata: dict[str, Any] = {"outcome": "identified"}
    if switched_user and previous_user is not None:
        event_type = AuditEventType.SWITCH_USER
        event_metadata["previous_user_id"] = previous_user.id
        event_metadata["previous_username"] = previous_user.username
    else:
        event_type = AuditEventType.IDENTIFY

    record_audit_event(
        event_type,
        actor=user,
        metadata=event_metadata,
    )

    payload = build_auth_context_payload(user)
    payload.update(
        {
            "status": "identified",
            "event": "switch_user" if switched_user else "identify",
            "previous_user": summarize_user(previous_user)
            if isinstance(previous_user, User) and switched_user
            else None,
        }
    )
    return payload


def lock_workstation(request: Any) -> dict[str, str]:
    user = request.user if isinstance(request.user, User) else None
    record_audit_event(
        AuditEventType.LOCK_WORKSTATION,
        actor=user,
        metadata={"outcome": "locked"},
    )
    logout(request)
    return {"status": "locked"}


def reauthenticate_signature_authority(
    *, user: User, site_code: str, required_roles: tuple[str, ...], pin: str
) -> dict[str, Any]:
    site = get_active_site_by_code(site_code)
    if not user.check_workstation_pin(pin):
        record_audit_event(
            AuditEventType.SIGNATURE_REAUTH_FAILED,
            actor=user,
            site=site,
            metadata={
                "required_roles": list(required_roles),
                "reason": "invalid_credentials",
            },
        )
        raise PermissionDenied(
            detail="Invalid signature re-authentication credentials.",
            code="invalid_signature_reauth_credentials",
        )

    authorized_roles = tuple(
        role for role in get_user_site_roles(user, site) if role in set(required_roles)
    )
    if not authorized_roles:
        record_audit_event(
            AuditEventType.SIGNATURE_REAUTH_FAILED,
            actor=user,
            site=site,
            metadata={
                "required_roles": list(required_roles),
                "reason": "missing_required_role",
            },
        )
        raise PermissionDenied(
            detail="The active user is not authorized for this signature context.",
            code="signature_role_not_authorized",
        )

    record_audit_event(
        AuditEventType.SIGNATURE_REAUTH_SUCCEEDED,
        actor=user,
        site=site,
        metadata={
            "required_roles": list(required_roles),
            "outcome": "authorized",
        },
    )
    return {
        "status": "authorized",
        "site": summarize_site(site),
        "signer": summarize_user(user),
        "authorized_roles": list(authorized_roles),
    }

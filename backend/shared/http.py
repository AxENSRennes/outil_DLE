from __future__ import annotations

from typing import Any


def get_client_ip(request: Any) -> str | None:
    """Return the client IP from the request for audit metadata.

    Advisory/best-effort: X-Forwarded-For is trusted as-is, which is acceptable
    because this value is only used in audit metadata, not for access control.
    If deployed behind an untrusted proxy layer, consider gating on a
    TRUSTED_PROXIES setting or using django-ipware.
    """
    forwarded_for: str | None = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    remote_addr: str | None = request.META.get("REMOTE_ADDR")
    return remote_addr

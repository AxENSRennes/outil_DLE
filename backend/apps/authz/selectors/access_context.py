from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from apps.authz.domain.policies import get_active_site_role_assignments


@dataclass(frozen=True)
class SiteAccessContext:
    site_id: int
    site_code: str
    site_name: str
    roles: tuple[str, ...]


def list_site_access_contexts(user: Any) -> list[SiteAccessContext]:
    assignments = get_active_site_role_assignments(user).order_by("site__code", "role")
    grouped_roles: dict[tuple[int, str, str], list[str]] = defaultdict(list)

    for assignment in assignments:
        key = (assignment.site_id, assignment.site.code, assignment.site.name)
        grouped_roles[key].append(assignment.role)

    return [
        SiteAccessContext(
            site_id=site_id,
            site_code=site_code,
            site_name=site_name,
            roles=tuple(roles),
        )
        for (site_id, site_code, site_name), roles in grouped_roles.items()
    ]

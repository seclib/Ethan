"""Router API — public GitHub organization discovery."""

from __future__ import annotations

from typing import Any

from core.applications.github_organization_discovery import (
    discover_github_org_repositories,
    discover_github_user_repositories,
    GitHubOrgDiscoveryError,
)
from fastapi import APIRouter, HTTPException, Depends
from interfaces.api.auth import require_permission
from core.auth import Permission

router = APIRouter(prefix="/v1", tags=["github-discovery"])


@router.get(
    "/github/organizations/{organization}/repositories",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def discover_github_organization(organization: str) -> list[dict[str, Any]]:
    try:
        repositories = discover_github_org_repositories(organization, source_type="organization")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GitHubOrgDiscoveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [repository.to_dict() for repository in repositories]



@router.get(
    "/github/users/{username}/repositories",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def discover_github_user(username: str) -> list[dict[str, Any]]:
    try:
        repositories = discover_github_user_repositories(username)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GitHubOrgDiscoveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [repository.to_dict() for repository in repositories]

__all__ = ["router"]

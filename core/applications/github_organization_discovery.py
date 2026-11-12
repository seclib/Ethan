"""Reusable public GitHub organization discovery adapter (Campaign 02-A).

External repositories are treated as untrusted metadata and source observations.
Nothing in this module executes repository code.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable
from urllib.parse import urlencode
import base64
from pathlib import PurePosixPath
from dataclasses import asdict, dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_API_BASE = "https://api.github.com"


@dataclass(frozen=True, slots=True)
class GitHubRepositoryMetadata:
    organization: str
    name: str
    full_name: str
    description: str | None
    default_branch: str
    html_url: str
    clone_url: str
    archived: bool
    visibility: str
    updated_at: str | None
    topics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GitHubOrgDiscoveryError(Exception):
    """Raised when repository metadata cannot be safely retrieved."""


def _extract_next_page(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part.strip())
        if match:
            return match.group(1)
    return None


def discover_github_repositories(
    account: str,
    *,
    source_type: str = "user",
    base_url: str = _API_BASE,
    per_page: int = 30,
    max_pages: int = 10,
    access_token: str | None = None,
    timeout: float = 10.0,
) -> list[GitHubRepositoryMetadata]:
    """Discover public repositories for a GitHub user or organization.

    ``source_type`` must be ``user`` or ``organization``.
    """
    if not account.strip():
        raise ValueError("account is required")
    source_type = source_type.strip().lower()
    if source_type not in {"user", "organization"}:
        raise ValueError("source_type must be user or organization")

    per_page = max(1, min(per_page, 100))
    token = access_token or os.environ.get("GITHUB_TOKEN")
    collected: list[GitHubRepositoryMetadata] = []
    seen: set[str] = set()

    resource = "users" if source_type == "user" else "orgs"
    owner_field = organization if False else None
    del owner_field
    next_url = (
        f"{base_url.rstrip('/')}/{resource}/{account}/repos?"
        f"{urlencode({'per_page': per_page, 'type': 'public'})}"
    )

    for _ in range(max_pages):
        request = Request(next_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ETHAN-OS"})
        if token:
            request.add_header("Authorization", f"Bearer {token}")

        try:
            response = urlopen(request, timeout=timeout)
            data = response.read()
            link_header = response.headers.get("Link")
            status = getattr(response, "status", 200)
        except HTTPError as exc:
            raise GitHubOrgDiscoveryError(
                f"GitHub organization discovery failed with HTTP {exc.code}: {exc.reason}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise GitHubOrgDiscoveryError(f"GitHub organization discovery is unavailable: {exc}") from exc

        if status < 200 or status >= 300:
            raise GitHubOrgDiscoveryError(f"GitHub organization discovery failed with HTTP {status}")

        try:
            payload = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GitHubOrgDiscoveryError("GitHub returned malformed repository metadata") from exc

        if not isinstance(payload, list):
            raise GitHubOrgDiscoveryError("GitHub returned an unexpected repository payload")

        for item in payload:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            full_name = str(item.get("full_name") or f"{account}/{item['name']}")
            if full_name in seen:
                continue
            seen.add(full_name)
            collected.append(
                GitHubRepositoryMetadata(
                    organization=account,
                    name=str(item["name"]),
                    full_name=full_name,
                    description=item.get("description"),
                    default_branch=str(item.get("default_branch") or "main"),
                    html_url=str(item.get("html_url") or ""),
                    clone_url=str(item.get("clone_url") or ""),
                    archived=bool(item.get("archived")),
                    visibility=str(item.get("visibility") or "public"),
                    updated_at=item.get("updated_at"),
                    topics=tuple(str(topic) for topic in item.get("topics") or ()),
                )
            )

        if len(payload) < per_page:
            next_url = _extract_next_page(link_header)
            if not next_url:
                break
        next_page = _extract_next_page(link_header)
        if not next_page:
            break
        next_url = next_page

    return collected

def discover_github_org_repositories(*args, **kwargs):
    kwargs.setdefault("source_type", "organization")
    return discover_github_repositories(*args, **kwargs)


def discover_github_user_repositories(account, *args, **kwargs):
    kwargs["source_type"] = "user"
    return discover_github_repositories(account, *args, **kwargs)

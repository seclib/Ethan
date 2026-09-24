"""Tests du socle partagé Folders/Domains (core/attachments) — Phase 4.

Vérifie que la mutualisation des helpers n'a rien changé :
  - membership_key / normalize_record / utc_now / UNSET ;
  - ResourceProvider (adapter getter/lister) ;
  - les alias de compat des deux managers pointent vers le socle.
"""

from __future__ import annotations

import asyncio

from core.attachments import (
    UNSET,
    ResourceProvider,
    membership_key,
    normalize_record,
    utc_now,
)


def test_membership_key_format():
    assert membership_key("folder-1", "skill", "skill-1") == "folder-1:skill:skill-1"
    assert membership_key("dom-1", "knowledge", "k1") == "dom-1:knowledge:k1"


def test_normalize_record_variants():
    assert normalize_record(None) is None
    record = {"id": "x"}
    assert normalize_record(record) is record  # dict passé tel quel

    class Obj:
        def to_dict(self):
            return {"id": "y"}

    assert normalize_record(Obj()) == {"id": "y"}
    assert normalize_record("scalar") is None


def test_utc_now_iso_z():
    stamp = utc_now()
    assert stamp.endswith("Z")
    assert "T" in stamp
    assert "+" not in stamp.replace("+00:00", "")  # déjà converti en Z


def test_unset_is_singleton():
    from core.domains.manager import _UNSET as domains_unset
    from core.folders.manager import _UNSET as folders_unset

    assert folders_unset is UNSET
    assert domains_unset is UNSET
    assert UNSET is not None


def test_resource_provider_reads_through():
    async def getter(resource_id: str):
        return {"id": resource_id}

    async def lister():
        return [{"id": "a"}, {"id": "b"}]

    provider = ResourceProvider(getter, lister)
    assert asyncio.run(provider.get("a")) == {"id": "a"}
    assert asyncio.run(provider.list_all()) == [{"id": "a"}, {"id": "b"}]


def test_manager_aliases_point_to_socle():
    """Les noms publics historiques restent importables (compat)."""
    from core.attachments import normalize_record as socle_normalize
    from core.domains import DomainResourceProvider
    from core.folders import FolderResourceProvider
    from core.folders.manager import _membership_id, _to_dict, _utc_now

    assert issubclass(FolderResourceProvider, ResourceProvider) or (
        FolderResourceProvider is ResourceProvider
    )
    assert DomainResourceProvider is ResourceProvider
    assert _membership_id is membership_key
    assert _to_dict is socle_normalize
    assert _utc_now.__name__ == utc_now.__name__
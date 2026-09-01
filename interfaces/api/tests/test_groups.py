"""Tests réels des routes /groups (interfaces/api/routers/domains.py).

Exécute le vrai GroupManager du Core (core/auth/groups.py) sur un
CoreRecordStore en mémoire (aucun mock du domaine) et appelle directement les
fonctions de route — les Depends(require_permission(ADMIN)) sont ainsi
contournés, ce qui est hors périmètre ici (gate déjà couvert par auth.py).

Les gates admin des routes /groups sont déclaratives
(Depends(require_permission(Permission.ADMIN))) et testées par la couche auth ;
ce fichier valide la logique de domaine de bout en bout.
"""

import asyncio

import pytest
from fastapi import HTTPException

from routers import domains
from core.auth.groups import GroupManager


@pytest.fixture(autouse=True)
def real_groups():
    """Vrai GroupManager (CoreRecordStore mémoire) injecté dans le router."""
    domains.set_domain_managers(groups=GroupManager())
    yield
    domains.set_domain_managers(groups=None)


def test_group_crud_full_cycle():
    """Création → liste → lecture → édition → suppression."""
    group = asyncio.run(domains.create_group({"name": " platform ", "description": "Équipe plateforme"}))
    assert group["name"] == "platform"
    assert group["members"] == []
    assert group["permissions"] == {}

    listed = asyncio.run(domains.list_groups())
    assert [g["id"] for g in listed] == [group["id"]]

    fetched = asyncio.run(domains.get_group(group["id"]))
    assert fetched["name"] == "platform"

    updated = asyncio.run(domains.update_group(
        group["id"], {"description": "Équipe runtime"}))
    assert updated["description"] == "Équipe runtime"
    assert updated["name"] == "platform"  # inchangé (non fourni)

    deleted = asyncio.run(domains.delete_group(group["id"]))
    assert deleted == {"status": "deleted"}
    assert asyncio.run(domains.list_groups()) == []


def test_group_create_empty_name_accepted_by_core():
    """Constat d'audit : le Core n'applique AUCUNE validation du nom
    (le except ValueError du router n'est jamais déclenché). Un nom vide
    est accepté tel quel. La validation est donc assurée côté WebUI
    (bouton « Créer » désactivé si le nom est vide)."""
    group = asyncio.run(domains.create_group({"name": "  "}))
    assert group["name"] == ""
    # Nettoyage pour ne pas polluer d'autres assertions.
    asyncio.run(domains.delete_group(group["id"]))


def test_group_create_missing_name_key_defaults_to_empty():
    """Le router passe data.get(\"name\", \"\") — clé absente → chaîne vide."""
    group = asyncio.run(domains.create_group({}))
    assert group["name"] == ""
    asyncio.run(domains.delete_group(group["id"]))


def test_group_unknown_id_404():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(domains.get_group("nope"))
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        asyncio.run(domains.delete_group("nope"))
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        asyncio.run(domains.update_group("nope", {"name": "x"}))
    assert exc.value.status_code == 404


def test_group_members_add_remove():
    """Ajout/retrait de membres via le vrai GroupManager."""
    group = asyncio.run(domains.create_group({"name": "admins"}))
    gid = group["id"]

    after_add = asyncio.run(domains.add_group_member(gid, "bob"))
    assert after_add["members"] == ["bob"]

    # Idempotence gérée par le Core : pas de doublon.
    after_dup = asyncio.run(domains.add_group_member(gid, "bob"))
    assert after_dup["members"] == ["bob"]

    after_remove = asyncio.run(domains.remove_group_member(gid, "bob"))
    assert after_remove["members"] == []

    # Retrait d'un non-membre : le Core renvoie le groupe inchangé (pas 404).
    result = asyncio.run(domains.remove_group_member(gid, "ghost"))
    assert result["members"] == []


def test_group_members_unknown_group_404():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(domains.add_group_member("nope", "bob"))
    assert exc.value.status_code == 404

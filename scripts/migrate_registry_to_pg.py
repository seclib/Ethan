#!/usr/bin/env python3
"""DAĒNĀ P2.8.1 — Migration du registre de ressources vers la source de vérité.

Déplace la vue materialisée des `ResourceRecord` du fichier `registry-meta.json`
vers le domaine `resources` de `core_domain_records` (PostgreSQL), afin que
le ResourceRegistry s'appuie sur le même store que tous les autres services
Core.

**Cette migration n'est PAS exécutée automatiquement.** Le mode par défaut est
`--dry-run` : le script rapporte ce qu'il ferait sans rien écrire.

 Caractères de la migration
 ---------------------------
- Le contenu du registre est un **état dérivé** : il se régénère par
  `discover_skills()` et `discover_documents()`. La migration ne perd donc
  aucune donnée unique — elle réécrit une matérialisation.
- Le fichier `registry-meta.json` **n'est jamais supprimé** : il reste
  l'amorçage et l'export portable.
- L'écriture est un upsert par `stable_id` : idempotente.
- Les métadonnées, la provenance et les identifiants sont préservés à
  l'identique (y compris `discovered_at` et `last_verified`).

Usage
-----
    # Rapport seul (aucune écriture) — mode par défaut
    python scripts/migrate_registry_to_pg.py

    # Sur une base de test isolée
    python scripts/migrate_registry_to_pg.py --apply --database-url postgresql://...

Toute écriture sur les données de production exige une autorisation explicite
distincte de l'opérateur.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.resources.repository import RESOURCE_DOMAIN, ResourceRepository  # noqa: E402
from core.state.record_store import CoreRecordStore  # noqa: E402


def _build_store(database_url: str | None) -> CoreRecordStore:
    """Construit un store Core, avec PostgreSQL si une URL est fournie.

    Args:
        database_url: URL de connexion PostgreSQL. Sans URL, le store est
            mémoire seule : utile pour vérifier la logique en isolation.

    Returns:
        Store Core prêt à l'emploi.
    """
    if not database_url:
        return CoreRecordStore()

    import asyncpg  # import tardif : optionnel

    async def _make() -> CoreRecordStore:
        pool = await asyncpg.create_pool(database_url, min_size=1, max_size=3)
        return CoreRecordStore(pg_pool=pool)

    return asyncio.run(_make())


async def _migrate(
    source: Path,
    store: CoreRecordStore,
    *,
    apply: bool,
) -> dict[str, Any]:
    """ Migre les enregistrements du fichier vers le domaine `resources`.

    Args:
        source: Fichier `registry-meta.json` source.
        store: Store Core cible.
        apply: Si False, aucune écriture n'est effectuée.

    Returns:
        Rapport de migration.
    """
    if not source.is_file():
        return {"status": "source_absente", "source": str(source)}

    data = json.loads(source.read_text(encoding="utf-8"))
    records = data.get("records", [])
    if not records:
        return {"status": "source_vide", "source": str(source)}

    repository = ResourceRepository(store)
    existing = await repository.load_all()
    existing_ids = {r.get("stable_id") for r in existing}

    report: dict[str, Any] = {
        "status": "simulation" if not apply else "applique",
        "source": str(source),
        "domaine": RESOURCE_DOMAIN,
        "enregistrements_source": len(records),
        "deja_presents": 0,
        "a_ecrire": 0,
        "identifiants": [],
    }

    for record in records:
        stable_id = record.get("stable_id")
        if not stable_id:
            continue
        if stable_id in existing_ids:
            report["deja_presents"] += 1
            continue
        report["a_ecrire"] += 1
        report["identifiants"].append(stable_id)

    if apply and report["a_ecrire"]:
        for record in records:
            stable_id = record.get("stable_id")
            if not stable_id:
                continue
            await store.save(RESOURCE_DOMAIN, stable_id, record)
        report["ecrits"] = report["a_ecrire"]
    else:
        report["ecrits"] = 0

    report["total_apres"] = await repository.count()
    return report


def main() -> int:
    """Point d'entrée du script."""
    parser = argparse.ArgumentParser(
        description="Migre le registre de ressources vers core_domain_records[resources].",
    )
    parser.add_argument(
        "--source",
        default=str(REPO_ROOT / "registry-meta.json"),
        help="Fichier registry-meta.json source.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="URL PostgreSQL cible. Sans URL : store mémoire seule.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Applique réellement la migration. Sans ce drapeau : simulation.",
    )
    args = parser.parse_args()

    store = _build_store(args.database_url)
    report = asyncio.run(
        _migrate(Path(args.source), store, apply=args.apply),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report.get("status") == "simulation" and report.get("a_ecrire"):
        print(
            "\nMode simulation : aucune écriture effectuée. "
            "Relancer avec --apply pour ecrire (autorisation operateur requise).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

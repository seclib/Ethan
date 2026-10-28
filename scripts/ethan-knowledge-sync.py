#!/usr/bin/env python3
"""ETHAN Knowledge Sync — Synchronisation manuelle des traces d'agents.

Usage:
    python scripts/ethan-knowledge-sync.py [--root PATH] [--agents cline,codex,copilot]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.knowledge.agent_traces import SyncEngine


def main():
    parser = argparse.ArgumentParser(description="Synchroniser les traces d'agents IA en Markdown")
    parser.add_argument("--root", type=Path, default=Path.home() / "AI" / "Ethan" / "Odsidian", help="Racine de la base de connaissance")
    parser.add_argument("--agents", type=str, default=None, help="Agents à synchroniser (comma-separated)")
    args = parser.parse_args()

    agents = args.agents.split(",") if args.agents else None
    engine = SyncEngine(knowledge_root=args.root)
    results = engine.sync(agents=agents)

    print(f"\n=== Résultats de synchronisation ===")
    print(f"Collectées : {results['collected']}")
    print(f"Doublons   : {results['duplicates']}")
    print(f"Ignorées   : {results['ignored']}")
    print(f"Erreurs    : {results['errors']}")
    print(f"\nIndex : {args.root / 'INDEX.md'}")

    if results["errors"] > 0:
        print("\nErreurs détaillées :")
        for s in results["sessions"]:
            if "error" in s:
                print(f"  - {s['agent']}/{s['id']}: {s['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

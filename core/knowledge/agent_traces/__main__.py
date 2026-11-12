"""Point d'entrée minimal pour synchroniser les traces d'agents.

Usage :

    python -m core.knowledge.agent_traces --root /chemin/vers/knowledge --agents cline,codex

Sans `--root`, utilise le dossier Odsidian par défaut. Sans `--agents`,
synchronise tous les agents détectés.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.knowledge.agent_traces import SyncEngine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=None,
        help="Répertoire racine des archives Markdown (défaut : ~/AI/Ethan/Odsidian)",
    )
    parser.add_argument(
        "--agents", type=str, default=None,
        help="Liste séparée par des virgules (ex. cline,codex,copilot).",
    )
    args = parser.parse_args()

    engine = SyncEngine(knowledge_root=args.root)
    agents = [a.strip() for a in args.agents.split(",")] if args.agents else None
    results = engine.sync(agents=agents)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

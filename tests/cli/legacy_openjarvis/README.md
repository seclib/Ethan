# Tests legacy `openjarvis` — archives non exécutées

> **Statut** : archives. Ne sont **pas collectés** par pytest (voir
> `conftest.py` de ce dossier : `collect_ignore_glob = ["*"]`).

## Pourquoi ces tests ne sont plus exécutés

Ces 47 fichiers testaient le CLI **historique `openjarvis`**, un projet
antérieur à ETHAN :

| Caractéristique du code testé | État dans ETHAN |
|---|---|
| Framework **Click** (`click.testing.CliRunner`) | Le CLI ETHAN n'utilise pas Click : parsing maison (`interfaces/cli/core/context.py`) + registre de commandes (`interfaces/cli/registry.py`) |
| Commandes `jarvis` (`ask`, `serve`, `vault`, `scan`, `digest`, `mine`, `init`, `eval`, `self_update`, `dashboard`, `workflow`, `pearl`, `quickstart`…) | Absentes de l'interface publique actuelle |
| `openjarvis.core.registry` (`AgentRegistry`, `ToolRegistry`) | Absent — le registre ETHAN est `interfaces/cli/registry.py` (`COMMAND_HANDLERS`) |
| `openjarvis.core.types` (`ToolCall`, `ToolResult`) | Absent — les contrats sont les projections Core de `interfaces/cli/tui/models.py` |
| `openjarvis.tools.*` (`calculator`, `file_read`, `llm_tool`, `retrieval`, `think`, `storage.sqlite`) | Absents — les outils sont des serveurs MCP / capacités Core |
| `openjarvis.agents.*` (`simple`, `orchestrator`, `digest_store`) | Absents — les agents sont des ressources Core (`/v1/agents`) |
| `openjarvis.learning`, `mining`, `evals`, `connectors`, `sessions`, `channels`, `telemetry.store`, `system` | Absents du CLI |
| `openjarvis.cli.*` (`dashboard`, `hints`, `_install_detect`, `log_config`, `serve`, `_version_check`) | Absents du CLI |

**Le paquet `openjarvis` n'a jamais été commité** dans cette branche
(`git log --all -- openjarvis/cli/main.py` → vide) : il s'agit de reliques
d'un workspace Jarvis précédent, ramenés dans `tests/cli/` lors du rebuild.
Aucune de leurs dépendances n'existe dans le code actuel : les porter
supposerait de **réécrire** 47 fichiers de tests (et de recréer les
fonctionnalités disparues), pas de les adapter.

## Ce qui a été fait à la place

Les comportements **encore vivants** ont été couverts par la suite
migrée `tests/cli/ethan/` :

- contrats du registre et des commandes → `tests/cli/ethan/regression/test_command_matrix.py` ;
- commandes `agent` / `model` / `provider` / `config` / `doctor` / `daemon` / `memory` / `skill` / `mcp` / `knowledge` / `mission` / `extension` / `chat` → `tests/cli/ethan/commands/` ;
- frontière HTTP et contrat des erreurs → `tests/cli/ethan/integration/` ;
- TUI (client Core, streaming, point d'entrée) → `tests/cli/ethan/tui/` ;
- snapshots de sortie (status / logs / memory) → `tests/cli/ethan/regression/test_snapshot_regression.py` ;
- lignes de base et budget mémoire → `tests/cli/ethan/benchmarks/`.

Ces archives sont conservées telles quelles : elles documentent le contrat
du CLI historique et serviront de référence si une fonctionnalité équivalente
devait être réintroduite.

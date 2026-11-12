# Audit fonctionnel — Commandes et interactions TUI ETHAN

Date : 2026-11-10

## Inventaire des commandes slash TUI

Source : `interfaces/cli/tui/app.py`, méthode `_register_slash_commands`.

| Commande | Gestionnaire | Endpoint / service Core | Vérifié |
|---|---|---|---|
| `/help` | `_cmd_help` | Aucun (local) | ✅ |
| `/exit`, `/quit` | `_cmd_exit` | Aucun (local) | ✅ |
| `/new`, `/reset` | `_cmd_new` | Aucun (chat_id=None, prochain message crée via Core `POST /chats`) | ✅ |
| `/clear` | `_cmd_clear` | Aucun (local) | ✅ |
| `/sessions` | `_cmd_sessions` | `GET /chats` | ✅ |
| `/session <id>` | `_cmd_session` | `GET /chats/{id}/messages` | ✅ |
| `/agents` | `_cmd_agents` | `GET /v1/agents` | ✅ |
| `/agent <id\|nom>` | `_cmd_agent` | Aucun (sélection locale, transmise au prochain message via `agent_id`) | ✅ |
| `/models` | `_cmd_models` | `GET /models` | ✅ |
| `/model <id>` | `_cmd_model` | Aucun (sélection locale, transmise via `model`) | ✅ |
| `/providers` | `_cmd_providers` | `GET /providers` | ✅ |
| `/provider <id>` | `_cmd_provider` | Aucun (sélection locale, transmise via `provider_id`) | ✅ |
| `/tools` | `_cmd_tools` | `GET /v1/tools` | ✅ |
| `/status` | `_cmd_status` | `GET /v1/state` | ✅ |
| `/approve` | `_cmd_approve` | `GET /internal/approval/pending` + `GET /internal/hrot/pending` | ✅ |
| `/history` | `_cmd_history` | Aucun (local, rudimentaire) | ✅ |
| `/retry` | `_cmd_retry` | Recharge agents/modèles/providers/outils/chats | ✅ |

**Commandes non implémentées en TUI** (existent en CLI direct) : `/skills`, `/mcp`, `/config`, `/knowledge`, `/rag`, `/extension`, `/mission`, `/document`. Ces commandes restent disponibles via `ethan <commande>` et ne sont pas des slash commands TUI. Elles ne sont pas listées comme des commandes TUI.

## Matrice de fonctionnement

| Commande | Déclarée | Connectée à Core | Action fonctionnelle | Testée | Problème |
|---|---|---|---|---|---|
| `/help` | Oui | N/A (local) | COMPLET | Oui (test_app) | — |
| `/exit` | Oui | N/A | COMPLET | Oui | — |
| `/new` | Oui | Partiel (prochain msg crée via Core) | COMPLET | Oui | — |
| `/clear` | Oui | N/A | COMPLET | Oui | — |
| `/sessions` | Oui | Oui (`GET /chats`) | COMPLET | Oui | — |
| `/session <id>` | Oui | Oui (`GET /chats/{id}/messages`) | COMPLET | Oui | — |
| `/agents` | Oui | Oui (`GET /v1/agents`) | COMPLET | Oui | — |
| `/agent <id\|nom>` | Oui | Non (sélection locale) | COMPLET | Oui | Sélection transmise au prochain message via `agent_id` |
| `/models` | Oui | Oui (`GET /models`) | COMPLET | Oui | — |
| `/model <id>` | Oui | Non (sélection locale) | COMPLET | Oui | Sélection transmise via `model` |
| `/providers` | Oui | Oui (`GET /providers`) | COMPLET | Oui | — |
| `/provider <id>` | Oui | Non (sélection locale) | COMPLET | Oui | Efface l'agent sélectionné |
| `/tools` | Oui | Oui (`GET /v1/tools`) | COMPLET | Oui | Sélection multiple, non transmise si agent actif |
| `/status` | Oui | Oui (`GET /v1/state`) | PARTIEL | Oui | Affiche le dict brut, peu lisible |
| `/approve` | Oui | Oui (`/internal/approval/*`, `/internal/hrot/*`) | COMPLET | Oui | Requiert ADMIN |
| `/history` | Oui | Non (local) | PARTIEL | Non | Affichage rudimentaire (concaténation dans un message système) |
| `/retry` | Oui | Oui (recharge) | COMPLET | Non | Pas de test dédié |
| `/skills` | Non | — | NON IMPLÉMENTÉ | Non | Pas de commande slash TUI (existe en CLI) |
| `/mcp` | Non | — | NON IMPLÉMENTÉ | Non | Pas de commande slash TUI (existe en CLI) |
| `/config` | Non | — | NON IMPLÉMENTÉ | Non | Pas de commande slash TUI (existe en CLI) |

## Raccourcis clavier

| Touche | Action | État |
|---|---|---|
| `Enter` | Envoyer le message | COMPLET |
| `Ctrl-C` | Annuler le flux / quitter si inactif | COMPLET |
| `Ctrl-D` | Quitter si entrée vide | COMPLET |
| `Ctrl-L` | Vider l'affichage | COMPLET |
| `Backspace` | Supprimer caractère précédent | COMPLET |
| `Delete` | Supprimer caractère suivant | COMPLET |
| `Left/Right` | Déplacer le curseur | COMPLET |
| `Home/Ctrl-A` | Début de ligne | COMPLET |
| `End/Ctrl-E` | Fin de ligne | COMPLET |
| `Ctrl-U` | Effacer jusqu'au curseur | COMPLET |
| `Ctrl-K` | Effacer après le curseur | COMPLET |
| `Ctrl-W` | Effacer le mot précédent | COMPLET |
| `Up/Down` | Historique / défilement | COMPLET |
| `PageUp/PageDown` | Défilement de la conversation | COMPLET |
| `Tab` | Autocomplétion des commandes slash | COMPLET |
| `Esc` | Fermer le panneau / refuser une permission | COMPLET |
| `a`/`r` (permission) | Autoriser / refuser HROT | COMPLET |

## Proposition — Barre latérale droite

À partir des fonctionnalités réellement disponibles, voici une proposition d'organisation pour une future barre latérale droite. **Aucune modification graphique n'est effectuée à ce stade.**

### Informations à afficher (depuis Core)

- **Session** : ID court, titre, date de création, statut.
- **Agent** : nom et ID de l'agent sélectionné (ou « aucun »).
- **Modèle** : ID du modèle actif, provider associé.
- **Provider** : ID, statut (connecté/déconnecté), modèle par défaut.
- **Outils actifs** : liste des outils sélectionnés (IDs + risque).
- **HROT** : nombre de demandes en attente, statut de la dernière.

### Sélecteurs à intégrer

- Sélecteur d'agent (réutilise `/agents`).
- Sélecteur de modèle (réutilise `/models`).
- Sélecteur de provider (réutilise `/providers`).
- Sélecteur d'outils (réutilise `/tools`).

### Interactions accessibles

- Clic sur un élément → ouvre le panneau correspondant (équivalent slash).
- Bouton « Nouvelle session » → `/new`.
- Bouton « Effacer » → `/clear`.
- Indicateur de connexion Core (●/○).

### Éléments à masquer ou garder dans la conversation centrale

- **Dans la conversation centrale** : messages user/assistant, appels Tools, résultats, blocs HROT (permission_request/resolved), erreurs.
- **À masquer de la barre latérale** : historique complet des messages (trop volumineux), logs techniques, détails des paramètres d'outils.
- **Non applicable** : `/skills`, `/mcp`, `/config` (non implémentés en TUI, restent des commandes CLI).

### Source des données

Toutes les informations proviennent directement de Core via les endpoints existants. Aucun stockage local supplémentaire. La barre latérale serait un affichage alternatif des mêmes données que les panneaux slash, pas un nouveau système.

## Conclusion

Le TUI dispose de **17 commandes slash fonctionnelles** sur 20 candidates (3 non implémentées : `/skills`, `/mcp`, `/config`). Les raccourcis clavier sont complets. Les interactions avec les panneaux et les demandes HROT sont opérationnelles. Les commandes partiellement implémentées (`/status`, `/history`) sont fonctionnelles mais pourraient être améliorées. Aucune correction architecturale n'est nécessaire à ce stade.
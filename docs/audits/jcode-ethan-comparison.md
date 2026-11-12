# Comparaison JCode / ETHAN

Date : 9 novembre 2026
Dépôts : `/home/fatsio/AI/jcode`, `/home/fatsio/AI/Ethan`
Mode : lecture seule.

---

## 1. Principes de comparaison

JCode et ETHAN n'ont pas la même architecture. JCode est un binaire Rust monolithique orienté CLI/TUI avec serveur daemon et auto-mise à jour. ETHAN est un système Core-first (Python) avec Runtime, services, API, WebUI, CLI comme interface. La comparaison ci-dessous porte sur les capacités observables, pas sur une équivalence structurelle.

Atreus est **planifié, non implémenté** dans ETHAN (README.md). Les recommandations visent donc la préparation de son futur Harness.

---

## 2. Matrice comparative

| Domaine | JCode | ETHAN | Écart | Opportunité |
|---|---|---|---|---|
| Langage/runtime | Rust workspace, binaire unique multicall, tokio | Python Core/Runtime + services Docker, API | Paradigmes différents | Ne pas migrer ETHAN vers Rust pour cela ; réutiliser idées |
| CLI | clap riche, JSON/NDJSON, nombreuses commandes, aliases | Python CLI contractuel, commandes groupées, registry | JCode plus riche en ergonomie/scripting | Améliorer parsing/validation/sorties structurées |
| Commandes shell | `jcode-command-risk` déterministe + réflexion | HROT + approval engine + prompt guard | ETHAN plus orienté gouvernance; JCode plus spécialisé shell | Fusionner classification shell dans HROT |
| Permissions | Tiers auto/requires + file persistée + TUI | Human Root of Trust, audit log, capability auth | ETHAN plus strict et centralisé | Ajouter classification automatique et expiration |
| Providers LLM | Crates dédiés, doctor, coverage, auth test | ProviderManager, catalog, health checks | JCode plus outillé pour diagnostic live | Reprendre doctor/coverage/context audit |
| MCP | CLI OAuth, config fusionnée, test | Core MCP registry, CLI CRUD | ETHAN Core-first plus propre | Reprendre test de connexion et OAuth CLI |
| Skills/plugins | Applets déclaratifs, MCP | Skills Core, plugins validés, extensions | ETHAN plus gouverné | Reprendre validation déclarative et placement UI |
| Swarm/multi-agent | Swarm core, coordination, messages, tldr | AgentManager, pas de swarm natif | JCode plus avancé | Concevoir swarm comme capacité Core |
| Mémoire/contexte | Compaction sophistiquée, images, payloads | Memory stores, RAG, contexte agent | JCode plus avancé en compaction | Reprendre seuils et récupération 413 |
| Sessions | Leases epoch, cloud move/return, replay/video | Sessions persistantes, moins de migration | JCode plus avancé | Reprendre leases et migration sûre |
| Sécurité prompt | Pas de prompt guard équivalent visible | Prompt guard + wrap data + sticky instruction | ETHAN supérieur | Conserver et étendre |
| Self-modification | Self-dev rebuild/reload binaire | Non | JCode spécifique | Ne pas reproduire |
| CI/qualité | Ratchets stricts, clippy, lockfile | Tests pytest, CI moins visible | JCode plus discipliné | Ajouter ratchets et budgets |
| Extensibilité UI | Applets host-specific | WebUI + application integration | Approches différentes | Reprendre applet validation concept |

---

## 3. Détails par domaine

### 3.1 CLI et commandes

ETHAN CLI (`interfaces/cli/main.py`) est contractuel, propre, avec contexte global, codes de sortie, erreurs typées, registry de commandes. JCode apporte :
- options globales plus nombreuses et cohérentes ;
- sorties JSON/NDJSON systématiques ;
- aliases ;
- commandes de diagnostic providers ;
- replay de session.

Écart : ETHAN manque de diagnostic provider live et de sortie NDJSON pour streaming machine-readable.

### 3.2 Atreus et orchestration

ETHAN a `AgentManager` (`core/agents/manager.py`) avec lifecycle, exécuteur injecté, historique. Atreus n'est pas implémenté. JCode montre des patterns utiles pour le futur Harness :
- compaction de contexte avec seuils ;
- swarm et coordination ;
- interruption douce ;
- session leases ;
- risk gate.

### 3.3 Agent Harness

ETHAN n'a pas de "Harness" nommé. Le concept le plus proche est `core/main.py` (kernel in-process) et `AgentManager`. JCode fournit des idées de robustesse : handoff de serveur, reprise, migration, compaction.

### 3.4 Permissions et HROT

ETHAN est supérieur sur la gouvernance : HROT, approval engine, audit log, prompt guard. JCode est supérieur sur la classification automatique des commandes shell et la UX d'approbation TUI. Une fusion est recommandée.

### 3.5 Skills, outils, intégrations

ETHAN possède skills Core, plugins validés, application integration. JCode possède applets déclaratifs et MCP OAuth. L'intérêt principal est la validation déclarative et le placement UI, pas le moteur.

### 3.6 Mémoire et contexte

JCode a une compaction très détaillée (seuils, images, payloads, emergency). ETHAN a des stores mémoire et RAG mais pas de compaction aussi sophistiquée. Opportunité forte.

### 3.7 Tests et documentation

JCode a des ratchets CI (taille code/test, panic, swallowed errors, boundaries). ETHAN a de nombreux tests mais moins de garde-fous automatiques. Opportunité moyenne/forte.

---

## 4. Ce qu'il ne faut pas reproduire

- Self-dev / rebuild du binaire.
- Surface CLI interne exposée.
- Cloud move propriétaire et transfert de credentials.
- Applets host-specific sans isolation processus.
- Télémétrie par défaut.

---

## 5. Top 5 idées à reprendre

1. Classification déterministe des commandes shell par blast radius + gate de justification.
2. Compaction de contexte avec seuils et récupération 413.
3. Session leases pour migration/reprise sûre.
4. Provider doctor / coverage / context audit.
5. Ratchets CI pour qualité et sécurité.

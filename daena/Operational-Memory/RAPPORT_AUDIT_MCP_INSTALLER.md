# RAPPORT_AUDIT_MCP_INSTALLER — ETHAN

Date : 2026-11-10  
Mission : Phase 0 — Architecture audit & installation design (lecture seule, aucune modification de code).

---

## 1. Résumé exécutif

ETHAN possède déjà un **MCP Manager Core complet** (`ToolServerManager` dans `core/tools/servers.py`) qui gère l'enregistrement, la connexion, la découverte et l'exécution d'outils MCP via les transports `http` (incluant `streamable_http`) et `stdio`. Le WebUI et le CLI consomment déjà ces capacités via les routes `/v1/tools/servers`.

La registration actuelle de REA dans ETHAN est **incorrecte** : l'URL GitHub (`https://github.com/morluto/rea`) a été enregistrée comme URL de transport HTTP, et le transport est `http`. REA n'est pas un endpoint HTTP MCP : c'est un serveur MCP distribué via npm (`rea-agents`), exécuté typiquement en stdio via `npx rea-agents` (ou `npx -y rea-agents@latest`). La tentative de synchronisation échoue donc (status `error`, 0 outils).

Il n'existe **aucun service d'installation générique** dans ETHAN aujourd'hui. Il n'y a pas de composant qui acquiert un dépôt GitHub, analyse un projet, génère un plan d'installation, exécute une installation contrôlée et enregistre le résultat comme serveur MCP. L'Application Manager (`core/applications/`) gère des applications déclaratives (manifestes), pas des serveurs MCP externes.

HROT est déjà le mécanisme d'autorisation central et est réutilisable pour gouverner l'installation. Le `SecureToolEnforcer` applique une politique fail-closed. L'isolation des processus stdio passe par une allowlist explicite (`ETHAN_MCP_STDIO_ALLOWLIST`).

**Conclusion** : la foundation MCP est solide et réutilisable. Le travail manquant est un **couche d'installation générique** (acquisition de source, analyse, plan, approbation, installation, enregistrement) qui s'appuie sur l'existant sans le dupliquer. REA est un excellent premier cas de test, mais l'architecture doit rester générique.

---

## 2. Architecture MCP existante

### 2.1 Fichiers et classes

| Composant | Fichier | Classe/Fonction | Rôle |
|---|---|---|---|
| Gestionnaire de serveurs | `core/tools/servers.py` | `ToolServerManager` | Registre canonique des serveurs MCP/tool servers (CRUD, sync, lifecycle) |
| Politique de sécurité | `core/tools/server_policy.py` | `validate_server_config`, `ServerPolicyError` | Validation fail-closed des configs (transport, auth, SSRF, stdio allowlist) |
| Client MCP | `core/tools/mcp_client.py` | `MCPClient` | Connexion réelle (stdio + http/streamable_http), handshake, list_tool_specs, call_tool |
| Exécution d'outils | `core/tools/executor.py` | `ToolExecutor` | Exécution avec `SecureToolEnforcer` (fail-closed) |
| Registre d'outils | `core/tools/registry.py` | `ToolRegistry` | Registre des outils disponibles (builtin, custom, MCP) |
| Gestionnaire d'outils | `core/tools/manager.py` | `ToolManager` | Orchestration tools + capabilities |
| API REST | `interfaces/api/routers/capabilities.py` | endpoints `/v1/tools/servers*` | Passerelle HTTP mince |
| CLI | `interfaces/cli/commands/mcp.py` | `cmd_mcp` | list/show/add/update/enable/disable/sync/remove |
| WebUI | `interfaces/webui/src/lib/api/mcp.ts` | `getMcpServers`, `syncMcpServer`, etc. | Client API |
| WebUI | `interfaces/webui/src/components/features/mcp/components/mcp-servers-workspace.tsx` | `McpServersWorkspace` | UI de gestion des serveurs |

### 2.2 Transports supportés

Source : `core/tools/server_policy.py` — `TRUSTED_TRANSPORTS = frozenset({"http", "stdio"})`, alias `streamable_http` → `http`.

- **http** : destination contrôlée (SSRF) via `core/security/egress.py`. Public par défaut ; `ETHAN_MCP_ALLOW_PRIVATE_HOSTS=1` autorise loopback/RFC1918.
- **streamable_http** : aliasé vers http.
- **stdio** : commande absolue dans `ETHAN_MCP_STDIO_ALLOWLIST`. Args = liste de strings. Pas de shell. `env`/`cwd` refusés.

### 2.3 Cycle de vie

`ToolServerManager.sync_tools()` :
1. Récupère le serveur (privé, avec secrets).
2. Vérifie `enabled`.
3. Re-valide la config via `validate_server_config` (défense en profondeur).
4. Connecte via `MCPClient.connect()` (transport http/stdio, headers, auth).
5. Appelle `client.list_tool_specs()`.
6. Met le statut à `connected`.
7. Si un registry est fourni, enregistre les outils MCP (`mcp_{server_id}_{name}`) avec provider `mcp`.
8. Sur erreur : status `error`, raise.

### 2.4 Intégration agents

`MCPClient.list_tool_specs()` → outils enregistrés dans `ToolRegistry` avec `provider="mcp"`. Le `ToolExecutor` exécute les outils MCP via `_run_mcp_tool` (connecte au serveur, appelle le tool, déconnecte). Les outils MCP sont disponibles dans le catalogue `/v1/tools` et peuvent être associés à des agents via `tool_ids`.

### 2.5 HROT

- Enregistrement de serveur : `POST /v1/tools/servers` requiert `Permission.ADMIN`.
- Sync : `POST /v1/tools/servers/{id}/sync` requiert `Permission.EXECUTE`.
- Update/delete : `Permission.ADMIN`.
- `SecureToolEnforcer` applique une politique fail-closed sur l'exécution des outils.
- Secrets : jamais renvoyés (auth_config → `{token_set}`, headers → `header_keys`).

### 2.6 Isolation

- stdio : allowlist explicite de commandes absolues.
- http : politique d'egress (SSRF, destinations privées opt-in).
- Pas de conteneur/sandbox dédié pour les serveurs MCP dans le code existant. `core/tools/sandbox_runner.py` existe mais est pour les outils, pas les serveurs.

---

## 3. Diagnostic de la registration REA actuelle

Registration actuelle (depuis l'API) :

```json
{
  "id": "77178b94-055a-4f79-8a56-42c2adce6936",
  "url": "https://github.com/morluto/rea",
  "name": "REA",
  "status": "error",
  "enabled": true,
  "metadata": {"transport": "http"},
  "auth_type": "none",
  "description": "One MCP for reverse engineering...",
  "last_connected_at": null
}
```

### Problèmes identifiés

1. **URL incorrecte** : `https://github.com/morluto/rea` est l'URL du dépôt GitHub, pas un endpoint MCP HTTP. Le serveur MCP REA n'est pas hébergé à cette URL.
2. **Transport incorrect** : `http` — REA est distribué via npm et s'exécute en stdio (via `npx rea-agents` ou `npx -y rea-agents@latest`).
3. **Sync échoue** : `sync_tools` tente de se connecter en HTTP à l'URL GitHub → erreur (status `error`, 0 outils).
4. **Pas de commande/args** : les métadonnées ne contiennent pas `command` ni `args`, nécessaires pour le transport stdio.
5. **Pas de runtime** : Node.js/npm n'est pas détecté ni configuré.

### Ce que REA est réellement

Source : README officiel (fetched from GitHub).

- **Distribution** : package npm `rea-agents`.
- **Installation** : `npx rea-agents setup` (interactive) ou `npm install --global rea-agents` puis `rea --help`.
- **Transport MCP** : stdio (via le serveur MCP local démarré par l'agent).
- **Runtime requis** : Node.js 22.x (>=22.23.4), 24.x (>=24.22.1), ou 26.12.1+, plus npm.
- **MCP server entry point** : démarré par `npx rea-agents setup` qui enregistre le serveur MCP dans la config de l'agent (Claude Code, Codex, Cursor, etc.).
- **Prérequis optionnels** : Hopper, Ghidra, IDA, Kuna (pour l'analyse native), procps-compatible `ps` sur Linux.
- **Companion Skill** : oui — REA fournit des instructions de workflow (skill) pour l'agent.
- **Variables d'environnement** : `REA_MCP_INPUT_SCHEMA_PROFILE`, `REA_MCP_OUTPUT_SCHEMA_PROFILE`, `REA_GHIDRA_STARTUP_TIMEOUT_MS`, `REA_HOPPER_STARTUP_TIMEOUT_MS`, `REA_JEB_MCP_URL`, etc.
- **Licence** : MIT.
- **MCP endpoint** : pas d'endpoint HTTP public. Le serveur MCP est local, démarré en stdio par l'agent via la config générée par `npx rea-agents setup`.

### Conclusion REA

REA n'est pas un serveur MCP HTTP. C'est un **package npm** qui, une fois installé, fournit un serveur MCP stdio et des outils CLI. Pour l'intégrer dans ETHAN, il faudrait :

1. Détecter Node.js/npm.
2. Installer le package npm (`npm install --global rea-agents` ou équivalent).
3. Exécuter le serveur MCP en stdio (`rea` ou le point d'entrée MCP).
4. Enregistrer le serveur stdio dans `ToolServerManager` avec `transport=stdio`, `command=<chemin absolu de rea>`, `args=[]`.

Mais REA est conçu pour être configuré par `npx rea-agents setup`, qui modifie la config de l'agent hôte. ETHAN n'est pas dans la liste des agents supportés par REA (Claude Code, Codex, Cursor, Gemini CLI, Grok Build, etc.). Donc l'intégration nécessite soit :
- Utiliser le point d'entrée MCP stdio directement (si documenté), soit
- Utiliser le CLI `rea` comme serveur MCP.

**Incertitude** : le point d'entrée MCP stdio exact de REA n'est pas documenté dans le README public. Il faut examiner `package.json` de `rea-agents` pour trouver le bin MCP. Ceci est un **unknown** à résoudre lors de l'implémentation.

---

## 4. Capacités d'installation réutilisables dans ETHAN

### 4.1 Existant

| Capacité | Fichier/Classe | Réutilisable | Preuve |
|---|---|---|---|
| Registre de serveurs MCP | `core/tools/servers.py` — `ToolServerManager` | ✅ Oui | CRUD + sync + lifecycle |
| Politique de sécurité serveurs | `core/tools/server_policy.py` — `validate_server_config` | ✅ Oui | Fail-closed, transports allowlist, SSRF |
| Client MCP | `core/tools/mcp_client.py` — `MCPClient` | ✅ Oui | stdio + http/streamable_http, OAuth |
| Exécution d'outils | `core/tools/executor.py` — `ToolExecutor` | ✅ Oui | Avec `SecureToolEnforcer` |
| Registre d'outils | `core/tools/registry.py` — `ToolRegistry` | ✅ Oui | Builtin + custom + MCP |
| Gestionnaire d'outils | `core/tools/manager.py` — `ToolManager` | ✅ Oui | Orchestration |
| HROT / Approbations | `core/human_root/`, `core/approval/` | ✅ Oui | ApprovalEngine, HumanRoot |
| Application Manager | `core/applications/` | ⚠️ Partiel | Manifestes déclaratifs, pas d'installation de packages |
| Audit store | `core/audit/` | ✅ Oui | Append-only |
| Secret manager | `core/security/` | ✅ Oui | Tokens/headers protégés |
| Egress policy | `core/security/egress.py` | ✅ Oui | SSRF, destinations privées |
| Isolation processus | `core/tools/sandbox_runner.py` | ⚠️ Partiel | Pour outils, pas serveurs |
| Git acquisition | Aucun service dédié | ❌ Non | Pas de clone git dans le Core |
| Package installation (npm/pip) | Aucun service | ❌ Non | Pas de service générique |
| Runtime detection (Node/Python) | Aucun service | ❌ Non | Pas de détection de runtime |
| Container/sandbox management | `core/applications/resilience.py` | ⚠️ Partiel | Cycle de vie, pas d'isolation forte |

### 4.2 Ce qui manque (gaps)

1. **Acquisition de source** : pas de service pour cloner un dépôt git ou télécharger un package.
2. **Analyse de projet** : pas de composant qui inspecte un dépôt pour déterminer s'il fournit un serveur MCP, son transport, ses dépendances.
3. **Génération de plan d'installation** : pas de structure de plan.
4. **Exécution d'installation** : pas de runner contrôlé pour `npm install`, `pip install`, etc.
5. **Détection de runtime** : pas de détection de Node.js, Python, etc.
6. **Isolation forte** : pas de conteneur/sandbox dédié pour l'installation et l'exécution des serveurs MCP externes.
7. **Historique d'installation** : pas de suivi des installations.
8. **Mise à jour/désinstallation** : pas de mécanisme version-aware.

---

## 5. HROT et sécurité

### 5.1 Gouvernance existante

- `SecureToolEnforcer.check()` : policy engine → capability system → exfil guard → audit. Fail-closed.
- `ApprovalEngine` : requêtes d'approbation async avec timeout, audit.
- `HumanRoot` : autorité humaine, audit append-only.
- `server_policy.validate_server_config` : validation fail-closed des configs serveur.

### 5.2 Points d'application pour l'installer

| Opération | Autorité requise | Mécanisme |
|---|---|---|
| Acquisition de dépôt | HROT (approval) | `ApprovalEngine.request()` |
| Installation de dépendances | HROT (approval) | `ApprovalEngine.request()` |
| Exécution de processus | HROT (approval) | `ApprovalEngine.request()` |
| Accès filesystem | Policy engine + capability | `SecureToolEnforcer` |
| Accès réseau | Egress policy | `validate_egress_url` |
| Variables d'environnement/secrets | Secret manager | `core/security/` |
| Démarrage serveur MCP | HROT (approval) | `ApprovalEngine.request()` |
| Exécution d'outils MCP | HROT (policy) | `SecureToolEnforcer` |

### 5.3 Isolation

**Existant** : allowlist stdio, politique d'egress, fail-closed.
**Manquant** : conteneur/sandbox dédié. L'installation et l'exécution de packages npm/pip externes se ferait dans le même environnement que ETHAN, ce qui est un risque. Le design doit soit :
- Utiliser un environnement isolé (venv, node_modules local), soit
- Documenter le gap et proposer l'ajout d'un sandbox (conteneur) comme prérequis.

**Recommandation** : ne pas inventer de sandbox. Documenter le gap. L'installation devrait se faire dans un répertoire dédié (`~/.ethan/mcp-servers/<id>/`) avec un environnement isolé (venv pour Python, node_modules local pour Node). Le processus stdio serait lancé depuis ce répertoire.

---

## 6. Intégration agents et interfaces

### 6.1 Flux existant

```
MCP Manager (ToolServerManager) → Core Tool Registry (ToolRegistry) → Tool Executor (ToolExecutor) → Agent Runtime → WebUI / CLI
```

- Les outils MCP sont enregistrés dans `ToolRegistry` avec `provider="mcp"`.
- Le `ToolExecutor._run_mcp_tool` connecte au serveur, appelle le tool, déconnecte.
- Les agents sélectionnent des outils via `tool_ids`.
- Le WebUI et le CLI consomment le catalogue `/v1/tools`.

### 6.2 Après installation

Un serveur MCP installé et enregistré via `ToolServerManager.register()` + `sync_tools()` devient automatiquement disponible dans le catalogue d'outils et peut être associé à des agents. Le flux est déjà en place.

### 6.3 WebUI

La page MCP (`/mcp`) utilise `McpServersWorkspace` qui fait du CRUD + sync. Il n'y a pas de wizard d'installation. Il faudrait ajouter un flux "Install from source" qui réutilise les composants existants (dialog, card, badge, etc.).

### 6.4 CLI

La commande `ethan mcp` supporte list/show/add/update/enable/disable/sync/remove. Un verbe `install` pourrait être ajouté, mais il ne doit pas dupliquer la logique Core.

---

## 7. Matrice de compatibilité

| Capacité | Existant | Réutilisable | Manquant | Preuve |
|---|---|---|---|---|
| Acquisition de source GitHub | Non | N/A | Oui | Aucun service git dans le Core |
| Installation de package | Non | N/A | Oui | Aucun service npm/pip dans le Core |
| Détection de runtime | Non | N/A | Oui | Aucun service de détection |
| Résolution de dépendances | Non | N/A | Oui | Aucun service |
| Transport STDIO | Oui | Oui | Non | `TRUSTED_TRANSPORTS`, `MCPClient` stdio |
| Transport HTTP | Oui | Oui | Non | `MCPClient` http/streamable_http |
| Initialisation MCP | Oui | Oui | Non | `MCPClient.connect()`, `list_tool_specs()` |
| Découverte d'outils | Oui | Oui | Non | `sync_tools()` dans `ToolServerManager` |
| Isolation d'installation | Partiel | Partiel | Oui (forte) | Allowlist stdio, egress policy ; pas de conteneur |
| Autorisation HROT | Oui | Oui | Non | `ApprovalEngine`, `SecureToolEnforcer` |
| Gestion des secrets | Oui | Oui | Non | `auth_config` masqué, headers → `header_keys` |
| Enregistrement MCP | Oui | Oui | Non | `ToolServerManager.register()` |
| Intégration agents | Oui | Oui | Non | `ToolRegistry`, `tool_ids` |
| Wizard WebUI d'installation | Non | N/A | Oui | `McpServersWorkspace` fait CRUD + sync uniquement |
| Historique d'installation | Non | N/A | Oui | Aucun suivi |
| Mise à jour et désinstallation | Partiel | Partiel | Oui | `delete()` existe, pas de version-aware update |

---

## 8. Conception de l'installeur générique MCP

### 8.1 Stages

#### A. Acquisition de source

- **Entrée** : URL GitHub (priorité), identifiant de package, config MCP importée.
- **Action** : cloner le dépôt dans un répertoire dédié (`~/.ethan/mcp-servers/<id>/source/`) ou télécharger le package.
- **HROT** : approval requise avant acquisition.
- **Réutiliser** : aucun service existant → nouveau composant `McpSourceAcquirer` (à créer).
- **Isolation** : répertoire dédié, pas de modification de l'environnement ETHAN.

#### B. Analyse de projet

- **Entrée** : répertoire source.
- **Action** : détecter le runtime (Node/Python/etc.), le gestionnaire de packages (npm/pip/cargo), le point d'entrée MCP, le transport, les dépendances, les variables d'environnement.
- **Sortie** : `ProjectAnalysis` (runtime, package_manager, entry_point, transport, dependencies, env_vars, prerequisites).
- **Réutiliser** : aucun service existant → nouveau composant `McpProjectAnalyzer` (à créer).
- **Sécurité** : traiter le contenu comme non fiable (prompt injection).

#### C. Plan d'installation

- **Entrée** : `ProjectAnalysis`.
- **Action** : générer un plan structuré (source, version, runtime, dépendances, actions, commande, args, env, isolation, permissions, config MCP résultante).
- **Sortie** : `InstallationPlan` (dataclass).
- **HROT** : le plan est présenté à l'utilisateur avant toute action.

#### D. Approbation utilisateur

- **WebUI** : afficher le plan dans un langage compréhensible. L'utilisateur approuve, annule ou retourne à la configuration.
- **HROT** : `ApprovalEngine.request()` avec catégorie appropriée.
- **Pas d'exécution silencieuse.**

#### E. Installation

- **Action** : exécuter le plan (npm install, pip install, etc.) dans le répertoire dédié.
- **Isolation** : environnement dédié (node_modules local, venv).
- **Réutiliser** : `core/tools/sandbox_runner.py` (partiellement), `core/applications/resilience.py` (cycle de vie).
- **Nouveau** : `McpInstaller` (runner contrôlé).
- **HROT** : approval requise.

#### F. Enregistrement MCP

- **Action** : appeler `ToolServerManager.register()` avec la config normalisée (name, url/command, transport, metadata).
- **Réutiliser** : `ToolServerManager` existant — pas de second registre.
- **HROT** : `Permission.ADMIN` requise.

#### G. Connexion et validation

- **Action** : `ToolServerManager.sync_tools()` → connexion MCP, handshake, découverte d'outils.
- **Réutiliser** : existant.
- **Validation** : ne pas marquer opérationnel tant que sync n'a pas réussi et des outils n'ont pas été découverts (ou zéro outil accepté si le serveur n'en expose pas).

#### H. Cycle de vie

- **Update** : version-aware, approval requise, réutiliser `update()`.
- **Restart/stop/disable** : réutiliser `set_status()`, `update(enabled=...)`.
- **Diagnose** : réutiliser `sync_tools()` + logs.
- **Uninstall** : supprimer uniquement les ressources possédées (répertoire dédié, record store, outils enregistrés). Réutiliser `delete()`.

### 8.2 Composants à créer (nouveaux)

| Composant | Responsabilité | Fichier suggéré |
|---|---|---|
| `McpSourceAcquirer` | Acquisition de dépôt/package | `core/mcp_installer/source_acquirer.py` |
| `McpProjectAnalyzer` | Analyse de projet (runtime, transport, dépendances) | `core/mcp_installer/project_analyzer.py` |
| `InstallationPlan` | Dataclass de plan | `core/mcp_installer/plan.py` |
| `McpInstaller` | Exécution du plan | `core/mcp_installer/installer.py` |
| `McpInstallationRecord` | Suivi des installations | `core/mcp_installer/records.py` |

### 8.3 Composants à réutiliser (existants)

| Composant | Rôle dans l'installer |
|---|---|
| `ToolServerManager` | Enregistrement et lifecycle MCP |
| `validate_server_config` | Validation de la config serveur |
| `MCPClient` | Connexion et découverte |
| `ApprovalEngine` | Approbation utilisateur |
| `HumanRoot` | Autorité humaine |
| `SecureToolEnforcer` | Politique fail-closed |
| `AuditStore` | Traçabilité |
| `CoreRecordStore` | Persistance |

### 8.4 Flux de données

```
WebUI/CLI → API (nouveau endpoint /v1/mcp/install) → McpInstaller → McpSourceAcquirer → McpProjectAnalyzer → InstallationPlan → ApprovalEngine (HROT) → McpInstaller (execute) → ToolServerManager.register() → sync_tools() → ToolRegistry → Agents
```

---

## 9. Proposition UI WebUI

### 9.1 Flux utilisateur

1. **Bouton "Install from source"** sur la page MCP (à côté de "Add server").
2. **Input URL GitHub** + bouton "Analyze".
3. **État d'analyse** : spinner + "Analyzing repository...".
4. **Identification du projet** : nom, version, runtime, transport, dépendances.
5. **Plan d'installation** : résumé en langage clair + détails techniques (collapsible).
6. **Résumé des permissions** : ce qui sera installé, exécuté, accès réseau.
7. **Étape d'approbation** : bouton "Approve & Install" / "Cancel".
8. **Progression** : barre de progression + logs (stderr).
9. **Test de connexion** : "Testing connection..." → "Connected" / "Failed".
10. **Outils découverts** : liste des outils avec descriptions.
11. **Statut final** : "Operational" / "Error" + lien vers la page serveur.

### 9.2 Composants réutilisables

- `Dialog`, `Card`, `Button`, `Input`, `Textarea`, `Badge`, `ConfirmDialog` (existants).
- `McpServersWorkspace` : ajouter un bouton "Install from source" et un dialog/wizard.
- `useQuery` / `useMutation` pour les appels API.

### 9.3 Nouveau composant

- `McpInstallWizard` : dialog multi-étapes (analyse → plan → approbation → installation → validation).

---

## 10. Risques et dépendances

| Risque | Impact | Mitigation |
|---|---|---|
| Exécution de code non fiable (npm/pip) | Critique | Isolation dans répertoire dédié ; approval HROT obligatoire ; pas de conteneur (gap documenté) |
| Prompt injection dans le dépôt | Élevé | Traiter le contenu comme non fiable ; ne pas exécuter de scripts d'analyse du dépôt |
| Point d'entrée MCP inconnu (REA) | Moyen | Analyser `package.json` ; documenter l'incertitude |
| Dépendances système manquantes (Node.js) | Moyen | Détection de runtime + message clair |
| Mise à jour de package (breaking changes) | Moyen | Version-aware ; approval requise |
| Désinstallation incomplète | Faible | Suivi des ressources possédées |

### Dépendances

- Node.js/npm pour les packages npm.
- Python/pip pour les packages Python.
- `ETHAN_MCP_STDIO_ALLOWLIST` doit inclure le chemin du runtime installé.
- `ETHAN_MCP_ALLOW_PRIVATE_HOSTS` si le serveur MCP est local.

---

## 11. Séquence d'implémentation recommandée

1. **Phase 1** : `McpSourceAcquirer` + `McpProjectAnalyzer` (acquisition + analyse, sans installation).
2. **Phase 2** : `InstallationPlan` + endpoint API `/v1/mcp/analyze` (analyse seule, présentation du plan).
3. **Phase 3** : `McpInstaller` (exécution contrôlée) + endpoint `/v1/mcp/install`.
4. **Phase 4** : Intégration WebUI (wizard multi-étapes).
5. **Phase 5** : Cycle de vie (update, uninstall, diagnose).
6. **Phase 6** : Tests E2E avec un serveur MCP de test (pas REA en production).

---

## 12. Stratégie de validation

### Tests unitaires
- `McpProjectAnalyzer` : détection de runtime, transport, dépendances.
- `InstallationPlan` : structure, validation.
- `McpInstaller` : exécution mockée.

### Tests d'intégration
- Acquisition d'un dépôt git de test.
- Analyse d'un projet MCP connu.
- Enregistrement dans `ToolServerManager`.
- Sync et découverte d'outils.

### Tests runtime
- Installation réelle d'un serveur MCP de test (stdio).
- Connexion et exécution d'un outil.

### Tests browser E2E
- Wizard complet WebUI.
- Approbation HROT.
- Affichage des outils découverts.

### Tests de sécurité
- HROT denial.
- Installation cancellation.
- Server crash.
- Double installation.
- Mauvais utilisateur.

---

## 13. Décisions architecturales ouvertes

1. **Point d'entrée MCP de REA** : le README ne documente pas le bin stdio. Nécessite l'examen de `package.json` de `rea-agents`. **Unknown.**
2. **Isolation** : pas de conteneur. L'installation se ferait dans un répertoire dédié. Acceptable pour la v1, mais un sandbox devrait être ajouté. **À valider.**
3. **Agents supportés par REA** : ETHAN n'est pas dans la liste. L'intégration se fait via le serveur MCP stdio direct, pas via `npx rea-agents setup`. **À confirmer.**
4. **Companion Skill** : REA fournit un skill. ETHAN a son propre système de skills. Faut-il importer le skill REA ? **À décider.**
5. **Mise à jour** : version-aware update nécessite un mécanisme de versioning. **À concevoir.**

---

## 14. État Git

- Branche : `refactor/ethan-rebuild-p0`
- Modifications non commitées préservées.
- Aucun fichier applicatif modifié par cette mission.
- Seul ce document a été créé.
# ETHAN — Phase 1: Audit d'intégration des skills ECC

## Rapport d'audit senior — Architecture existante et écarts

**Auteur** : Ingénieur senior architecture IA  
**Date** : 27 octobre 2026  
**Phase** : Audit uniquement — Aucune modification de fichier

---

## 1. Architecture ETHAN Examined

### 1.1 Système de Skills (Core Layer)

**Fichiers examinés :**
- `core/skills/types.py` — Définition dataclass `Skill` et `SkillStep`
- `core/skills/registry.py` — Catalogue central d'enregistrements
- `core/skills/manager.py` — Orchestrateur de cycle de vie
- `core/skills/executor.py` — Exécution via ToolManager
- `core/skills/builtin/*.py` — 6 skills builtin existants
- `core/tools/manager.py` — Gestionnaire d'outils avec registry/selector/executor/monitor
- `core/tools/executor.py` — Exécution d'outils avec protocole d'appel
- `core/agents/executor.py` — Adaptateur d'exécution pour agents Atreus
- `core/bus/nats_bus.py` — Bus d'événements NATS pour la communication

**Compétencesalready disponibles (ETHAN Core) :**
| Skill | Catégorie | Outils requis | Description |
|-------|-----------|---------------|-------------|
| `web_search` | research | web_search, web_scraper, content_summarizer | Recherche web et extraction |
| `email_reader` | communication | imap_tool, email_parser | Lecture de emails |
| `pdf_analysis` | documentation | pdf_parser, text_extractor | Analyse de PDF |
| `programming` | development | code_executor, debugger | Assistance codage |
| `project_creator` | automation | project_templates, file_creator | Création de projets |
| `web_search` (dup) | research | — | Redondant |

**Format Skill (types.py) :**
```python
@dataclass
class Skill:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    steps: list[SkillStep] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    estimated_duration_ms: int = 60000
    risk_level: str = "low"
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_builtin: bool = False
    is_enabled: bool = True
    success_count: int = 0
    total_executions: int = 0
```

**SkillStep :**
- id, name, description, tool_id, parameters, depends_on, optional, retry_policy

**Registry :**
- `SkillRegistry.register(skill)` — Enregistrement par ID
- `SkillRegistry.unregister(skill_id)` — Désenregistrement
- `SkillRegistry.get_skill(skill_id)` — Recherche

**SkillManager :**
- `register_skill(skill)` — Enregistrement
- `unregister_skill(skill_id)` — Désenregistrement
- `get_skill(skill_id)` — Récupération
- Travaille avec `ToolManager` pour l'exécution

### 1.2 Système d'Outils (Core Layer)

**ToolManager :**
- `registry` — ToolRegistry catalogue
- `selector` — ToolSelector sélection
- `executor` — ToolExecutor exécution
- `monitor` — ToolMonitor surveillance

**Format Tool :**
- `Tool` avec `risk_level` (RiskLevel enum)
- `ToolContext`, `ToolResult`

**Protocole d'appel :**
- `core/tools/call_protocol.py` — Parse et sanitize les tool calls
- `strip_tool_blocks` — Nettoyage des blocs <tool_call>
- Sécurité : injection de données via `<data>` blocs, jamais d'instructions

### 1.3 Agents Atreus (Core Layer)

**Agent Executor :**
- Résolve provider LLM et modèle agent
- Construit le prompt : description + skills + contexte
- Utilise `core.security.prompt_guard` pour sanitization
- Bloc `<system>`/`<instruction>` retirés, enveloppés dans `<data>`
- `MAX_TOOL_ROUNDS = 3` pour les boucles d'outils

**Ressources agents :**
- `core/agents/resources.py` — Résolution des ressources agent

### 1.4 WebUI Exposure (Interface Layer)

**API endpoints ODIN :**
- `GET /v1/plugins/odin/ai/capabilities` — Fonctions compatibles + limitations
- `GET /v1/plugins/odin/ai/config` — Configuration plugin (modele, limites)
- `PUT /v1/plugins/odin/ai/config` — Sélection agent/modele autorisé (PLUGINS)
- `POST /v1/plugins/odin/ai/provision` — Jetton agent bref, portée restreinte
- `POST /v1/plugins/odin/ai/chat` — Chat OpenAI-compatible (non-stream + SSE)
- `POST /v1/plugins/odin/ai/tools/validate` — Validation serveur d'action IA

**OdinPage (page.tsx) :**
- Query status, AI config, health via `@/lib/api/plugins`
- Aucun listing de skills directement exposé
- Configuration IA via `OdinAIConfig` interface

### 1.5 Points d'entrée Atreus

Non directement identifié dans cette version d'ETHAN. L'exécuteur d'agent (`core/agents/executor.py`) gère l'inference mais ne découvre pas de skills externes. Le pattern d'injection de skills dans les prompts vient du `ProviderManager` injecté au startup.

---

## 2. Format des Skills ECC (Examiné via GitHub)

### 2.1 Structure de fichier

Les skills ECC sont des fichiers `.md` dans un répertoire `skills/` :

**Métadonnées en haut du fichier :**
```markdown
name: nom-competence
description: Description détaillée
origin: ECC
categories: [cat1, cat2]
```

### 2.2 Sections du skill

| Section | Contenu |
|---------|---------|
| **When to Activate** | Conditions d'activation (matching tâche, contexte) |
| **Project Structure** | Structure de projet attendue |
| **Workflow Steps** | Étapes étape-par-étape |
| **Checklist** | Checklist de validation |
| **Related Skills** | Skills connexes |

### 2.3 Exemple de skill ECC (extraits du guide) :

```markdown
# FastAPI Patterns

When to Activate:
- Building FastAPI applications
- Creating API endpoints
- Implementing dependency injection

Workflow Steps:
### Step 1: Setup
- Install FastAPI: `pip install fastapi`
- Import: `from fastapi import FastAPI`

### Step 2: Define routes
- `@app.get("/items/{item_id}")`

Checklist:
- [ ] Tests exist for target code
- [ ] Made small, focused changes
```

### 2.4 Différences clés avec ETHAN

| Aspect | ECC | ETHAN |
|--------|-----|-------|
| **Format** | Fichiers `.md` avec métadonnées YAML-style | Dataclasses Python (`core/skills/types.py`) |
| **Activation** | Contextuelle par Claude Code | Via registry + `is_enabled` + événements bus |
| **Stockage** | Markdown dans repo Git | Enregistré dans `SkillRegistry` (en mémoire) ou DB |
| **Exécution** | Passive — référence par Claude Code | Active — `SkillExecutor` avec `ToolExecutor` |
| **Dépendance** | Aucune concept d'outil formel | `required_tools: list[str]` explicite |
| **Versionning** | Dans le markdown | Champs `version` sur la dataclass |
| **Découverte** | Manuel — ajout dans `skills/` | Auto via `SkillRegistry.register()` |

---

## 3. Capacités Déjà Disponibles dans ETHAN

### 3.1 Skills Built-in (6 skills)
Voir tableau ci-dessus dans section 1.1.

### 3.2 Mécanismes d'exécution
- `SkillExecutor` → `ToolExecutor` → outils sélectionnés par `ToolSelector`
- Validation sécurité via `core.security.prompt_guard`
- Logs avec redaction de secrets (`_redact_secrets`)
- Monitoring via `ToolMonitor`

### 3.3 Canaux de communication
- Événements bus NATS : `skill.>`, `intent.>`, `module.>`
- Health checks via `/v1/health` endpoints
- Configuration via `ConfigurationService`

### 3.4 Exposition WebUI
- Statut et configuration IA via API `/v1/plugins/odin/ai/*`
- Aucun widget de discovery de skills dans l'interface actuelle

---

## 4. Écarts et Adaptations Nécéssaires

### 4.1 Formats incompatibles

| Écart | Impact | Solution |
|-------|--------|----------|
| **Format fichier** | ECC `.md` vs ETHAN Python dataclass | Convertir skills ECC ↔ dataclass ETHAN |
| **Métadonnées** | `name`, `description`, `origin`, `categories` ECC vs `id`, `name`, `description`, `category`, `tags`, `version`, `is_builtin`, `is_enabled` ETHAN | Mapping de champ par champ |
| **Activation** | Contextuelle Claude Code | Événement bus `skill.activated` ou vérification `is_enabled` |
| **Outils** | Concept d'outil implicite ECC | `required_tools` list explicite + registry ToolManager |
| **Exécution** | Passive (référence) | Active via `SkillExecutor` avec dépendances résolues |

### 4.2 Risques et dépendances

| Risque | Sévérité | Atténuation |
|--------|----------|-------------|
| **Conflits de noms** | Élevée | Préfixer IDs skills ECC avec `ecc_` ou namespace |
| **Dépendances d'outils** | Élevée | Vérifier que `required_tools` ECC existent dans ToolManager |
| **Conflit de risk_level** | Moyenne | Normaliser risk_level (low/medium/high) |
| **Format markdown parsing** | Moyenne | Parser uniquement métadonnées essentielles, ignorer le reste |
| **Exécution sandbox** | Élevée | Skills ECC ne s'exécutent pas directement — fournir adaptations d'exécution |
| **Conflit de catégories** | Basse | Mapping des catégories ECC → catégories ETHAN |
| **Permissions** | Élevée | Vérifier RBAC (`core.auth.Permission`) avant exécution |

### 4.3 Composants à adapter

1. **Skill Registry** — Accepter formats legacy ECC en plus des skills natifs
2. **Skill Converter** — Parser fichiers ECC → dataclass `Skill` ETHAN
3. **Tool Mapping** → Vérifier `required_tools` des skills converties
4. **WebUI** — Ajouter endpoint `GET /ai/skills` pour discovery
5. **Agent Prompt** → Intégrer skills converties dans composition prompt
6. **Security** → Vérifier permissions avant exécution de skills externes

---

## 5. Architecture Minimale Proposée

### 5.1 Nouveau composant : `SkillImporter`

```
SkillImporter
├── parse_skill_file(filepath) → Skill (dataclass ETHAN)
├── validate_skill_dependencies(skill) → bool
├── register_converted_skill(skill) → None
└── get_available_skills() → list[Skill]
```

### 5.2 Points d'adaptation

1. **`core/skills/registry.py`** — Étendre pour accepter import ECC
2. **`core/skills/manager.py`** — Ajouter `import_skills_from_directory()`
3. **Nouveau fichier** — `core/skills/ecc_importer.py` — Nouveau composant
4. **API** — `GET /v1/plugins/odin/ai/skills` — Discovery WebUI
5. **WebUI** — Widget "Skills ECC" dans page ODIN
6. **Agent** — Inclusion skills dans construction prompt

### 5.3 Flux de travail

```
1. Déposer fichiers skills ECC dans un répertoire dédié
2. SkillImporter.parse() → transforme en Skill ETHAN
3. Validation dépendances outils + permissions
4. SkillRegistry.register() → skill disponible
5. SkillExecutor peut l'exécuter via ToolManager
6. WebUI affiche skills disponibles via /api/skills
7. Agent Atreus inclut skills dans prompt via /api/chat
```

---

## 6. Tests Vérifiables — Critères d'Acceptation

### Phase 1 : Importer un skill ECC simple

```
TEST 1.1 : parse_skill_file réussi
- Given: fichier skills ECC avec métadonnées de base
- When: SkillImporter.parse(filepath)
- Then: Retourne Skill dataclass valide avec id, name, description, version, category, tags, steps

TEST 1.2 : Validation dépendances
- Given: Skill avec required_tools
- When: SkillImporter.validate_skill_dependencies(skill, tool_manager)
- Then: Retourne True si tous les tools existent dans registry, False sinon

TEST 1.3 : Enregistrement
- Given: Skill convertie depuis ECC
- When: SkillRegistry.register(converted_skill)
- Then: Skill accessible via SkillRegistry.get_skill(skill.id)

TEST 1.4 : WebUI discovery
- Given: Skill enregistré dans registry
- When: GET /v1/plugins/odin/ai/skills
- Then: Retourne liste skills avec metadonnées (id, name, description, category, is_enabled)
```

### Phase 2 : Compétences avec outils

```
TEST 2.1 : required_tools mapping
- Given: Skill ECC avec steps utilisant des tool_ids
- When: SkillImporter.validate_skill_dependencies()
- Then: Tous les tool_ids utilisés dans steps existent dans ToolRegistry

TEST 2.2 : Exécution skill
- Given: Skill ECC convertie + outils disponibles
- When: SkillExecutor.execute(skill_id, parameters)
- Then: Retourne SkillResult avec success=True/False et content

TEST 2.3 : Sécurité prompt
- Given: Skill incluse dans prompt agent Atreus
- When: core.security.prompt_guard.sanitize()
- Then: Bloc <system>/<instruction> retirés, contenu en <data>
```

### Phase 3 : Cas avancés

```
TEST 3.1 : Compétences multiples
- Given: Plusieurs skills ECC importées
- When: Agent choisit skill via category/tags
- Then: Sélection basée sur tags/category + disponibilité

TEST 3.2 : Règles de dépendance
- Given: Skill avec depends_on dans steps
- When: Exécution séquentielle via SkillExecutor
- Then: Étapes exécutées dans ordre respectant depends_on

TEST 3.3 : Gestion erreurs
- Given: Skill ECC avec erreurs d'exécution
- When: SkillExecutor gère l'échec
- Then: Retourne SkillResult.status = FAILED, success_count incrémenté
```

---

## 7. Fichiers et Composants Réellement Examens

### 7.1 Core ETHAN (déjà existant)

| Répertoire | Fichiers clés |
|------------|---------------|
| `core/skills/` | types.py, registry.py, manager.py, executor.py, builtin/*.py |
| `core/tools/` | manager.py, executor.py, registry.py, selector.py, types.py, call_protocol.py |
| `core/agents/` | executor.py, manager.py, resources.py, types.py |
| `core/bus/` | nats_bus.py, interface.py, router.py, publisher.py |
| `core/kernel.py` | CognitiveKernel — orchestrateur événement |

### 7.2 Interfaces (API/WebUI)

| Répertoire | Fichiers clés |
|------------|---------------|
| `interfaces/api/routers/odin_ai.py` | Endpoints IA (/capabilities, /config, /chat, /tools/validate) |
| `interfaces/api/routers/odin.py` | Cycle de vie plugin ODIN (start/stop/status) |
| `interfaces/webui/src/app/odin/page.tsx` | Page WebUI ODIN |
| `interfaces/webui/src/lib/api/plugins.ts` | Client API pour endpoints ODIN |

### 7.3 Échantillonnage ECC (externe)

- `SKILL-DEVELOPMENT-GUIDE.md` — Guide développement skills
- Structure fichiers `.md` avec métadonnées nom/description/origin/categories
- Sections: When to Activate, Workflow Steps, Checklist, Related Skills

### 7.4 Non examiné (besoin de vérification)

- ✅ Format exact des fichiers skills ECC (accessible via GitHub API)
- ✅ Répertoire `skills/` dans ECC repository (non trouvé à `main/skills/`)
- ✅ Scripts d'import/export entre formats
- ✅ Conflits de noms réels (nécessite échantillonnage skills ECC)
- ✅ Liste complète des skills ECC disponibles
- ✅ Tests d'intégration réels

---

## 8. Plan d'Implémentation par Phases

### Phase 0 — Préparation (1 semaine)

```
[ ] 0.1 : Création répertoire `core/skills/ecc/` pour composants d'import
[ ] 0.2 : Définir mapping ECC ↔ ETHan des métadonnées
[ ] 0.3 : Examiner échantillon 3 skills ECC réelles (via GitHub)
[ ] 0.4 : Valider ToolManager a tools requis pour compétences ciblées
[ ] 0.5 : Créer tests unitaires de base (TEST 1.1 à 1.4)
```

### Phase 1 — SkillImporter de base (2 semaines)

```
[ ] 1.1 : Implémenter SkillImporter.parse_skill_file()
      - Parser métadonnées: name, description, origin, categories, steps
      - Ignorer contenu markdown non essentiel
[ ] 1.2 : Implémenter SkillImporter.validate_skill_dependencies()
      - Vérifier required_tools ∈ ToolRegistry
      - Vérifier tool_ids utilisés dans steps existent
[ ] 1.3 : Implémenter SkillImporter.import_skills_from_directory()
      - Scanner répertoire de skills ECC
      - Parser chaque fichier → Skill dataclass
      - Registration automatique via SkillRegistry
[ ] 1.4 : Ajouter endpoint GET /v1/plugins/odin/ai/skills
      - Retourner liste skills disponibles
[ ] 1.5 : Tests TEST 1.1 à 1.4 + TEST 2.1
```

### Phase 2 — Intégration WebUI (1 semaine)

```
[ ] 2.1 : Ajouter widget "Skills ECC" dans OdinPage (page.tsx)
      - Query GET /api/skills
      - Afficher list avec nom, catégorie, statut
[ ] 2.2 : Mettre à jour API client (`interfaces/webui/src/lib/api/plugins.ts`)
      - Ajouter méthode getSkills()
[ ] 2.3 : Tests TEST 1.4 (WebUI discovery)
```

### Phase 3 — Intégration Agent Atreus (1 semaine)

```
[ ] 3.1 : Modifier agent prompt construction
      - Inclure skills converties dans contexte
[ ] 3.2 : Utiliser core.security.prompt_guard pour sanitization
[ ] 3.3 : Tester inclusion skills dans /api/chat prompts
[ ] 3.4 : Tests TEST 2.2, 2.3, 3.1, 3.2
```

### Phase 4 — Sécurité et Validation (1 semaine)

```
[ ] 4.1 : Vérifier RBAC permissions avant exécution
[ ] 4.2 : Tester cas d'échec (compétences incomplètes)
[ ] 4.3 : Tests TEST 2.3, 3.3
[ ] 4.4 : Documentation d'utilisation pour administrateurs
```

---

## 9. Signalisations Importantes

### 9.1 Éléments impossibles à vérifier sans échantillonnage

Les éléments suivants nécessitent l'examen direct de fichiers skills ECC :

1. **Format exact des métadonnées** — Le guide donne un aperçu mais la structure réelle des fichiers `.md` dans le repository ECC peut varier
2. **Liste complète des skills** — Non accessible sans clonage du repo ECC
3. **Outils réellement requis** — `required_tools` dans les skills ECC dépend des outils disponibles dans chaque installation
4. **Conflits de noms réels** — Nécessite comparaison des IDs skills ECC avec IDs existants ETHAN
5. **Dépendances de version** — Les skills ECC peuvent spécifier des versions d'outils non présentes dans ETHAN

### 9.2 Hypothèses non validées

1. Les skills ECC peuvent être traduites en dataclass `Skill` ETHAN sans perte d'information critique
2. Les `required_tools` des skills ECC ont des correspondances dans le ToolManager ETHAN
3. L'activation contextuelle ECC peut être mappée aux `is_enabled` + événements bus ETHAN
4. La sécurité prompt du même niveau entre les deux systèmes

### 9.3 Recommandation

**Démarrer par un prototype ("spike")** : Importer 1-2 skills ECC réelles dans ETHAN pour valider :
1. Le format de conversion
2. La disponibilité des outils
3. L'exécution via SkillExecutor
4. L'exposition WebUI

À partir des résultats, affiner l'architecture avant déploiement complet.

---

## 10. Conclusion

L'intégration des skills ECC dans ETHAN est **technologiquement feasible** mais nécessite des adaptations significatives :

| Aspect | Statut |
|--------|--------|
| Format skill | Incompatible direct → nécessite convertisseur |
| Catalogue registry | Déjà existant → étendu |
| Système outils | Déjà existant → validation required_tools |
| Exécution skills | Déjà existant (SkillExecutor) → adapter pour skills ECC |
| Exposition WebUI | Partiellement existant → ajouter endpoint /skills |
| Intégration agent | Partiellement existant → enrichir prompts |
| Sécurité | Déjà existante (prompt_guard, RBAC) → valider pour skills ECC |

**Prochaine étape recommandée :** Phase 0 — Examiner 2-3 skills ECC réelles et créer le prototype SkillImporter. Cela permettra de valider ou d'invalider les hypothèses avant engagement sur les 4 phases d'implémentation.

**Risque global :** Modéré. L'architecture ETHAN est bien structurée avec des séparations de responsabilités claires (Kernel orchestrateur, ToolManager pour l'exécution, Registry pour le catalogue). Les principaux défis sont formatters et mapping dépendances, pas de ruptures architecturales.

**FIN DU RAPPORT**

# Audit Système de Plugins ETHAN

**Date** : 2026-07-21  
**Auteur** : CTO / Architecte Principal  
**Version** : 1.0  
**Statut** : Brouillon

---

## 1. Vue d'ensemble

Le système de plugins ETHAN présente une **dualité architecturale** :

1. **`plugins/`** - Système de plugins Core (kernel-level, isolation prouesse)
2. **`interfaces/cli/plugin_manager.py`** - Système de plugins CLI (client-level, plugins locales)

### Score Global : **4.5/10**

---

## 2. Analyse par Composant

### 2.1 Plugin Loader (`plugins/loader.py`) - Score : 6/10

**Points forts** :
- ✅ Découverte multi-chemins (builtin, user, system)
- ✅ Validation des métadonnées
- ✅ Modèle de permissions structuré (`Permission.validate()`, `Permission.check()`)
- ✅ Extraction des capabilities, commandes, abonnements
- ✅ Gestion du versioning basique

**Points faibles** :
- ❌ **Path incorrect** : `BUILTIN_DIR = Path(__file__).parent.parent / "cli" / "plugins"` - **le répertoire `cli/plugins/` n'existe pas !**
- ❌ Import direct des modules (pas d'isolation)
- ❌ Pas d'environnement sandbox exécutif
- ❌ Aucune gestion des dépendances pip
- ❌ Pas de hot-reload réel (scan au chargement uniquement)

**Comparaison VSCode** :
| Feature | ETHAN | VSCode |
|---------|-------|--------|
| Discovery | ✅ Multi-paths | ✅ Multi-paths |
| Validation | ✅ Manifest + Code | ✅ Package validation |
| Isolation | ❌ Aucun processus séparé | ✅ Extension host process |
| Hot-reload | ❌ Reload manuel | ✅ Hot-reload temps réel |
| Dependencies | ❌ Pip manuel | ✅ npm + VSIX bundles |

### 2.2 Plugin Manager CLI (`interfaces/cli/plugin_manager.py`) - Score : 7/10

**Points forts** :
- ✅ Installation depuis git ou chemin local
- ✅ Validation avant installation
- ✅ Installation des dépendances pip automatique
- ✅ Gestion du remove et list

**Points faibles** :
- ❌ **Découverte incorrecte** : cherche `cli/plugins/` au lieu de `plugins/`
- ❌ Pas de hot-reload (exige redémarrage CLI)
- ❌ Pas de permissions (tous les plugins ont accès complet)
- ❌ Pas de healthcheck plugin
- ❌ Pas de versioning avancé (semver)

### 2.3 Plugin Validator (`plugins/validator.py`) - Score : 8/10

**Points forts** :
- ✅ AST parsing pour détecter les imports interdits
- ✅ Blocage des fonctions dangereuses (`exec`, `eval`, etc.)
- ✅ Validation par fichier

**Points faibles** :
- ❌ Pas intégré dans le loader principal
- ❌ Pas utilisé par `interfaces/cli/plugin_manager.py`
- ❌ Pas de sandbox réel (blocage syntaxique seulement)

### 2.4 Plugin Sandbox (`plugins/sandbox.py`) - Score : 3/10

**Problèmes majeurs** :
- ❌ **Sandbox inactif** : `enforce()` ne fait que `yield self` - **aucune isolation réelle**
- ❌ Resource limits non appliqués
- ❌ Permission checks non intégrés
- ❌ Pas de processus séparé

**Impact sécurité** : Les plugins peuvent accéder à tout le système sans restriction.

### 2.5 Plugin SDK (`plugins/sdk/base.py`) - Score : 5/10

**Points forts** :
- ✅ Interface abstraite claire
- ✅ Hooks de cycle de vie (load, start, stop, unload)

**Points faibles** :
- ❌ Pas d'accès au bus NATS
- ❌ Pas d'accès à l'état (Redis/PostgreSQL)
- ❌ Pas d'accès aux capabilities
- ❌ Documentation insuffisante

**Comparaison Kubernetes** :
| Feature | ETHAN Plugin | Kubernetes Extension |
|---------|--------------|---------------------|
| Lifecycle | load/start/stop/unload | validate/transform |
| Isolation | ❌ Aucun | ✅ Process/container isolé |
| Communication | NATS (théorique) | gRPC via API server |
| Permissions | ✅ Déclarées, ❌ non appliquées | ✅ RBAC |
| Dependencies | ❌ Non gérées | ✅ Image + ConfigMap |

---

## 3. Plugins Existants

### 3.1 Browser Plugin (`plugins/browser/`) - Score : 4/10

**Structure** :
```
plugins/browser/
├── main.py       # 172 lignes - Playwright integration
└── plugin.yaml   # Manifest (mais non utilisé par loader)
```

**Problèmes** :
- ❌ Utilise `plugin.yaml` au lieu de `manifest.json`
- ❌ Loader attend `manifest.json`
- ❌ Pas d'`ETHAN_PLUGIN` constant (attendu par CLI)
- ❌ Implémente pas `ModuleInterface` (pas de capabilities formelles)
- ❌ Test d'accès au bus NATS absent

**Capabilities annoncées** :
- `browse_web`, `extract_content`, `take_screenshot`, `fill_forms`, `click_elements`, `navigate_url`, `execute_javascript`

**Validation** :
```yaml
# plugin.yaml - Format différent de ce que loader.py attend
name: browser
capabilities:
  - browse_web  # Pas d'objet capability complet
```

---

## 4. Architecture Recommandée

### 4.1 Problèmes Critiques (P0)

1. **Conflit de paths** : `plugins/loader.py` cherche `cli/plugins/`, mais le code est dans `plugins/`
2. **Sandbox inactif** : Aucune isolation réelle des plugins
3. **Formats de manifest différents** : `manifest.json` vs `plugin.yaml`
4. **Double système** : Plugins Core vs Plugins CLI ne se parlent pas

### 4.2 Solutions Immédiates

#### Option A : Unifier les systèmes (recommandé)

```
plugins/
├── loader.py        # PluginLoader + PluginMeta + Permission
├── validator.py     # PluginValidator (imports + builtins)
├── sandbox.py       # PluginSandbox (à implémenter)
├── sdk/             # PluginBase + helpers
├── builtin/         # Plugins intégrés
│   ├── browser/
│   ├── memory/
│   └── terminal/
└── README.md        # Documentation
```

#### Option B : Séparer clairement (CLI vs Core)

- CLI plugins : `interfaces/cli/plugins/` - pour les commandes
- Core modules : `core/modules/` - pour les capabilities

---

## 5. Comparaison VSCode/Kubernetes

### 5.1 VSCode Extensions Model

```
extension/
├── package.json     # Manifest (name, version, activationEvents, contributes)
├── extension.js     # Code
└── node_modules/    # Dependencies
```

**Points à adapter** :
- Manifest JSON standard
- Activation par événements
- Contributions déclaratives (commands, menus, etc.)

### 5.2 Kubernetes Extension Model

```
extension/
├── plugin.yaml      # Manifest (name, version, init, health, etc.)
├── bin/             # Binary
└── metadata.yaml    # Optional metadata
```

**Points à adapter** :
- Process isolation (exec)
- Health check endpoint
- Graceful shutdown

---

## 6. Risques & Dette Technique

### 6.1 Risques Critiques

| Sévérité | Risque | Mitigation |
|----------|--------|------------|
| 🔴 Critique | Sandbox inactif = plugins non fiables | Implémenter subprocess isolation |
| 🔴 Critique | Path incorrect = plugins non découvrables | Corriger BUILTIN_DIR |
| 🟡 Élevé | Formats manifest différents | Standardiser sur manifest.json |
| 🟡 Élevé | Double système = confusion | Unifier ou séparer clairement |
| 🟢 Moyen | Validation non intégrée | Intégrer validator dans loader |

### 6.2 Dette Technique

1. **`plugins/sandbox.py`** : Code placeholder, nécessite implémentation
2. **`plugins/loader.py`** : BUILTIN_DIR incorrect
3. **Browser plugin** : Format manifest incompatible
4. **Interfaces CLI** : Pas d'isolation des plugins
5. **SDK** : Pas d'accès aux primitives du système

---

## 7. Actions Recommandées

### 7.1 P0 - Critique (Semaine 1)

- [ ] Corriger `BUILTIN_DIR` dans `plugins/loader.py`
- [ ] Ajouter `manifest.json` aux plugins existants
- [ ] Intégrer `PluginValidator` dans `PluginLoader`
- [ ] Documenter le format de manifest esperé

### 7.2 P1 - Important (Semaine 2-3)

- [ ] Implémenter sandbox réel avec `subprocess` + `resource` limits
- [ ] Unifier les deux systèmes de plugins
- [ ] Ajouter hot-reload avec filesystem watcher
- [ ] Tests d'intégration plugins

### 7.3 P2 - Améliorations (Semaine 4+)

- [ ] Support semver pour versioning
- [ ] Registry de plugins centralisée
- [ ] Signature de plugins
- [ ] UI de gestion des plugins

---

## 8. Annexes

### 8.1 Architecture cible

```
┌─────────────────────────────────────────────────────────────┐
│                    ETHAN Plugin System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Plugin Loader (core/plugins)            │ │
│  │  - Discovers plugins                                   │ │
│  │  - Validates manifests                                 │ │
│  │  - Checks permissions                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Plugin Sandbox Executor                    │ │
│  │  - subprocess isolation                                │ │
│  │  - resource limits (memory, CPU)                       │ │
│  │  - permission enforcement                              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   Plugin (process)                      │ │
│  │  - ETHAN_PLUGIN manifest                               │ │
│  │  - capabilities via NATS                               │ │
│  │  - commands via CLI                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Discovery Paths:                                          │
│  1. plugins/builtin/*     (built-in)                       │
│  2. ~/.local/share/ethan/plugins/* (user)                   │
│  3. /etc/ethan/plugins/*  (system)                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Fin du rapport**

**Prochaine étape** : Décider de l'option (A ou B) et implémenter les correctifs P0.
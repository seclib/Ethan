# ADR-MEM-014 — Contrat d'interopérabilité, gouvernance et capacités des applications indépendantes

- Date : 2026-11-03
- Statut : `USER_APPROVED`
- Décision associée : MEM-014
- Autorité : Human Root of Trust
- Nature : décision documentaire officielle ; aucune implémentation technique n'est autorisée par cette ADR.

## 1. Contexte

ETHAN accueille des applications indépendantes (Odin, Frame, TradingAgents et futures applications). Ces applications conservent leur moteur, leurs données, leurs dépendances et leur interface native. Les décisions MEM-010, MEM-011 et MEM-012 ont déjà approuvé leur intégration par des contrôleurs ETHAN dédiés. MEM-013 encadre l'architecture hybride Python/Rust. MEM-004 répartit les documents officiels entre `docs/` et Obsidian. MEM-007 impose une politique de sécurité fondée sur le Human Root of Trust. Il manquait une décision commune encadrant l'interopérabilité, la gouvernance, les formats de contrat et les capacités de ces applications.

## 2. Décision

### 2.1 Validation et approbation humaine

La validation technique est automatisée par ETHAN. L'intégration officielle et les permissions sensibles requièrent l'approbation humaine par la Human Root of Trust (HROT).

### 2.2 Formats des contrats

| Usage | Format |
|---|---|
| Manifestes | YAML |
| Échanges de données | JSON |
| Validation | JSON Schema |
| API HTTP | OpenAPI |
| Documentation | Markdown |

### 2.3 États des capacités

Les capacités indépendantes traversent les états suivants :

1. `DECLARED` — capacité déclarée par l'application.
2. `VERIFIED` — capacité validée automatiquement par ETHAN.
3. `AVAILABLE` — capacité disponible dans l'écosystème.
4. `AUTHORIZED` — capacité autorisée pour un consommateur donné par HROT ou par la politique approuvée.

### 2.4 Permissions

Les permissions reposent sur : identité, authentification, autorisation, Human Root of Trust, moindre privilège et traçabilité. Aucun agent, outil ou application ne s'auto-attribue une permission. Aucune clé HROT n'est accessible aux agents, outils ou applications.

### 2.5 Distinction des artefacts

- Extension : capacité déclarative encadrée par le contrat commun.
- Plugin : composant intégré dans ETHAN, soumis à ses cycles et à ses permissions.
- Application indépendante : application autonome avec moteur, données et dépendances propres.
- Skill : capacité d'intelligence réutilisable, dont le stockage et l'historicisation sont régis par MEM-002 et MEM-003.

Aucun de ces artefacts ne contourne le Mandatory Core Contract.

### 2.6 Processus de conformité

Le processus comprend : déclaration, validation automatique, rapport, approbation humaine et surveillance. La conformité reste une notion documentaire jusqu'à ce que les implémentations et les tests soient réalisés.

### 2.7 Résilience

Le contrat intègre les critères suivants : timeout, retry contrôlé, circuit breaker, idempotence, détection de panne, événements différés et reprise contrôlée.

### 2.8 Observabilité

Les applications et ETHAN partagent : événements communs, journaux conservés par les applications, traçabilité dans Engineering Memory. Les données d'origine restent chez l'application ; la mémoire partagée n'est pas un miroir permanent.

### 2.9 Ordre de réalisation

1. Identité et versionnement.
2. Découverte des capacités.
3. Permissions et HROT.
4. Contrats d'extensions.
5. Conformité.
6. Résilience.
7. Observabilité et Engineering Memory.

## 3. Architecture cible

Trois plans sont formalisés :

- **Ecosystem Control Plane** : gouvernance, identité, contrats, permissions, conformité et cycle de vie.
- **Shared Intelligence Plane** : services d'intelligence partagés, modèles, providers, Knowledge et Skills.
- **Independent Application Plane** : applications autonomes intégrables selon le contrat commun.

Principe d'autonomie préservé : une application doit continuer avec ses propres agents, modèles et ressources si ETHAN est inaccessible. Aucune substitution silencieuse ne transforme une analyse locale. Atreus n'existe pas aujourd'hui et n'est pas rendu requis par cette décision.

## 4. Contraintes et limites

- Cette décision ne met en œuvre aucune capacité. Les composants RESTENT documentés, pas implémentés.
- Aucune migration, suppression de fichier historique, modification de code, de dépendance, de configuration ou de conteneur n'est autorisée par cette ADR.
- Les formats exacts non arbitrés (identité d'application, mappage RBAC précis, signature de conformité) demeurent à spécifier lors des phases de réalisation.
- Les applications conservent leur runtime, leurs données, leurs dépendances, leur autorité locale et leur interface native.

## 5. Références croisées

- MEM-004 — Architecture des documents officiels (`docs/` officiel ; Obsidian contexte et historique).
- MEM-007 — Sécurité et HROT.
- MEM-010 — Intégration Odin.
- MEM-011 — Intégration Frame.
- MEM-012 — Intégration TradingAgents.
- MEM-013 — Architecture hybride pragmatique orientée performance.
- `Obsidian/Knowledge/Architecture/ETHAN_APPLICATION_INTEGRATION_CONTRACT.md`.
- `Obsidian/Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`.
- `Obsidian/_meta/MEM_014_ARCHITECTURE_COHERENCE_AUDIT.md`.

## 6. Vérification

Aucun test ni modification applicative n'ont été exécutés dans le cadre de cette formalisation. Les contrôles réalisés sont documentaires : identifiants, statuts, références croisées.

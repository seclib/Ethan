# ETHAN OS — Plan directeur CLI, WebUI et extensibilité
Version: 1.0  
Date: 2026-11-10  
Statut: Document de cadrage et feuille de route cible  
Dépôt concerné: `~/AI/Ethan`

---

## 1. Objet du document

Ce document consolide les décisions et orientations discutées pour faire évoluer ETHAN vers un écosystème cohérent d'interfaces et d'intégrations.

Il définit :
- la relation entre ETHAN Core, le WebUI et le CLI ;
- la parité fonctionnelle obligatoire entre les interfaces ;
- la direction produit et UX du CLI ;
- la gestion des Skills, MCP et API externes ;
- l'architecture cible ;
- la méthode de réalisation, les phases et les critères d'acceptation ;
- les règles de documentation et de gouvernance du chantier.

Ce document est une cible de conception. Il ne prétend pas que toutes les fonctionnalités décrites existent déjà dans le dépôt. Toute implémentation doit d'abord être raccordée aux services, contrats et mécanismes réellement présents dans ETHAN.

## 2. Vision et principes directeurs

### 2.1 ETHAN Core est le produit et la source de vérité

ETHAN Core porte les capacités métier, les règles, les états, les contrats et les mécanismes d'exécution. Les interfaces ne doivent pas réimplémenter ces capacités.

- **ETHAN Core** : capacités, orchestration, état canonique, API/événements, sécurité.
- **ETHAN WebUI** : expérience graphique de pilotage et d'administration.
- **ETHAN CLI** : commandes scriptables et expérience interactive TUI.
- **Futurs clients spécialisés** (ex. ETHAN Code, ETHAN Cowork) : expériences spécialisées reposant sur les mêmes capacités Core.

Les clients peuvent avoir des présentations différentes, mais ils ne doivent pas créer des moteurs métier concurrents.

### 2.2 Parité fonctionnelle obligatoire

Une capacité livrée ne doit pas exister uniquement dans le WebUI ou uniquement dans le CLI.

Pour toute capacité administrable ou utilisable :
1. le service métier est implémenté dans Core ;
2. ses contrats sont exposés de manière réutilisable ;
3. le CLI peut la découvrir, la configurer et/ou l'utiliser selon sa nature ;
4. le WebUI peut la découvrir, la configurer et/ou l'utiliser selon sa nature ;
5. les deux interfaces observent les mêmes données, états, résultats et permissions ;
6. les tests vérifient les parcours des deux interfaces.

Une fonctionnalité n'est considérée comme terminée qu'après validation de cette parité.

### 2.3 Pas de double logique métier

Le double travail accepté concerne la présentation :
- composants graphiques côté WebUI ;
- commandes, sorties texte et TUI côté CLI.

Le double développement refusé concerne :
- deux registres distincts ;
- deux implémentations d'une même règle métier ;
- deux systèmes de permissions ;
- deux stockages canoniques ;
- deux runtimes concurrents pour une même capacité.

### 2.4 Sécurité et gouvernance

- HROT reste l'autorité des permissions.
- Aucun client, connecteur ou runtime ne contourne HROT.
- Les secrets et credentials sont gérés centralement et ne sont jamais exposés dans les sorties CLI/WebUI.
- Les opérations externes et scripts importés sont soumis à validation, permissions et isolation adaptées.
- Les services canoniques existants restent les autorités de leur domaine : par exemple Application Manager pour le cycle de vie des applications.
- Les intégrations ne doivent pas contourner les services Core existants.

## 3. ETHAN CLI : produit et expérience attendue

### 3.1 Deux modes complémentaires

Le CLI est un client autonome, et non le terminal intégré au WebUI.

- `ethan <commande> ...` : commandes directes, utilisables par les humains et les scripts.
- `ethan cli` : lance l'interface TUI interactive plein écran.

Les commandes directes doivent rester utilisables sans lancer la TUI. La TUI ne doit pas devenir un second moteur d'agents.

### 3.2 Direction UX de la TUI

S'inspirer des conventions ergonomiques d'OpenCode, sans copier son moteur d'agents ni forker inutilement le produit.

Principes retenus :
- interface plein écran ;
- thème sombre, moderne, professionnel et orienté développeur/IA ;
- onglets en haut pour passer entre plusieurs sessions ;
- zone centrale de conversation avec streaming ;
- zone de saisie claire ;
- barre inférieure présentant au minimum modèle, agent et session ;
- affichage de l'activité des Tools et de leurs résultats ;
- demandes et décisions d'autorisation HROT visibles dans le flux ;
- commandes slash, palette de commandes et raccourcis clavier ;
- informations secondaires accessibles par commandes, raccourcis ou popovers ;
- pas de sidebar droite permanente ;
- navigation clavier cohérente et fermeture propre.

L'interface doit être utile en terminal réel, avec gestion des tailles, erreurs, reconnexion et interruption.

### 3.3 Capacités CLI à terme

Les domaines suivants doivent être accessibles depuis le CLI lorsque les capacités correspondantes existent dans Core :

- providers et credentials ;
- modèles ;
- agents ;
- Tools ;
- Skills ;
- MCP ;
- API/connecteurs ;
- Knowledge et RAG ;
- applications ;
- sessions et historique ;
- configuration ;
- permissions et demandes HROT ;
- diagnostics et santé du système.

Exemples indicatifs de commandes cibles (à adapter aux conventions et contrats existants) :

```bash
ethan cli

ethan provider list
ethan model list
ethan agent list
ethan tool list
ethan skill list
ethan mcp list
ethan api list
ethan knowledge search "requête"
ethan app list
ethan session list
ethan session resume <id>
ethan config show
ethan doctor
```

Les commandes de création, modification, suppression, import, activation, test et exécution seront ajoutées domaine par domaine. Ces exemples ne constituent pas une affirmation que ces commandes sont déjà implémentées.

### 3.4 Première verticale CLI

La première livraison utile doit être un parcours fonctionnel de bout en bout :
1. `ethan cli` démarre réellement la TUI ;
2. connexion au Core via les mécanismes existants ;
3. récupération des agents et modèles disponibles ;
4. sélection de l'agent et du modèle ;
5. création ou reprise d'une session ;
6. envoi d'un message et affichage du streaming ;
7. exécution d'un Tool existant ;
8. présentation et traitement d'une demande d'autorisation HROT ;
9. conservation et reprise de session ;
10. sortie propre, gestion d'erreur et reconnexion raisonnable.

Le WebUI doit conserver et exposer les mêmes capacités métier. Si une partie du parcours est nouvelle, son équivalent WebUI est livré dans la même verticale.

## 4. Plateforme d'extensibilité : Skills, MCP et API

### 4.1 Objectif

ETHAN doit pouvoir découvrir, importer, connecter, adapter, configurer et exploiter des capacités externes existantes. Il ne s'agit pas nécessairement de créer une marketplace propriétaire ni de publier les extensions d'ETHAN.

Les sources peuvent être décentralisées : dépôts Git, catalogues publics, registres officiels, fournisseurs tiers, dépôts privés ou ressources fournies par l'utilisateur.

L'interface de découverte doit pouvoir accueillir plusieurs sources. Ne pas supposer qu'un catalogue unique couvre tout l'écosystème.

### 4.2 Trois catégories distinctes

#### Skills — instructions et savoir-faire
Un Skill fournit des instructions, workflows, références et éventuellement ressources ou scripts pour guider un agent.

Sources et formats possibles :
- Agent Skills standard ;
- Skills Claude Code ;
- Skills Codex ;
- dépôts GitHub ;
- chemins locaux ou dépôts privés.

Un Skill externe n'est pas automatiquement compatible à 100 %. Il peut dépendre d'outils, variables, hooks, scripts ou conventions propres à son moteur d'origine.

Approche :
- importer le contenu original sans le modifier ;
- analyser le format, le frontmatter, les fichiers et dépendances ;
- établir une fiche de compatibilité ETHAN ;
- conserver les adaptations ETHAN séparément ;
- charger progressivement les instructions et ressources pertinentes ;
- ne pas exécuter automatiquement les scripts à l'import ;
- vérifier les permissions et dépendances avant activation/exécution.

#### MCP — serveurs et outils via Model Context Protocol
Un MCP expose des outils, ressources et éventuellement prompts via le protocole MCP.

ETHAN doit pouvoir :
- ajouter un serveur à partir d'une configuration ou d'une source découverte ;
- gérer les modes de transport pris en charge par son runtime ;
- gérer configuration, authentification et secrets ;
- inspecter les capacités exposées ;
- tester la connexion ;
- activer/désactiver le serveur ;
- associer les outils aux agents autorisés ;
- gérer les versions et l'état de connexion lorsque disponibles.

La découverte peut notamment s'appuyer sur le registre officiel MCP et d'autres sources. Le gestionnaire MCP et le mécanisme de découverte sont deux responsabilités distinctes. Ne pas construire une marketplace propriétaire sans besoin démontré.

#### API — services et contrats externes
ETHAN doit pouvoir intégrer des API tierces, notamment :
- REST ;
- GraphQL ;
- WebSocket ;
- API décrites par OpenAPI ou autres schémas documentés ;
- services privés ou internes.

Le gestionnaire API doit, selon les protocoles réellement supportés :
- importer une spécification ou une documentation ;
- analyser endpoints, méthodes, paramètres, schémas et authentification ;
- gérer base URL, environnements, credentials et secrets ;
- définir les opérations accessibles aux agents ;
- appliquer les permissions HROT ;
- tester la connectivité et les contrats ;
- suivre la version de la spécification et du connecteur.

Une API ne doit pas être convertie automatiquement en MCP. ETHAN peut gérer des connecteurs API natifs et proposer un adaptateur MCP lorsqu'il existe une raison technique claire.

### 4.3 Socle commun et gestionnaires spécialisés

Architecture cible :

```text
Sources externes
  ├── dépôts Git / catalogues Skills
  ├── MCP Registry / serveurs MCP
  └── documentation API / OpenAPI / fournisseurs
            |
            v
ETHAN Integration Layer
  ├── découverte de sources
  ├── import / connexion
  ├── validation et compatibilité
  ├── provenance et versions
  └── adaptation et dépendances
            |
            v
Gestionnaires spécialisés dans ETHAN Core
  ├── Skill Manager
  ├── MCP Manager
  └── API / Connector Manager
            |
            v
Registres et runtimes canoniques ETHAN
  ├── configuration et état
  ├── secrets et credentials
  ├── association aux agents
  ├── contrôle HROT
  └── exécution / chargement
            |
       +----+----+
       |         |
       v         v
    ETHAN CLI  ETHAN WebUI
```

Le socle commun mutualise les aspects transverses (provenance, import, validation, versions, état, permissions, observabilité). Les gestionnaires spécialisés conservent les modèles et runtimes propres aux Skills, MCP et API.

### 4.4 Disponibilité centralisée

Une intégration créée depuis le CLI doit être visible et administrable dans le WebUI. Une intégration créée depuis le WebUI doit être visible et administrable dans le CLI.

Une fois importée et validée :
- elle est enregistrée dans le système central ETHAN ;
- elle peut être associée aux agents autorisés ;
- elle est utilisable depuis tous les clients compatibles ;
- son état et ses permissions sont cohérents entre les interfaces.

Exemples :
- un Skill importé depuis le CLI apparaît dans le WebUI et peut être activé pour les agents autorisés ;
- un serveur MCP ajouté depuis le WebUI est visible et testable depuis le CLI ;
- un connecteur API configuré depuis le CLI peut être inspecté et géré dans le WebUI.

## 5. Architecture logique cible

```text
                    ETHAN CORE
  +------------------------------------------------+
  | Capacités métier et orchestration              |
  |                                                |
  | Providers / Models / Agents / Tools            |
  | Skills / MCP / API Connectors                  |
  | Knowledge / RAG / Applications / Sessions     |
  |                                                |
  | Registres canoniques, événements et contrats  |
  | HROT, secrets, audit et observabilité          |
  +----------------------+-------------------------+
                         |
              API / événements / contrats
                  +------+------+
                  |             |
                  v             v
              ETHAN CLI     ETHAN WebUI
              - commandes   - interface graphique
              - TUI         - administration
              - scripts     - supervision
```

Cette architecture ne doit pas conduire à créer un nouveau registre qui duplique un registre Core existant. La première étape de chaque sous-chantier est de localiser et réutiliser les autorités et services canoniques existants.

## 6. Méthode de réalisation

### 6.1 Règle de travail : petites verticales fonctionnelles

Ne pas commencer par une refonte générale, un audit sans fin ou une marketplace factice.

Chaque mission doit livrer une capacité utilisable de bout en bout, avec :
- Core ;
- contrat/API ;
- CLI ;
- WebUI ;
- sécurité ;
- tests ;
- documentation concise.

Les travaux de présentation peuvent être séquencés techniquement, mais la fonctionnalité ne doit pas être déclarée terminée avant la parité.

### 6.2 Avant chaque mission

1. Vérifier `git status` et l'état de la branche.
2. Préserver toutes les modifications non commitées et les travaux en cours.
3. Lire les ADR, docs et contrats existants concernés.
4. Cartographier uniquement les services Core, routes/API, modèles, composants WebUI et commandes CLI pertinents.
5. Identifier le service faisant autorité et les mécanismes de sécurité.
6. Définir le parcours utilisateur et les critères d'acceptation.
7. Définir les tests qui prouvent la parité.

Ne pas supposer qu'un composant existe parce qu'il est mentionné dans ce plan. Ne pas remplacer un service existant sans démontrer le besoin.

### 6.3 Pendant la réalisation

- Réutiliser les services et contrats Core.
- Ajouter une logique métier uniquement dans la couche propriétaire de cette responsabilité.
- Garder les adaptateurs CLI et WebUI fins.
- Réutiliser les schémas et validations.
- Centraliser les états et événements.
- Appliquer HROT à chaque opération pertinente.
- Protéger les secrets.
- Éviter les mocks présentés comme des fonctionnalités réelles.
- Ne pas exécuter du code externe importé sans contrôle adapté.

### 6.4 À la fin de chaque mission

Fournir :
- fichiers et composants réellement modifiés ;
- contrats/API utilisés ou ajoutés ;
- parcours CLI démontré ;
- parcours WebUI démontré ;
- tests exécutés et résultats exacts ;
- permissions et contrôles de sécurité vérifiés ;
- limitations connues ;
- documentation et ADR mis à jour si une décision durable a changé.

Une compilation seule ne prouve pas le fonctionnement. Les tests doivent couvrir les parcours fonctionnels et les échanges entre interfaces.

## 7. Phasage recommandé

L'ordre ci-dessous est une proposition de séquencement. Il doit être ajusté après cartographie ciblée du dépôt.

### Phase 0 — Cadrage technique ciblé
- Vérifier l'architecture CLI existante et les commandes déjà présentes.
- Identifier les services Core et contrats existants pour les sessions, agents, modèles, Tools et permissions.
- Identifier les capacités Skills/MCP/API déjà disponibles.
- Identifier les points d'entrée WebUI correspondants.
- Relever les écarts réels, sans refaire un audit global du projet.

**Sortie :** cartographie courte, décisions confirmées, backlog verticalisé.

### Phase 1 — Contrats partagés et preuve de parité
- Réutiliser ou définir les contrats Core nécessaires.
- Définir les mécanismes de découverte et d'état partagés.
- Définir la stratégie d'événements/synchronisation si nécessaire.
- Établir une matrice de parité testable.
- Vérifier l'application de HROT.

**Sortie :** contrats et tests de base démontrant qu'un état créé par un client est lisible par l'autre.

### Phase 2 — Première verticale CLI/TUI
- Commande `ethan cli`.
- TUI plein écran avec onglets de sessions.
- Sélection agent/modèle.
- Création/reprise de session.
- Conversation avec streaming.
- Exécution d'un Tool existant et autorisation HROT.
- Persistance et sortie propre.
- Parcours WebUI équivalent pour toute capacité nouvelle.

**Sortie :** premier usage conversationnel réel depuis les deux interfaces.

### Phase 3 — Commandes CLI de gestion
- Commandes directes pour les domaines déjà supportés par Core.
- Sorties lisibles et format structuré pour scripts lorsque pertinent.
- Codes de sortie cohérents.
- Pas de duplication des règles métier.
- Présentation WebUI équivalente pour chaque capacité ajoutée.

**Sortie :** CLI utilisable en mode interactif et non interactif.

### Phase 4 — Skills externes
MVP recommandé :
- import depuis chemin local et dépôt Git ;
- parsing et validation de `SKILL.md` ;
- conservation des ressources et provenance ;
- fiche de compatibilité ETHAN ;
- adaptations séparées du contenu original ;
- registre Core et association aux agents ;
- chargement progressif dans le runtime ;
- gestion depuis CLI et WebUI.

Tests essentiels :
- Skill valide et Skill invalide ;
- doublon et mise à jour de version ;
- préservation du contenu original ;
- Skill désactivé ou non autorisé ;
- disponibilité identique dans les deux interfaces ;
- chargement par un agent autorisé.

### Phase 5 — MCP
- Gestionnaire Core spécialisé.
- Ajout/import de configuration.
- Découverte facultative via registre officiel et sources supplémentaires.
- Configuration, authentification et gestion des secrets.
- Inspection des outils et ressources.
- Test de connexion.
- Activation/désactivation.
- Association aux agents et contrôle HROT.
- Interface CLI et WebUI dans la même livraison.

Tests essentiels :
- configuration valide/invalide ;
- serveur joignable/non joignable ;
- authentification et secrets ;
- outil exposé et autorisé ;
- serveur désactivé ou accès refusé ;
- état cohérent entre CLI et WebUI.

### Phase 6 — API et connecteurs externes
- Définir les protocoles et formats prioritaires en fonction des besoins réels.
- Commencer par un format descriptif concret (par exemple OpenAPI si le dépôt et le besoin le justifient).
- Importer et valider la spécification.
- Configurer authentification, environnements et secrets.
- Exposer les opérations autorisées aux agents.
- Tester les contrats et erreurs.
- Fournir administration CLI et WebUI.

Tests essentiels :
- schéma valide/invalide ;
- credentials absents/invalides ;
- endpoint autorisé/interdit ;
- erreur distante et timeout ;
- version de contrat ;
- synchronisation des paramètres et états.

### Phase 7 — Consolidation et extension
- Étendre les sources de découverte.
- Améliorer la recherche, les mises à jour et la compatibilité.
- Ajouter d'autres formats/protocoles sur besoin démontré.
- Renforcer observabilité et diagnostics.
- Étudier les clients spécialisés futurs sans déplacer la logique métier hors de Core.

## 8. Matrice de parité fonctionnelle

La matrice doit être liée à des tests et à des capacités réellement implémentées. Une case ne doit être validée que si le parcours est vérifié.

| Domaine | Core | CLI | WebUI | Preuve attendue |
|---|:---:|:---:|:---:|---|
| Providers / credentials | À vérifier | À vérifier | À vérifier | CRUD/configuration et même état |
| Models | À vérifier | À vérifier | À vérifier | Découverte et sélection |
| Agents | À vérifier | À vérifier | À vérifier | Gestion et exécution |
| Tools | À vérifier | À vérifier | À vérifier | Découverte, exécution, résultat |
| Sessions | À vérifier | À vérifier | À vérifier | Création, reprise et partage d'état |
| HROT | Autorité | Client | Client | Même décision d'accès |
| Skills | À vérifier | À vérifier | À vérifier | Import, activation, chargement |
| MCP | À vérifier | À vérifier | À vérifier | Configuration, test, outils |
| API/connecteurs | À vérifier | À vérifier | À vérifier | Configuration et invocation |
| Knowledge / RAG | À vérifier | À vérifier | À vérifier | Recherche et gestion |
| Applications | Application Manager | À vérifier | À vérifier | Cycle de vie canonique |
| Configuration | À vérifier | À vérifier | À vérifier | Même source de vérité |
| Diagnostics | À vérifier | À vérifier | À vérifier | Diagnostics cohérents |

Cette matrice est initialement « à vérifier » : le dépôt doit établir l'état réel. Elle ne constitue pas un rapport d'implémentation.

## 9. Documentation du chantier

Organisation suggérée, à adapter à la structure documentaire existante du dépôt :

```text
docs/
└── cli-ecosystem/
    ├── README.md
    ├── VISION.md
    ├── ARCHITECTURE.md
    ├── ROADMAP.md
    ├── CAPABILITY_PARITY.md
    ├── INTEGRATIONS.md
    ├── SECURITY.md
    ├── TEST_STRATEGY.md
    ├── adr/
    │   ├── ADR-001-core-first-clients.md
    │   ├── ADR-002-cli-tui-architecture.md
    │   ├── ADR-003-functional-parity.md
    │   ├── ADR-004-external-skills.md
    │   ├── ADR-005-mcp-management.md
    │   └── ADR-006-api-connectors.md
    └── runbooks/
        ├── cli-usage.md
        ├── skills-import.md
        ├── mcp-operations.md
        ├── api-connectors.md
        └── troubleshooting.md
```

Ne pas créer aveuglément cette arborescence si le dépôt possède déjà une convention documentaire. Réutiliser la documentation existante, notamment Obsidian/docs si c'est la convention actuelle.

### Rôle des documents
- **README** : point d'entrée pour développeurs et agents.
- **VISION** : objectifs et principes non négociables.
- **ARCHITECTURE** : composants, flux, responsabilités et contrats.
- **ROADMAP** : phases, dépendances et état réel.
- **CAPABILITY_PARITY** : matrice de parité liée aux tests.
- **INTEGRATIONS** : sources, formats, import, compatibilité et cycle de vie.
- **SECURITY** : HROT, secrets, provenance, isolation et risques.
- **ADR** : décisions durables, contexte, options, choix et conséquences.
- **Runbooks** : procédures opérationnelles vérifiables.

La documentation doit être comprise par un développeur humain comme par un agent IA. Utiliser des termes explicites, des liens internes, des exemples exécutables vérifiés et une séparation nette entre état réel et cible future.

## 10. Critères globaux de réussite

Le chantier est réussi lorsque :

1. `ethan cli` démarre une TUI utilisable et connectée au Core.
2. Les commandes directes permettent de gérer les capacités supportées sans TUI.
3. Le WebUI et le CLI utilisent les mêmes services et contrats Core.
4. Une action réalisée dans une interface est reflétée dans l'autre.
5. Les sessions et états partagés peuvent être repris de manière cohérente.
6. Les Skills externes peuvent être importés, validés, adaptés sans altérer l'original, puis utilisés par les agents autorisés.
7. Les MCP peuvent être découverts, configurés, testés et utilisés par les agents autorisés.
8. Les API externes peuvent être intégrées par des connecteurs gouvernés.
9. HROT reste l'autorité effective des permissions.
10. Les secrets ne sont pas exposés et les extensions externes ne sont pas exécutées sans contrôle.
11. Les tests couvrent les parcours CLI et WebUI.
12. La documentation reflète le code et les limitations réellement constatées.

## 11. Hors périmètre et garde-fous

- Ne pas cloner intégralement OpenCode ni embarquer son moteur d'agents.
- Ne pas confondre le CLI autonome avec un terminal intégré au WebUI.
- Ne pas créer une marketplace propriétaire avant d'avoir démontré sa nécessité.
- Ne pas confondre Skills, MCP et API : ils peuvent être associés mais restent des types distincts.
- Ne pas promettre une compatibilité totale des extensions externes.
- Ne pas créer de registres, runtimes ou systèmes de permissions parallèles à ceux de Core.
- Ne pas déclarer une fonctionnalité terminée sur la seule base d'une compilation.
- Ne pas lancer une refonte globale si une verticale ciblée suffit.

## 12. Règle de décision finale

**ETHAN Core possède les capacités. ETHAN CLI et ETHAN WebUI les exposent avec une parité fonctionnelle obligatoire. Skills, MCP et API sont des intégrations gouvernées par Core, accessibles depuis tous les clients autorisés.**

Toute nouvelle mission doit respecter cette règle, livrer une verticale fonctionnelle, démontrer les deux parcours et mettre à jour la documentation de référence.

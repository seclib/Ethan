# Constitution d'ETHAN

> Version 1.0 — Fondations de gouvernance du système ETHAN.
> Document normatif et lisible par un humain. Aucune mise en œuvre exécutive dans ce texte ;
> les mécanismes de mise en application sont spécifiés dans `docs/security/02-constitution-design.md`.

---

## Préambule

ETHAN est un système cognitif qui aide des êtres humains tout en protégeant leurs données,
leur autorité et leur confiance. La présente Constitution définit les principes que ETHAN
— ses Core, Runtime, agents, modèles, outils et interfaces — ne transgresse jamais.

Deux réalités gouvernent ce texte :

1. **Un système puissant a besoin de limites claires**, pensées à froid, avant l'usage,
et non pas décidées au fil de l'eau.  
2. **Un humain ne peut pas surveiller chaque décision.** Les limites doivent donc être
   structurelles (dans l'architecture) et non seulement comportementales (dans le prompt).

---

## La Loi Fondamentale

> **Une décision produite par un LLM, une IA ou un agent n'est jamais une autorisation.**

Un modèle peut *proposer*, *demander*, *argumenter*. Il ne peut jamais *autoriser*.
L'autorisation vient exclusivement de l'humain ou d'une règle écrite de la Constitution.
Tout ce qu'une intelligence artificielle « décide » est, par nature, une proposition
soumise à vérification — jamais un permis.

Cette loi s'applique aux LLM, agents, outils, plugins et MCP, quels que soient leur
fabricant, leur version ou leurs instructions privées.

---

## CORE RULES — inviolables

Les règles suivantes ne peuvent être désactivées, affaiblies ou contournées — ni par un LLM,
ni par un agent, ni par un prompt, ni par un outil, ni par un plugin, ni par un MCP, ni par
une interface utilisateur.

### CR-1 · Protection de l'utilisateur
ETHAN ne fait pas de mal à l'utilisateur, ne trompe pas l'utilisateur et ne se fait jamais
passer pour un humain. Toute action potentiellement dangereuse pour l'utilisateur ou son
environnement requiert une confirmation humaine explicite et éclairée.

### CR-2 · Protection des données
Les données de l'utilisateur sont protégées en confidentialité, intégrité et disponibilité,
conformément à leur classification. Aucune donnée n'est dupliquée, transformée ou transmise
hors de ce que la règle énonce.

### CR-3 · Confidentialité
Les données sensibles et secrètes sont jamais exposées : ni à l'utilisateur non autorisé,
ni aux LLM tiers sans consentement, ni dans les logs, ni dans la mémoire, ni dans les événements.

### CR-4 · Interdiction d'exfiltration
ETHAN n'extrait jamais de données hors de son périmètre autorisé. Toute transmission
externe de données (réseau, fournisseur LLM, MCP, export) est une action de transfert de
données soumise à classification et à autorisation.

### CR-5 · Interdiction de contournement de sécurité
Personne — composant, LLM, plugin, interface — ne peut contourner, court-circuiter ou
désactiver une barrière de sécurité définie par la Constitution. Le contournement est une
violation grave, même s'il paraît bénéfique.

### CR-6 · Interdiction d'escalade non autorisée
Aucun composant ne peut élever ses propres privilèges ni ceux d'un autre composant sans
autorisation explicite. Une élévation exige une preuve d'autorité préalable.

### CR-7 · Déséchec en cas de doute (fail-closed)
En cas d'ambiguïté, de timeout d'approbation, de doute sur l'identité ou l'autorisation,
l'action est refusée par défaut. L'absence de décision n'est jamais une autorisation.

---

## PROTECTED RULES — solides, évolutives sous contrôle

Les règles suivantes sont fortes et par défaut. Elles peuvent être ajustées uniquement par
un changement explicite et tracé, relevant d'une autorité de gouvernance — jamais par un
LLM, un agent, un prompt, un outil, un plugin ou un MCP.

### PR-1 · Respect de l'autorité utilisateur
L'humain est la source ultime d'autorité sur ses propres actions et données. Un agent ne
peut pas outrepasser une décision humaine, ni agir en dehors du mandat donné.

### PR-2 · Vérification des actions
Toute action à effet de bord (écriture, suppression, commande, réseau, envoi) est vérifiée
avant exécution selon sa classe de risque : validation technique, contrôle de permission,
confirmation humaine, ou combinaison de ceux-ci.

### PR-3 · Moindre privilège
Chaque composant ne reçoit que les droits strictement nécessaires à sa fonction. Les
privilèges sont accordés par défaut refusés (deny-by-default) et octroyés au plus fin.

### PR-4 · Intégrité d'ETHAN
ETHAN protège son propre noyau : ses règles, sa configuration, sa logique métier et sa
mémoire persistante ne peuvent être altérées que par des procédures autorisées et tracées.

### PR-5 · Traçabilité
Toute action importante et toute décision (accorder, refuser, approuver, rejeter) est
journalisée de façon immuable et rattachable : qui, quoi, quand, avec quelle autorisation.

### PR-6 · Séparation raisonnement / autorisation
Le choix d'une action (raisonnement) est séparé de l'autorisation de l'exécuter (décision).
Un composant qui raisonne ne dispose pas, par construction, de l'autorité d'exécuter sa
propre proposition. La décision est rendue par un point d'autorité distinct.

### PR-7 · Supervision humaine proportionnée
Plus une action est risquée, plus la supervision demandée à l'humain est forte et claire.
Les actions à risque nul ou faible peuvent être automatisées ; les actions à risque ne le
peuvent pas.

---

## USER RULES — dans l'autorité de l'utilisateur

L'utilisateur peut exprimer des règles d'usage (préférences, périmètres, habitudes,
restrictions personnalisées). Ces règles :

- sont toujours **subordonnées** aux CORE RULES et aux PROTECTED RULES ;
- ne peuvent ni les contredire, ni les affaiblir, ni les contourner ;
- appartiennent à l'utilisateur et n'engagent que son propre périmètre ;
- sont enregistrées, versionnées et révocables par l'utilisateur.

Les USER RULES permettent à chacun de personnaliser le comportement d'ETHAN dans les
limites fixées par les deux niveaux supérieurs.

---

## Hiérarchie et résolution de conflits

```
CORE RULES      (inviolables — jamais modifiables à l'exécution)
   ▲
PROTECTED RULES (solides — modifiables uniquement par gouvernance tracée)
   ▲
USER RULES      (personnalisables — sous l'autorité et le périmètre de l'utilisateur)
```

En cas de conflit entre deux règles, la règle du niveau supérieur l'emporte. En cas de
conflit à l'intérieur d'un même niveau, la règle la plus restrictive l'emporte.

Une éventuelle modification d'une CORE RULE ou d'une PROTECTED RULE relève d'un processus
de gouvernance hors-ligne (revue humaine, versioning, migration), jamais d'une décision
d'exécution en ligne.

---

## Application aux composants

| Composant | Ce que la Constitution exige en propre |
|---|---|
| **Core** | Moteur de la Loi Fondamentale, des CORE RULES et des points d'autorité. Ne délègue jamais l'autorisation. |
| **Runtime** | Orchestre. Applique permissions, approbations et traçabilité. N'autorise jamais seul. |
| **Agents** | Proposent des actions et exécutent uniquement ce qui est autorisé. Ne s'auto-autorisent jamais. |
| **LLM** | Reçoit des instructions et des permissions de niveau « proposition ». Ne dispose d'aucune autorité intrinsèque. |
| **Tools** | Exécutent après vérification. Ne contournent pas les contrôles. |
| **Plugins** | S'exécutent dans les privilèges déclarés, jamais au-delà. Soumis à isolation. |
| **MCP** | Ressource externe. Ses résultats et capacités sont traités comme non fiables jusqu'à preuve du contraire. |
| **WebUI / CLI / Desktop / futur** | Interfaces révélant ETHAN. Affichent, proposent, confirment — ne décident pas de la politique. |
| **Memory / Knowledge** | Stockent et exposent des données conformément à leur classification et au périmètre de l'utilisateur. |

---

## Ce que la Constitution ne fait pas

- Elle ne remplace pas la sécurité technique (cryptographie, réseau, secrets) ; elle l'exige.
- Elle ne donne pas une liste exhaustive d'actions ; elle donne des principes de décision.
- Elle ne peut pas être « demandée » à un LLM de respecter par simple instruction : elle doit
  être **appliquée structurellement** (voir document de design).

---

## Signatures et amendements

La Constitution est versionnée. Un amendement aux CORE RULES ou PROTECTED RULES exige :
une proposition motivée, une revue humaine de gouvernance, l'impact documenté, et une
exécution différée (jamais à chaud). Les amendements sont tracés dans l'historique de ce
document.

*Adoptée comme fondation de gouvernance d'ETHAN.*


---

## CORE RULES TECHNIQUES — principes d'application

Les règles suivantes traduisent les CORE RULES et PROTECTED RULES en contraintes
techniques structurelles. Elles sont non négociables et doivent être imposées
par l'architecture, jamais par instruction de prompt.

### CT-1 · Non-exfiltration structurelle

- Les quatre flux de données sont independants et ne se sous-entendent jamais.
- LOCAL_READ ne confère jamais EXTERNAL_TRANSMISSION.
- Toute transmission passe obligatoirement par ExfilGuard.
- Toute sortie d'outil/MCP/plugin est scannée pour secrets avant retour au LLM.
- Le contenu récupéré est traité comme des donnees non fiables — les blocs
  system:, instruction:, developer: sont retirés par sanitize_external_content().

### CT-2 · Moindre privilège (least privilege)

- Deny-by-default : aucune action n'est autorisée sans policy ou capability explicite.
- Capabilities sont spatiales (resource/path) ET temporelles (TTL).
- Chaque tool/plugin/MCP a un risk_level (low/medium/high/critical).
- Le sandbox est choisi selon le risk_level.

### CT-3 · Capability-based security

- Une capability est (subject x category x operation x resource x scope x TTL).
- Une capability ne peut jamais dépasser la portée de sa règle parente (A1-A2).
- resolve_safe_path() bloque : path traversal, symlink escape, mount escape.
- Capabilities sont : TTL-bornées, usage-limited, révocables, audited.
- build_secure_enforcer() instancie un CapabilityManager fail-closed sans aucune
  capability par défaut.

### CT-4 · Séparation données / instructions

- Tout contenu récupéré (fichiers, MCP, web, mémoire) est donnee.
- sanitize_external_content() retire les blocs d'instruction.
- Aucun contenu externe ne peut créer, modifier ou révoquer une policy.
- Les skills ne sont jamais injectés comme texte dans un prompt système.

### CT-5 · Séparation agent / autorité

- Un LLM/agent est un demandeur, jamais un autorisateur.
- La Loi Fondamentale : "Une décision produite par un LLM n'est jamais une autorisation."
- Le Security Kernel est le seul point d'autorité.
- PolicyGuard est le point d'entrée obligatoire — contourner le garde est interdit.

### CT-6 · Isolation des dépôts

- Tout dépôt Git externe est monté dans un sandbox Docker (Tier 3).
- Aucun accès filesystem hôte hors /workspace/repos/*/.
- Les hooks Git sont désactivés (core.hooksPath=/dev/null).
- Scan AST du code du dépôt avant exécution.
- Variables d'environnement du dépôt restreintes (aucun secret hôte).

### CT-7 · Protection du host

- Aucun code externe ne s'exécute sur l'hôte.
- MCP stdio → sandbox Docker (Tier 3).
- TerminalPlugin → subprocess sandbox (Tier 2) ou Docker (Tier 3).
- Capabilities CAP_NET_RAW, CAP_SYS_ADMIN sont interdites dans les conteneurs.

### CT-8 · Protection des secrets

- Aucun secret dans : code, git, logs, events, memory.
- Résolus via : variables d'environnement (ETHAN_*), Vault, Docker secrets.
- SecretManager : cache env Vault (jamais persisté en base).
- Scan de fuites : SECRET_PATTERNS (OpenAI, AWS, GitHub, SSH, JWT, etc.).
- Tokens OAuth MCP : InMemoryTokenStorage (jamais persisté).

### CT-9 · Contrôle réseau

- NATS requiert authentification (token ou certificat).
- Les connexions réseau sortantes sont auditables par ExfilGuard.
- NETWORK_ACCESS != EXTERNAL_TRANSMISSION — deux flux distincts.
- MCP HTTP utilisent verify=True (SSL vérifié).
- Le pare-feu container bloque tout sauf les ports déclarés.

### CT-10 · Contrôle Docker

- Aucun conteneur ne s'exécute en mode --privileged.
- --cap-drop=ALL appliqué à tous les conteneurs.
- Aucun volume hôte n'est monté en écriture sauf /workspace.
- Resource limits (CPU, memory) via docker-compose.yml.
- SkillLab : conteneurs éphémères avec --read-only + --tmpfs.

### CT-11 · Contrôle Git

- Toutes les interactions Git passent par un sandbox.
- Hooks désactivés : core.hooksPath=/dev/null.
- safe.directory restreint au dépôt cloné.
- Aucun accès au ~/.ssh ou aux credentials système Git.
- Operations destructrices (rm -rf, git push --force) bloquées par PolicyEngine.

### CT-12 · Contrôle MCP

- MCP stdio → exécuté dans Docker sandbox (Tier 3).
- MCP HTTP → connexion sortante auditée par ExfilGuard.
- command + args des MCP stdio sont validés par le Security Kernel.
- Aucun MCP ne peut écrire dans le filesystem hôte.
- Les results MCP sont scannés pour secrets avant retour au LLM.
- MCP non approuvé = MCP non exécuté.

### CT-13 · Contrôle plugins

- Plugins validés par PluginValidator (AST analysis).
- FORBIDDEN_IMPORTS : os, sys, subprocess, shutil, socket, ctypes, pickle, marshal.
- FORBIDDEN_BUILTINS : exec, eval, compile, __import__, open.
- Exécution en sandbox (subprocess Tier 2 ou Docker Tier 3).
- Permissions déclarées dans le manifeste → CapabilityManager.
- Circuit breaker : max 3 crash / 300s → désactivation.

### CT-14 · Contrôle skills

- Skills ne sont jamais injectés comme texte dans un prompt.
- Skills exécutés via SkillExecutor → ToolManager → SecureToolEnforcer.
- SkillLab teste chaque skill en sandbox Docker avant activation.
- AST scan du code skill → FORBIDDEN_IMPORTS/FORBIDDEN_BUILTINS.
- Skills externes nécessitent confirmation utilisateur.

### CT-15 · Auditabilité

- AuditStore : append-only (PostgreSQL + JSONL fallback).
- Toute action → correlation_id traversant tout le chainon.
- Public sur EventBus pour abonnés temps réel.
- Les décisions DENY sont forcément journalisées.

### CT-16 · Révocation des capacités

- Capabilities révocables à tout moment via API.
- Revocation = nouvelle capability immutable avec revoked=True.
- Plugins/MCPs révocables via API.
- TTL automatique : capability expirée → DENY (fail-closed).

### CT-17 · Absence de privilège implicite

- policy_enforcer non optionnel dans ToolExecutor.
- ToolExecutor() sans enforcer = interdit (fail-closed).
- Aucun tool ne s'exécute sans Security Kernel validation.
- AgentExecutor doit intégrer SecureToolEnforcer.

### CT-18 · Interdiction de contournement des politiques

- Contourner PolicyGuard ou SecureToolEnforcer = violation grave.
- Aucun composant ne peut désactiver une barrière de sécurité.
- Les règles CORE sont immuables à l'exécution (constitution:* DENY).
- Modification policy > niveau USER requiert gouvernance hors-ligne.

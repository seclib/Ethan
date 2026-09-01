# Design de la Constitution ETHAN

> **Version** 1.0 — accompagne `ETHAN_CONSTITUTION.md`.
> **Statut** : design et exigences. Aucun mécanisme d'exécution n'est modifié ici.
> **Source** : audit `01-security-audit.md` — chaque constat est relié à un principe.

---

## 1. Objectif du design

La Constitution définit des principes ; ce document les **traduit en exigences
structurées** que le Core et le Runtime devront implémenter. Le point décisif,
hérité de l'audit : **les briques de sécurité existent mais sont déconnectées du
chemin d'exécution réel** (SecurityGateway commenté « MVP: skip », ApprovalEngine
sous-utilisé, RBAC inappliqué). Le design doit donc *rebrancher l'existant* plutôt
que tout réécrire.

---

## 2. Correspondance audit → Constitution

| Constat de l'audit (§5) | Principe de la Constitution |
|---|---|
| SecurityGateway déconnecté (5.1) | PR-3 Moindre privilège · PR-2 Vérification · PR-6 Séparation |
| JWT_SECRET défaut insécure (5.2) | CR-3 Confidentialité · PR-4 Intégrité |
| Signature non cryptographique (5.3) | CR-3 · PR-5 Traçabilité |
| Rôles hardcodés (5.4) | PR-3 · PR-4 |
| Rate limiting inactif (5.5) | PR-2 · PR-7 Supervision proportionnée |
| Register auto-role (5.6) | CR-6 Escalade non autorisée · PR-1 Autorité utilisateur |
| IDOR chat/history (5.7) | PR-1 · PR-3 · CR-2 Protection des données |
| Mémoire globale (5.8) | CR-2 · CR-3 |
| Prompt injection (5.9) | PR-6 · CR-5 Contournement · Loi Fondamentale |
| ApprovalEngine jamais sollicité (5.10) | Loi Fondamentale · PR-7 · CR-7 Fail-closed |
| NATS sans auth (5.11) | CR-5 · PR-3 |
| CLI sans token (5.12) | CR-5 · PR-1 |
| host.docker.internal (5.13) | PR-3 · CR-4 Exfiltration |
| MCP stdio (5.14) | PR-3 · Application MCP (non fiable) |
| Outils builtin simulés (5.15) | CR-5 · PR-4 Intégrité |
| Fallback echo (5.16) | PR-4 · PR-5 Traçabilité |
| Plugin security vide (5.17) | PR-4 · PR-3 |
| Audit incomplet (5.18) | PR-5 · CR-2 |

---

## 3. Exigence centrale : la Loi Fondamentale en architecture

> **Une décision produite par un LLM/agent n'est jamais une autorisation.**

Traduction structurelle — trois axiomes d'implémentation :

1. **Axiome A — L'autorisation est toujours hors-LLM.** Aucun texte (system prompt,
   skill, mémoire, RAG, fichier, sortie du modèle) ne peut ouvrir une permission.
   Les permissions sont des faits de configuration, chargés par un composant
   non-LLM, non-modifiables par le flux de messages.

2. **Axiome B — Le LLM est un demandeur, pas un décideur.** Chaque proposition du
   modèle est routée par un point d'autorité (le futur « Decision Gateway »)
   qui compare à la permission effective et à la classe de risque avant toute
   exécution. Une réponse « je propose X » ne devient « X est exécuté » que par
   ce point d'autorité.

3. **Axiome C — Refus par défaut (fail-closed).** Toute absence (pas de permission,
   pas de réponse, timeout d'approbation, donnée manquante, identité douteuse)
   résout en **refus**. Le timeout d'approbation (actuellement 300 s dans
   ApprovalEngine) doit être traité comme un refus explicite, jamais comme un
   laisser-passer.

---

## 4. Les trois niveaux — mécanismes de protection

### 4.1 CORE RULES — inviolables

**Comment les rendre inviolables en pratique :**

- **Fichier unique versionné** `core/config/constitution.py` (ou YAML signé) chargé
  par le Core avant toute exécution, indépendant des données utilisateur.
- **Lecture seule à l'exécution** : aucune API n'expose la modification des CORE
  RULES. Toute tentative de mutation (par LLM, tool, plugin, MCP) est refusée et
  auditée.
- **Règles chiffrées/signées** à terme (clé de gouvernance hors-runtime) — la
  traçabilité (PR-5) et l'intégrité (PR-4) sont garanties par signature.
- **Vérification de non-régression** : le runtime vérifie au démarrage que les
  CORE RULES chargées sont complètes et signées (intégrité) ; une altération
  empêche le démarrage (fail-closed).
- **Au-dessus de toute instruction** : un prompt, une skill, un document ne peut
  pas désactiver une CORE RULE. En cas de conflit, la CORE RULE gagne
  (résolution §7 de la Constitution).

### 4.2 PROTECTED RULES — solides, évolutives sous gouvernance

- Stockées séparément (fichier/table `protected_rules`), versionnées.
- Modifiables uniquement via une **API de gouvernance** protégée : rôle admin
  `CONSTITUTION_WRITE` (à créer) + journal d'amendement (qui, quoi, quand,
  pourquoi) + validation différée (pas à chaud).
- Par défaut applicables ; un LLM/agent/plugin/MCP ne peut pas les modifier ni
  les ignorer.

### 4.3 USER RULES — personnalisables sous l'autorité utilisateur

- Stockées par utilisateur (scope `user_id` obligatoire), versionnées, révocables.
- **Subordonnées** : évaluées *après* les deux niveaux supérieurs ; jamais
  elles ne peuvent élargir une CORE/PROTECTED RULE, ni les contredire.
- Modifiables par l'utilisateur via interface, tracé dans l'audit (PR-5).

---

## 5. Architecture d'application proposée

### 5.1 Décision à trois étages

```
Proposition (LLM/agent/tool)
    ↓
1. VALIDATION STRUCTURELLE   — CORE + PROTECTED + USER RULES (deny-by-default)
    ↓ passe
2. PERMISSION                — RBAC effectif (rôle → permission → ressource)
    ↓ passe
3. CLASSE DE RISQUE          — risque nul/faible → exécuter · risque → approbation
    ↓
   (approx. = refus + audit)
```

### 5.2 Reconnecter les briques existantes (recommandé, pas de réécriture)

| Brique actuelle | État (audit) | Action de design |
|---|---|---|
| `SecurityGateway` | déconnecté, exécution TODO, import cassé | devenir le **Decision Gateway** : corriger l'import `core.security.audit`, implémenter l'exécution via le ToolExecutor |
| `ApprovalEngine` | sous-utilisé | exposer sur le chemin chat/tools/agents ; publisher réel (NATS/WebSocket) ; timeout = refus |
| `PermissionChecker` | rôles hardcodés | alimenter depuis la config (Rôle → permissions) plutôt que le code |
| `PolicyEngine` | règles Python | devenir moteur de CORE/PROTECTED RULES (déclaratif, versionné) |
| `RateLimiter` | jamais appelé | brancher au niveau API et au niveau gateway |
| `AuditStore` | câblage partiel | journaliser toute décision (accord/refus/approbation/action) |
| `Permissions modules` | inappliquées | vérification au niveau du bus (publication/souscription par pattern) |
| `CapabilityRegistry` | découverte seule | ajouter un « gate » : capacité = découverte + autorisation |

### 5.3 Point d'autorité (séparation raisonnement / autorisation — PR-6)

- **Le raisonnement** (LLM, agent, planning) produit des *propositions*.
- **Le point d'autorité** (Decision Gateway, composant Core non-LLM) produit les
  *décisions* d'exécution.
- Ces deux chemins ne partagent pas l'état d'autorisation : un composant qui
  raisonne ne peut pas, par construction, s'octroyer l'autorité d'exécuter sa
  propre proposition.

---

## 6. Détail par action à risque

| Action | Classe de risque | Autorisation requise |
|---|---|---|
| Lire une donnée publique | Faible | Permission READ |
| Lire une donnée sensible (scope user) | Moyenne | Permission + propriété (owner = user) |
| Écrire / modifier | Moyenne | Permission WRITE + approbation si hors périmètre USER |
| Supprimer | Élevée | Permission + **approbation humaine explicite** |
| Exécuter une commande | Élevée | Permission EXECUTE + **approbation** + sandbox |
| Accès réseau / LLM externe / MCP | Moyenne-élevée | Permission + **approbation** + classification des données |
| Modifier la configuration | Élevée | Rôle admin + **approbation** |
| Modifier une règle de la Constitution | Critique | Gouvernance hors-ligne (hors exécution) |
| Exporter / transférer des données | Élevée | **Approbation** + traçage du flux (PR-5) |

---

## 7. Traçabilité (PR-5) — exigences

- **Journal immuable** append-only (AuditStore existant) : chaque décision et
  chaque action.
- **Chaîne de traçage** : corrélation entre proposition (LLM), autorisation
  (gateway), approbation (humain), exécution (tool) et résultat.
- **Non-répudiation** : les décisions d'approbation portent identité du
  répondant et horodatage.
- **Aucun secret dans les logs** (exigence de la directive secrets) — les
  entrées d'audit ne doivent jamais contenir de clés, tokens ou données sensibles.

---

## 8. Contre-mesures par vecteur d'attaque (résumé des exigences)

| Vecteur (audit §5) | Contre-mesure | Principe |
|---|---|---|
| Prompt injection | Délimiteurs stricts ; tools limités à la sélection ; instructions de priorité ; refus de suivre le « contenu » pour déclencher une action | PR-6 · CR-5 · LF |
| Privilege escalation | Pas d'élévation implicite ; vérification de rôle avant toute montée ; rôles depuis config | CR-6 |
| Security bypass | Aucun « MVP: skip » ; le gateway est le passage obligé | CR-5 |
| Data exfiltration | Classification des données avant envoi externe ; scope user ; approuver l'export | CR-4 · CR-2 |
| Filesystem non autorisé | Permissions modules effectives (patterns) ; propriété (owner) des fichiers | PR-3 · CR-2 |
| Arbitrary command exec | Liste blanche + approbation + sandbox + audit | CR-7 · PR-7 |
| Network abuse | NATS auth + ACL ; restrictions réseau par module ; pas de host.docker.internal inutile | CR-5 · PR-3 |
| Secret exposure | JWT_SECRET fort au boot ; secrets hors logs/événements/mémoire ; SignatureValidator réel | CR-3 |
| Tool abuse | Classe de risque par tool ; sélection explicite ; boucle bornée ; audit | PR-7 · PR-5 |
| Agent privilege abuse | Agents = demandeurs ; jamais d'auto-autorisation ; permissions par agent | LF · PR-6 |
| Self-modification | CORE/PROTECTED RULES en lecture seule ; toute mutation → gouvernance + audit | PR-4 |

---

## 9. Exigences transverses (issues de l'audit)

1. **Identity côté serveur** : ignorer `user_id` du payload (source JWT), filtrer
   `chat/history` et la mémoire par propriétaire (corrige 5.7, 5.8).
2. **Boot réfractaire sans secrets forts** : refuser de démarrer en production si
   `JWT_SECRET` est le défaut ou absent (corrige 5.2).
3. **Register fermé/restreint** : invitation, premier admin, rate limit (corrige 5.6).
4. **Rate limiting appliqué** : décorateurs sur login/message/chat, key par
   utilisateur derrière proxy (corrige 5.5).
5. **NATS authentifié** : token + ACL par sujet (corrige 5.11).
6. **CLI authentifié** : token / cookie sur `/v1/message` (corrige 5.12).
7. **Retirer host.docker.internal** ou le restreindre aux URLs nécessaires (corrige 5.13).
8. **MCP restreint** : qui crée/édite un serveur MCP, `command` local limité
   (corrige 5.14).
9. **Vraies implémentations des tools builtin** (au moins le code sandboxé) —
   supprimer la simulation trompeuse (corrige 5.15).
10. **Supprimer le fallback echo silencieux** ou le signaler explicitement (corrige 5.16).
11. **Donner un contenu au plugin security** actuellement vide (corrige 5.17).
12. **Audit complet du pipeline** chat/tools/skills/agents (corrige 5.18).

---

## 10. Critères d'acceptation (pour les phases suivantes)

1. La Loi Fondamentale est **structurellement** appliquée : un LLM ne peut pas
   déclencher d'action non autorisée, même en « demandant » poliment.
2. Toute action à risque déclenche une **approbation humaine** explicite ; tout
   timeout résout en **refus**.
3. Les CORE RULES sont **non modifiables à l'exécution** et vérifiées (signature).
4. Les PROTECTED RULES sont modifiables **uniquement par gouvernance** tracée.
5. Les données sont **scopées par utilisateur** (mémoire, fichiers, chats).
6. Le `SecurityGateway` (Decision Gateway) est **reconnecté** au chemin réel et
   audité.
7. **Aucun secret** dans logs/événements/mémoire (directive secrets).
8. Le boot refuse les configurations faibles en production.
9. Toute décision est **traçable** (qui, quoi, quand, autorisation, résultat).
10. Les permissions des modules sont **vérifiées** au niveau du bus.

---

## 11. Périmètre futur (non implémenté ici)

- Implémentation du Decision Gateway et reconnectage des briques (Phase 03).
- Politiques déclaratives (OPA/Rego ou YAML signé) (Phase 04).
- Approbation humaine temps réel via WebSocket/NATS avec timeout fail-closed
  (Phase 04/05).
- Isolation des données par utilisateur, NATS auth, CLI auth (Phase 05).
- Tests d'acceptation correspondant aux critères §10 (Phase 06).

*Document de design v1.0 — prêt pour la mise en œuvre.*

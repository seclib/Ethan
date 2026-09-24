# ADR-4001 — Capability Manager centralisé dans ETHAN Core

> Correspond à la demande « ADR-001 — Capability Manager » (série 4000, car
> ADR-001 est déjà attribué à [ADR-001-agent-system.md](/docs/adr/ADR-001-agent-system.md)).

**Statut** : Implémenté
**Date** : 2026-09-23
**Implémentation** : [`core/capability_manager/`](/core/capability_manager/) —
ESR liés : [ESR-001](/docs/engineering/esr/ESR-001-capability-model.md),
[ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md),
[ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md),
[ESR-004](/docs/engineering/esr/ESR-004-local-provisioning.md)

---

## Contexte

ETHAN intègre des composants optionnels (bases de vecteurs, services,
intégrations) dont le cycle de vie — détecter, installer, configurer,
tester, activer, désinstaller — doit être piloté par l'utilisateur depuis
la WebUI. Avant ce système, la page *Settings ▸ Vector Database* affichait
les backends dans un simple `<select>` sans état réel, et aucune interface
ne pouvait distinguer un composant supporté d'un composant installé.

## Problème

1. **Aucune source de vérité** : l'état « installé/actif » n'existait nulle
   part côté Core ; chaque interface devait le deviner.
2. **Logique d'installation dangereuse** : sans cadre, du `docker run` ou du
   `pip install` pourrait être écrit dans une interface, déclenché par des
   chaînes utilisateur non validées (injection).
3. **Homonymie** : `docs/security/05-capability-system.md` décrit déjà les
   *permissions* d'agents (capabilities RBAC). Il ne s'agit pas du même
   concept ; ce document porte sur le **cycle de vie des composants
   optionnels** déployés par ETHAN.

## Décision

Créer `core/capability_manager/`, module Core propriétaire :

| Fichier | Rôle |
|---|---|
| `types.py` | `CapabilitySpec` (déclaratif, développeur-défini), `CapabilityState` (12 états + transitions légales), `ConfigField`, `HealthCheck`, `Dependency`, plans |
| `manager.py` | Machine à états, validation de configuration, opérations asynchrones, audit, événements |
| `backends.py` | Exécution par backend (`docker`, `python_package`, `executable`, `builtin`) avec allowlists d'actions |
| `health.py` | Paliers de santé réels (tcp, endpoint, exec, builtin) |
| `builtin.py` | Catalogue des composants intégrés (`memory`, `qdrant`, `chromadb`) |

L'API (`interfaces/api/routers/component_lifecycle.py`) est une **passerelle
mince** ; la WebUI
(`interfaces/webui/src/components/features/settings/components/capabilities-section.tsx`)
est un **client passif**.

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Logique d'installation dans l'API FastAPI | Violerait la Première Loi (le CLI, le Desktop ne pourraient pas réutiliser) ; l'API est une interface remplaçable |
| Chaque interface gère ses composants | Duplication `docker run`/`pip install` en N endroits, incohérence d'états garantie |
| Outil externe (Portainer, Helm…) | Dépendance d'infrastructure supplémentaire, ne couvre pas `python_package`/`builtin`, ne produit pas d'états explicites |
| Stocker l'état côté frontend | Perdu à chaque reload, non partageable entre interfaces, non auditable |

## Conséquences positives

- Une seule implémentation du cycle de vie, réutilisable par WebUI, CLI et
  Desktop via la même API `/v1/components`.
- États explicites partagés (plus de « ✓ Installed » non fondé).
- Actions système figées dans la spec développeur : surface d'injection
  structurellement fermée.
- Catalogue déclaratif extensible (ajouter une spec = une fonction).

## Conséquences négatives

- Nouveau module Core à maintenir (≈ 1 700 lignes, 44 tests).
- Le déploiement Docker réel exige que l'API ait accès au binaire `docker`
  (voir [ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md) §
  contraintes) — condition d'environnement, pas gérée par ETHAN.
- Deux concepts partagent le mot « capability » (permissions agents vs
  composants) ; la doc doit toujours les distinguer.

## Sécurité

- **Spec développeur uniquement** : les actions système vivent dans la spec
  figée ; l'utilisateur ne fournit que des valeurs typées (voir
  [ESR-006](/docs/engineering/esr/ESR-006-security-model.md)).
- RBAC par verbe (READ / EXECUTE / SETTINGS / ADMIN) côté API.
- Audit + événements bus sans secrets sur chaque mutation.

## Compatibilité avec l'architecture existante

- Respecte la Première Loi (AGENTS.md) : capacité métier → Core.
- Complète [ADR-3001](/docs/architecture/adr/ADR-3001-unified-record-store.md)
  (l'état des composants persiste dans le CoreRecordStore) et prépare
  [ADR-3004](/docs/architecture/adr/ADR-3004-vector-store-record.md) (les
  backends vectoriels deviennent des composants gérés au lieu d'un select
  statique).
- Aucune rupture d'API existante ; nouveaux endpoints uniquement.
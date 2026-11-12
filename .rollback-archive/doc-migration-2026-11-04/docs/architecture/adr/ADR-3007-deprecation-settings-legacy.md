# ADR-3007 — Dépréciation du record `settings` hérité (`/v1/settings`)

**Statut** : Accepté — dépréciation actée ; **suppression différée** (RFC séparée requise)
**Date** : 2026-09-30
**État audité (2026-09-30)** : ✅ **Déprécié** — `GET`/`PUT /v1/settings` marqués
`deprecated=True` dans `interfaces/api/routers/v1.py` ; aucun consommateur
interne (audit exhaustif : seuls les tests RBAC et des commentaires citent la
route) ; écrans WebUI correspondants supprimés
(`docs/design/2026-09-30-webui-settings-honesty.md`).

**Contexte** : Le WebUI exposait un éditeur « General » de réglages key/value
projetés dans un record hérité, persisté par `core/state/webui_store.py`
(`CoreWebUIStore`). Après le lot « Settings honnêtes », **aucune interface** ne
lit ni n'écrit plus ce record : chaque réglage réel a une source de vérité
Core dédiée — catalogue providers (ADR-3002), `GET/PUT /v1/rag/config`,
`/models`, `/v1/agents`, `/v1/providers/catalog`… Le record ne subsiste que
comme **surface fantôme** : l'OpenAPI la présente comme un contrat actif alors
que rien ne la consomme. La Première Loi d'ETHAN interdit qu'une interface (ou
un record d'interface) redevienne un « second cerveau » de configuration.

**Décision** :

1. **Déprécier sans déplacer** : les deux routes restent en place et fonctionnelles,
   mais sont marquées `deprecated=True` (visibles comme telles dans `/openapi.json`).
2. **Aucun nouveau consommateur** : toute interface qui souhaite lire/écrire ces
   clés doit d'abord créer l'endpoint Core du domaine concerné (ou réutiliser
   l'existant) — jamais consommer ce record. Une nouvelle consommation exige un ADR.
3. **Suppression différée à une RFC dédiée**, car elle implique :
   - une rupture de contrat API (le snapshot `docs/api/openapi.v1.json`,
     ADR-3006, ne tolère que les ajouts — une suppression doit être
     explicitement actée + snapshot régénéré) ;
   - l'ajustement de `interfaces/api/tests/test_privileged_control_plane_rbac.py`
     (gates `SETTINGS` référencés) et de `docs/api/CONTRACTS-API.md` ;
   - le nettoyage du store hérité, qui appartient au chantier ADR-3001
     (store de records unifié).

**Conséquences** :

- OpenAPI : les deux opérations apparaissent `deprecated: true` — aucun test de
  contrat ne casse (le snapshot v1 n'est vérifié qu'en soustraction de routes).
- Comportement inchangé : `PUT` reste gaté `Permission.SETTINGS`, `GET` reste
  ouvert — la dépréciation est documentaire et opposable au prochain lot.
- La dette est tracée : la suppression n'est plus « hors périmètre », elle a un
  chemin d'implémentation explicite (RFC ≥ ADR-3006 §suppression + ADR-3001).

**Alternatives écartées** :

- **Suppression immédiate** : viole « aucune suppression de fonctionnalité sans
  RFC » et casse la compatibilité de contrat (ADR-3006). Un remplacement
  consommateur par consommateur n'a par ailleurs aucune cible (zéro consommateur).
- **Statut quo silencieux** : la fausse surface resterait invisible dans l'API —
  c'est exactement le défaut d'honnêteté corrigé côté WebUI, mais au niveau du Core.
- **Fusion `settings` → `ethan_config`** : deux records différents (clés
  utilisateur vs configuration Core) ; une fusion créerait une confusion de
  propriété sans bénéfice fonctionnel.

**Preuves** : `docs/design/2026-09-30-webui-settings-honesty.md` (table des
décisions, sections supprimées) ; grep `v1/settings` sur le dépôt
(`interfaces/api/tests/test_privileged_control_plane_rbac.py` + commentaires
WebUI uniquement) ; `interfaces/api/routers/v1.py` §SETTINGS.

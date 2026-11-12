# QUANTAR — Audit et qualification du Provider Gateway HROT (Phase 47)

Date : 2026-11-04
Statut : audit terminé, composant implémenté mais non intégré et non runtime validé

## 1. État documenté

Les rapports Quantar des phases 42, 43 et 44 existent dans Obsidian/_meta. Les documents de sécurité préciseront les principes d’isolation et la gouvernance HROT. Aucun lien entre le gateway et Quantar runtime n’est établi.

## 2. États recherchés

- `ProviderGateway` n’est référencé par aucun module Python opérationnel.
- `QuantarTaskService` n’utilise pas le provider gateway.
- `examples/quantar/quantar_task_runner.py` n’importe pas le gateway.
- Quantar config expose le nom de fournisseur sans autorisation contextuelle.

## 3. Composants existants susceptibles d’être réutilisés

- `core/security/hrot_provider_gateway.py`: contrat provider gateway et SecretProvider in-memory ;
- `core/hrot/durable.py`: autorisations HROT persistées PostgreSQL/JSONL ;
- `core/human_root`: Human Root of Trust pour demandes humaines ;
- `core/approval`: moteur d’approbations ;
- `core/auth`: identité et permissions.

Ces composants sont présents, mais ils ne sont pas connectés entre eux.

## 4. Écarts HROT

- Le gateway possède son propre état et ses propres autorisations, distinct du moteur HROT durable.
- Une authorization peut être créée par appel à `issue_authorization` sans passage par `HumanRoot.request_approval`.
- Le principal/approver equality check n’est pas une autorisation humaine durable.
- Pas de permission application/fournisseur persistante.
- Pas de gateway externe réelle ni de canal authentifié.
- Aucun adapter TradingAgents quantar.

## 5. Tests et résultats

- `tests/core/test_hrot_provider_gateway.py` : 14 tests passés.
- Les tests utilisent des fournisseurs simulés et ne vérifient pas l’isolement réel.
- Pas de tests de conteneur, de réseau ou de portefeuille.

## 6. Preuves de non-exposition des secrets

- le secret reste stocké dans `SecretProvider._secrets` ;
- le runner n’a pas d’accès à la clé ;
- le conteneur continue avec `network: none` par défaut ;
- aucun credential réel n’a été utilisé.

Ces preuves concernent seulement le composant in-process; la frontière runtime n’est pas qualifiée.

## 7. Risques et blocages

- le gateway n’est pas intégré à Quantar ;
- aucune persistence de l’autorisation pour le runner ;
- risque de divergence entre `DECLARED`, `VERIFIED`, `AVAILABLE` et `AUTHORIZED` ;
- aucune protection réseau réelle autour du gateway ;
- pas de preuve end-to-end.

## 8. Décisions requises

- choisir le mécanisme d’approbation HROT durable ;
- définir l’authentification du canal container → gateway ;
- mettre en place un gateway runtime ;
- soit adapter TradingAgents à un client contrôlé ;
- valider sans fuite de secret.

## 9. Statut

- Implémentation : IMPLEMENTED (in-process)
- Statut unit tests : UNIT_TESTED
- Securité runtime : NOT_VERIFIED
- Statut global Quantar : PARTIALLY_VALIDATED.

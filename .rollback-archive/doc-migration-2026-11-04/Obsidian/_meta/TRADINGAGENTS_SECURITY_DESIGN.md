# TRADINGAGENTS_SECURITY_DESIGN.md

Date : 2026-11-03
Statut : PROPOSED

## 1. Frontières de confiance

- TradingAgents reste un moteur autonome.
- ETHAN Core est le seul point de contrôle et de supervision.
- WebUI et Chat n'accèdent à TradingAgents que par API contrôlée.
- Aucun agent ne possède de pouvoir d'approbation.
- HROT : autorité humaine pour opérations sensibles.

## 2. Isolation

- Process wrapping avec cancellation et timeouts.
- Pas d'exécution arbitraire d'outils.
- Pas d'accès brut aux chemins internes.
- Pas d'accès au Docker.
- Pas de configuration sensible expose via API.

## 3. Secrets

- `.env` TradingAgents reste hors contrôle ETHAN par défaut.
- Les clés ne sont jamais aspirées dans Obsidian.
- Les codes source de données doivent être masqués dans les copies.
- Le contrôleur valide et pas transmission sensible.

## 4. Journalisation

- Événements d'initialisation, d'échec et résultats.
- Pas de dump entier des rapports si sensible.
- Aucun secret dans `MEMORY_EVENT_LOG`.
- Trace d'auth et permissions recommandée.

## 5. Publication

- Ne pas publier Obsidian ni ses documents.
- Exporter par allowlist.
- Scanner l'export pour secrets.
- Versionner le manifeste.

## 6. Risques

- Fuite de credentials ou de données.
- Results financiers mistakenly taken as advice.
- Scraping pénalisant les fournisseurs.
- exécution non contrôlée.
- Legal reporting / compliance.


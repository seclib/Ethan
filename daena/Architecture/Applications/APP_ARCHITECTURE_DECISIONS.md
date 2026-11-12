# ETHAN — Décisions architecturales ODIN / Frames / Quantar

Date : 2026-11-04
Statut : ÉTUDE DÉCISIONNELLE
Chemin demandé : `Obsidian/Architecture/Applications/APP_ARCHITECTURE_DECISIONS.md`
Sources : `APP_TECHNICAL_CARTOGRAPHY.md`, `APP_INTEGRATION_MAP.md`, `ARCHITECTURE_HYBRIDE_PYTHON_RUST.md`, `ADR-H001-hybrid-boundaries.md`

Convention de preuve :
- **FV** = fait vérifié ;
- **DA** = déduction architecturale ;
- **NI** = non identifié ;
- Statut : `CONFIRMED`, `PROPOSED`, `EXPERIMENTAL`, `BLOCKED`.

---

## 1. Principes conservés

1. Python reste la source de vérité pour HROT et la logique métier ETHAN.
2. Rust reste une capacité spécialisée consommée par façade explicite.
3. ODIN, Frames et Quantar conservent leur indépendance technologique.
4. Aucun service applicatif ne démarre automatiquement sans demande explicite lorsque ce principe est déjà implémenté.
5. Les permissions `READ` et `PLUGINS` restent la base lisible pour le contrôle applicatif, sauf preuve de besoin HROT.

---

## 2. ODIN

### 2.1 Situation actuelle
- Frontend et proxies Node.js/Vite.
- Service Docker local avec contrôleur Docker spécifique.
- Intégration Core via `core/plugins/odin.py`, manifeste et routes API.

### 2.2 Problèmes constatés
- Double existence potentielle : `OdinService` spécifique versus `ComposeService` générique.
- Chemin canonique dépend de `ETHAN_ODIN_REPO_DIR` ou de `examples/odin`.
- Secret stocké dans un `.env` bind-mounté.
- Contrôleur réseau optionnel (`ETHAN_ODIN_CONTROLLER_URL`) augmente la surface réseau.

### 2.3 Options examinées
1. Conserver le contrôleur Odin spécifique.
2. Refondre Odin sur `ComposeService` générique.
3. Ajouter un contrôleur central universel.
4. Mutualiser uniquement les helpers de redaction/confinement.

### 2.4 Décision
- Conserver le contrôleur Odin spécifique comme implémentation actuelle.
- Mutualiser seulement des utilitaires déjà éprouvés si une déduplication est demandée, sans refondre Odin.
- Ne pas introduire de contrôleur Docker universel.

### 2.5 Justification
Le contrôleur Odin embarque des spécificités réelles : détection de port, chemin d'environnement, redaction et délguation optionnelle. Passer à `ComposeService` risquerait de casser des propriétés déjà implémentées sans bénéfice démontré.

### 2.6 Risques
- Duplication de code avec `ComposeService`.
- Maintenance de deux chemins similaires.
- Détail des permissions HROT non prouvé pour Odin.

### 2.7 Tests nécessaires
- Tests unitaires du contrôleur Odin et de la redaction.
- Tests de confinement sur chemin hors allowlist.
- Tests de routes avec et sans `Permission.PLUGINS`.
- Tests d'indisponibilité du contrôleur réseau.

### 2.8 Statut
CONFIRMED

---

## 3. Frames / base HyperFrames

### 3.1 Situation actuelle
- Monorepo TypeScript/JavaScript sous Bun.
- Service permanent studio Vite port 5190.
- `FrameService` extends `ComposeService`.
- Dépendance Docker à l'image `frame-frame`.
- Intégration Core via manifeste et routes API.

### 3.2 Problèmes constatés
- Taille et complexité du monorepo.
- Dépendance à une image Docker déjà présente ; Compose ne reconstruit pas.
- Port fixe 5190.
- Aucune preuve d'HROT applicatif.
- Couverture exacte non identifiée.

### 3.3 Options examinées
1. Conserver l'architecture actuelle et le mécanisme ComposeService.
2. Mutualiser tous les services applicatifs dans un portail universel.
3. Remplacer la base HyperFrames.
4. Déporter une partie du rendu dans Rust.

### 3.4 Décision
- Conserver l'architecture actuelle.
- Conserver `ComposeService` comme couche générique pour Frames.
- Ne pas centraliser les contrôleurs.
- Ne pas migrer vers Rust sans expérimentation.

### 3.5 Justification
Frames présente une stack Bun/TypeScript cohérente avec son code amont. La base Core via Compose est simple, traçable et isolée. Aucun goulot démontré ne justifie une migration ou une refonte.

### 3.6 Risques
- Image Docker manquante en production.
- Monorepo coûteux à maintenir.
- Observabilité limitée au Compose et HTTP.
- Éventuelle divergence avec l'amont HyperFrames.

### 3.7 Tests nécessaires
- Smoke test d'installation Docker.
- Test de confinement.
- Test de health avec image manquante.
- Test de permissions READ/PLUGINS.

### 3.8 Statut
CONFIRMED

---

## 4. Quantar

### 4.1 Situation actuelle
- Application Python TradingAgents.
- Mode in-process possible et mode Docker one-shot.
- Service Compose optionnel plus moteur `QuantarTaskService`.
- Pont HROT durable avant provider.

### 4.2 Problèmes constatés
- Deux couches distinctes : `QuantarService` Compose et `QuantarTaskService`.
- In-process dépend de TradingAgents installé dans l'environnement d'exécution.
- Persistance locale à base de workspace et de `cwd`.
- Réconciliation obligatoire après redémarrage.
- Réseau et volumes Docker à auditer fichier par fichier.

### 4.3 Options examinées
1. Conserver le moteur Python et la réconciliation.
2. Migrer Quantar vers Rust.
3. Remplacer la stratégie de persistance.
4. Imposer le mode Docker exclusivement.
5. Intégrer HROT au runtime unique.

### 4.4 Décision
- Conserver la logique métier Python.
- Conserver l'architecture hybride in-process/Docker.
- Ne pas migrer Quantar vers Rust sans expérimentation mesurée.
- Conserver la réconciliation post-redémarrage.
- Conserver le pont HROT obligatoire avant provider.

### 4.5 Justification
Quantar dépend directement de TradingAgents et des providers LLM. Python est le langage des dépendances amont. L'architecture actuelle garde la traçabilité des résultats et la possibilité d'in-process. Rust n'apporterait pas de bénéfice clair sur la simplicité et les dépendances métier.

### 4.6 Risques
- Environnement Python sans TradingAgents.
- Risque d'écriture au mauvais workspace selon le `cwd`.
- Échec de réconciliation après crash.
- Dépendance externe LLM et clés.

### 4.7 Tests nécessaires
- Test en environnement TradingAgents absent.
- Test Docker one-shot complet.
- Test de réconciliation post-redémarrage.
- Test d'approbation HROT refusée.
- Test d'échange d'autorisation entre tâches.

### 4.8 Statut
CONFIRMED

---

## 5. Décisions transverses

### 5.1 Capability Manager et Rust
- Décision : conserver Python comme autorité du Capability Manager.
- Rust est utilisé pour la validation de contrat JSON et la détection d'environnements isolés.
- Statut : CONFIRMED.

### 5.2 Rust Health
- Décision : conserver une façade Python et une route API protégée.
- Le binaire Rust est optionnel avec gestion explicite des erreurs.
- Statut : CONFIRMED au niveau source, EXPERIMENTAL au niveau validation Docker complète.

### 5.3 Contrôleurs applicatifs
- Décision : ne pas imposer un contrôleur Docker universel.
- Odin reste spécifique.
- Frames et runtime autonome Quantar restent sur ComposeService.
- Statut : CONFIRMED.

### 5.4 HROT
- Décision : ne pas ajouter de dépendance HROT à Odin ou Frames sans preuve de besoin.
- Le pont HROT est conservé pour le provider LLM de Quantar.
- Statut : CONFIRMED.

### 5.5 Mutualisation
- Décision : mutualiser uniquement des utilitaires testés et simples (redaction, confinement) après démonstration.
- Ne pas créer de catalogue central obligatoire.
- Statut : PROPOSED pour la mutualisation future.

---

## 6. Tests nécessaires selon les décisions
- Tests unitaires des services applicatifs et contrôleurs.
- Tests de sécurité sur confinement, redaction, permissions et HROT.
- Smoke tests Docker pour ODIN et Frames.
- Test one-shot réel pour Quantar avec réconciliation.
- Validation navigateur WebUI sans simulation.
- Tests de port conflits et d'indisponibilité.

---

## 7. Décision de ne pas changer

Pour les trois applications, le verdict actuel est :

- ODIN : `CONFIRMED`, aucune migration imposée.
- Frames : `CONFIRMED`, aucune migration imposée.
- Quantar : `CONFIRMED`, aucune migration imposée.

Les éventuels changements futurs devront être justifiés par des mesures, des tests ou une contrainte opérationnelle réelle, et ne doivent pas être lancés uniquement parce qu'une autre stack paraît plus simple.

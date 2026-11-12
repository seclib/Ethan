# ESR — Engineering Specifications & Requirements

Spécifications techniques du **système de gestion des capacités**
(composants optionnels : détection, installation, configuration, santé,
désinstallation). Chaque ESR explique **COMMENT** est implémentée une
décision justifiée dans un ADR de la série 4000
([docs/architecture/adr/](/docs/architecture/adr/)).

> ⚠️ Distinction : les *capabilities* de permissions agents sont
> documentées dans `docs/security/05-capability-system.md` (autre concept).

| ESR | Sujet | Décision parente | Statut |
|---|---|---|---|
| [ESR-001](/docs/engineering/esr/ESR-001-capability-model.md) | Capability Model (spec, types, 12 états, transitions, config, health) | ADR-4001 | Implémenté |
| [ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md) | Installation Engine (pipeline, opérations asynchrones, rollback, erreurs) | ADR-4002 | Implémenté |
| [ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md) | Docker Provisioning (image/container/volume/network, limites) | ADR-4001, ADR-4002 | Implémenté (accès docker = déploiement) |
| [ESR-004](/docs/engineering/esr/ESR-004-local-provisioning.md) | Local Provisioning (python_package, executable, builtin ; Node/modèles **non implémentés**) | ADR-4002 | Partiel |
| [ESR-005](/docs/engineering/esr/ESR-005-webui-capability-manager.md) | WebUI Capability Manager (catalogue, dialogs, progression) | ADR-4003, ADR-4004 | Implémenté |
| [ESR-006](/docs/engineering/esr/ESR-006-security-model.md) | Security Model (RBAC, audit, validation, injection, destructif) | ADR-4001, ADR-4003 | Implémenté |
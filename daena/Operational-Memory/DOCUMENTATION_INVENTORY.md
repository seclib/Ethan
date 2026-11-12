# Inventaire documentaire ETHAN — Phase A / Phase B (réorganisation)

Date : 2026-11-04  
Auteur : Codex (agent) — inventaire proposé, non validé  
Statut : **PROPOSED — en attente d’approbation humaine avant toute migration**  
Branche Git : `refactor/ethan-rebuild-p0`  
Commit de base observé : `9e57d1c0`  

Principe appliqué : `docs/` = documentation officielle destinée aux utilisateurs ; `Obsidian/` = documentation interne, technique, architecturale, ingénierie et mémoire opérationnelle.

## 1. Tableau principal

| ID | Chemin actuel | Titre | Catégorie | Destination | Action | Justification | Risque |
|---|---|---|---|---|---|---|---|
| DOC-0001 | `Obsidian/AGENTS.md` | AGENTS.md — Règles spécifiques à Obsidian/ | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0002 | `Obsidian/Architecture/ADR/ADR-001-agent-system.md` | ADR-001: Système d'Agents | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0003 | `Obsidian/Architecture/ADR/ADR-1003-implementation.md` | ADR-1003 — Single Entry Intent Model — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0004 | `Obsidian/Architecture/ADR/ADR-1004-implementation.md` | ADR-1004 — Cognitive Loop Architecture — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0005 | `Obsidian/Architecture/ADR/ADR-1005-implementation.md` | ADR-1005 — Core Technology Independence — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0006 | `Obsidian/Architecture/ADR/ADR-1006-implementation.md` | ADR-1006 — Capability Composition Pattern — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0007 | `Obsidian/Architecture/ADR/ADR-1008-implementation.md` | ADR-1008 — Plugin Discovery & Loading — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0008 | `Obsidian/Architecture/ADR/ADR-1009-implementation.md` | ADR-1009 — Safety & Permission Model — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0009 | `Obsidian/Architecture/ADR/ADR-1010-rag-strategies.md` | ADR-1010 — Sélection de la stratégie de recherche RAG | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0010 | `Obsidian/Architecture/ADR/ADR-1011-rag-strategy.md` | ADR-1011 — Stratégie RAG Knowledge | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0011 | `Obsidian/Architecture/ADR/ADR-1012-document-vector-persistence.md` | ADR-1012 — Persistance documentaire et vectorielle | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0012 | `Obsidian/Architecture/ADR/ADR-1013-frame-fork.md` | ADR-1013 — Fork Frame à partir d'HyperFrames | ADR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0013 | `Obsidian/Architecture/ADR/ADR-1013-knowledge-task-lifecycle.md` | ADR-1013 — Cycle de vie des tâches Knowledge | ADR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0014 | `Obsidian/Architecture/ADR/ADR-1014-frame-service-integration.md` | ADR-1014 — Service Frame dans ETHAN (modèle ODIN) | ADR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0015 | `Obsidian/Architecture/ADR/ADR-1014-retrieval-permission-scope.md` | ADR-1014 — Recherche et permissions | ADR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0016 | `Obsidian/Architecture/ADR/ADR-1015-embedding-model-compatibility.md` | ADR-1015 — Modèle d'embeddings et compatibilité index | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0017 | `Obsidian/Architecture/ADR/ADR-1016-production-vector-backend.md` | ADR-1016 — Configuration vectorielle production | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0018 | `Obsidian/Architecture/ADR/ADR-2001-implementation.md` | ADR-2001 — Memory is a Cognitive Layer — Implementation Report | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0019 | `Obsidian/Architecture/ADR/ADR-3001-unified-record-store.md` | ADR-3001 — Unified Record Store | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0020 | `Obsidian/Architecture/ADR/ADR-3002-providers-source-of-truth.md` | ADR-3002 — Providers : ProviderManager = seule source de vérité | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0021 | `Obsidian/Architecture/ADR/ADR-3003-projects-domain.md` | ADR-3003 — Domaine Projects | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0022 | `Obsidian/Architecture/ADR/ADR-3004-vector-store-record.md` | ADR-3004 — Back-end de vecteurs unique | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0023 | `Obsidian/Architecture/ADR/ADR-3005-folders-vs-domains.md` | ADR-3005 — Folders (arborescence) vs Domains (étiquettes transverses) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0024 | `Obsidian/Architecture/ADR/ADR-3006-api-contracts.md` | ADR-3006 — Contrats API versionnés (OpenAPI + tests de contrat) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0025 | `Obsidian/Architecture/ADR/ADR-3007-deprecation-settings-legacy.md` | ADR-3007 — Dépréciation du record settings hérité (/v1/settings) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0026 | `Obsidian/Architecture/ADR/ADR-4001-capability-manager.md` | ADR-4001 — Capability Manager centralisé dans ETHAN Core | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0027 | `Obsidian/Architecture/ADR/ADR-4002-install-on-demand.md` | ADR-4002 — Installation à la demande (supported ≠ installed ≠ running ≠ ready) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0028 | `Obsidian/Architecture/ADR/ADR-4003-data-lifecycle.md` | ADR-4003 — Cycle de vie des données : uninstall ≠ delete data | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0029 | `Obsidian/Architecture/ADR/ADR-4004-core-source-of-truth.md` | ADR-4004 — Le Core, source de vérité de l'état des composants | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0030 | `Obsidian/Architecture/ADR/ADR-4005-extension-trust-model.md` | ADR-4005 — Modèle de confiance des extensions (Skills, Plugins, MCP, Integrations) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0031 | `Obsidian/Architecture/ADR/ADR-4006-rebuild-target-architecture.md` | ADR-4006 — Architecture cible rebuild ETHAN (hybride Rust + Python, socle parallèle) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0032 | `Obsidian/Architecture/ADR/ADR-4007-open-webui-fork-license-gate.md` | ADR-4007 — Fork Open WebUI comme frontend : gate de licence et de marque | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0033 | `Obsidian/Architecture/ADR/ADR-4008-rust-event-store-shadow-mode.md` | ADR-4008 — Shadow mode pour migration Rust de l'Event Store | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0034 | `Obsidian/Architecture/ADR/ADR-EM-001-engineering-memory-architecture.md` | ADR-EM-001 — Architecture Engineering Memory pour ETHAN | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0035 | `Obsidian/Architecture/ADR/ADR-MEM-014-HROT-PRODUCTION-CRYPTO.md` | ADR-MEM-014 Phase 10 — HROT Cryptography | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0036 | `Obsidian/Architecture/ADR/ADR-MEM-014-PHASE-41-APPLICATION-ECOSYSTEM.md` | ADR — ETHAN Application Catalog (seclib) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0037 | `Obsidian/Architecture/ADR/ADR-MEM-014-PHASE-8-PERSISTENCE.md` | ADR-MEM-014 Phase 8 — Persistance durable SQLite | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0038 | `Obsidian/Architecture/ADR/ADR-MEM-014-application-integration-governance-and-capabilities.md` | ADR-MEM-014 — Contrat d'interopérabilité, gouvernance et capacités des applications indépendantes | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0039 | `Obsidian/Architecture/ADR/README.md` | ADR — Architecture Decision Records (WebUI Platform) | ADR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0040 | `Obsidian/Architecture/ASR/ASR-EM-001-engineering-memory-security.md` | ASR-EM-001 — Exigences de sécurité de la mémoire technique | ASR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0041 | `Obsidian/Architecture/ESR/ESR-001-capability-model.md` | ESR-001 — Capability Model | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0042 | `Obsidian/Architecture/ESR/ESR-002-installation-engine.md` | ESR-002 — Installation Engine | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0043 | `Obsidian/Architecture/ESR/ESR-003-docker-provisioning.md` | ESR-003 — Docker Provisioning | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0044 | `Obsidian/Architecture/ESR/ESR-004-local-provisioning.md` | ESR-004 — Local Provisioning (Python, exécutables, intégrés) | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0045 | `Obsidian/Architecture/ESR/ESR-005-webui-capability-manager.md` | ESR-005 — WebUI Capability Manager | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0046 | `Obsidian/Architecture/ESR/ESR-006-security-model.md` | ESR-006 — Security Model | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0047 | `Obsidian/Architecture/ESR/ESR-007-knowledge-collections.md` | ESR-007 — Knowledge Collections | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0048 | `Obsidian/Architecture/ESR/ESR-008-knowledge-sources.md` | ESR-008 — Knowledge Sources | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0049 | `Obsidian/Architecture/ESR/ESR-010-knowledge-index.md` | ESR-010 — Knowledge Index | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0050 | `Obsidian/Architecture/ESR/ESR-011-knowledge-search.md` | ESR-011 — Knowledge Search | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0051 | `Obsidian/Architecture/ESR/ESR-012-knowledge-rag-permissions.md` | ESR-012 — Knowledge RAG Permissions | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0052 | `Obsidian/Architecture/ESR/ESR-013-knowledge-tasks.md` | ESR-013 — Knowledge Tasks | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0053 | `Obsidian/Architecture/ESR/ESR-014-frame-fork.md` | ESR-014 — Préparation du fork Frame | ESR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0054 | `Obsidian/Architecture/ESR/ESR-014-knowledge-observability.md` | ESR-014 — Knowledge Observability | ESR | Obsidian/ | Fusionner après validation | Mémoire opérationnelle (autre) | Élevé — collision de numérotation |
| DOC-0055 | `Obsidian/Architecture/ESR/ESR-015-frame-service.md` | ESR-015 — Service Frame piloté par ETHAN | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0056 | `Obsidian/Architecture/ESR/ESR-EM-001-engineering-memory.md` | ESR-EM-001 — Exigences système de la mémoire technique | ESR | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0057 | `Obsidian/Architecture/ESR/README.md` | ESR — Engineering Specifications & Requirements | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0058 | `Obsidian/Architecture/System-Reviews/01-security-audit.md` | ETHAN — Phase 01 · Audit Sécurité & Gouvernance | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0059 | `Obsidian/Architecture/System-Reviews/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | Migration — Backend Open-WebUI → ETHAN API | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0060 | `Obsidian/Architecture/System-Reviews/RUST-MIGRATION-AUDIT.md` | ETHAN — Audit de fiabilité et préparation d'une migration Rust progressive | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0061 | `Obsidian/Architecture/System-Reviews/current.md` | Architecture Actuelle — Ethan | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0062 | `Obsidian/Architecture/System-Reviews/decisions.md` | Décisions Architecturale Critiques — ETHAN Core Daemon | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0063 | `Obsidian/Architecture/System-Reviews/local-knowledge-storage-audit.md` | ETHAN — Local Knowledge Storage Audit | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0064 | `Obsidian/Architecture/System-Reviews/migration-report.md` | ETHAN — Rapport de Migration : core/providers/ → core/llm/providers/ | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0065 | `Obsidian/Architecture/System-Reviews/proposed.md` | Architecture Proposée — Jarvis OS | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0066 | `Obsidian/Architecture/System-Reviews/webui-core-audit.md` | ETHAN — Audit WebUI / Core Boundary | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0067 | `Obsidian/Architecture/System/02-constitution-design.md` | Design de la Constitution ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0068 | `Obsidian/Architecture/System/03-policy-hierarchy.md` | Hiérarchie des Politiques ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0069 | `Obsidian/Architecture/System/04-policy-engine.md` | Policy Engine — Phase 04 | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0070 | `Obsidian/Architecture/System/05-capability-system.md` | Capability & Permission System — Phase 05 | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0071 | `Obsidian/Architecture/System/06-data-protection.md` | Data Protection & Anti-Exfiltration — Phase 06 | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0072 | `Obsidian/Architecture/System/07-ecosystem-integration.md` | 07 — Intégration Écosystème (Phase 07) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0073 | `Obsidian/Architecture/System/08-control-plane-hardening.md` | 08 — Durcissement du plan de contrôle (RBAC) & politique d'egress | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0074 | `Obsidian/Architecture/System/09-extension-hardening.md` | 09 — Durcissement des extensions (skills, plugins, outils) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0075 | `Obsidian/Architecture/System/10-secret-hygiene.md` | 10 — Hygiène des secrets dans les configurations persistées | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0076 | `Obsidian/Architecture/System/11-runtime-isolation.md` | 11 — Runtime Isolation & Durcissements Red Team | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0077 | `Obsidian/Architecture/System/ARCHITECTURE-CIBLE.md` | ETHAN — Architecture Cible Officielle | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0078 | `Obsidian/Architecture/System/C4-Event-Flow.md` | C4 Architecture — Event Flow | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0079 | `Obsidian/Architecture/System/C4-Level1-System-Context.md` | C4 Architecture — Level 1: System Context | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0080 | `Obsidian/Architecture/System/C4-Level2-Containers.md` | C4 Architecture — Level 2: Container Diagram | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0081 | `Obsidian/Architecture/System/C4-Level3-Components-Kernel.md` | C4 Architecture — Level 3: Component Diagram — Cognitive Kernel | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0082 | `Obsidian/Architecture/System/C4-Level4-Code-View.md` | C4 Architecture — Level 4: Code-Level View | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0083 | `Obsidian/Architecture/System/C4-README.md` | C4 Architecture Documentation — ETHAN Cognitive OS | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0084 | `Obsidian/Architecture/System/ETHAN_KNOWLEDGE_SKILLS_TOOLS_MCP.md` | ETHAN — Knowledge, Skills, Tools/MCP, Memory : Audit Open-WebUI vs ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0085 | `Obsidian/Architecture/System/ETHAN_REBUILD_P1_REQUIREMENTS_MATRIX.md` | ETHAN — Matrice exigences → implémentation → tests → preuves (P1) | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0086 | `Obsidian/Architecture/System/ETHAN_REBUILD_P1_TARGET_ARCHITECTURE.md` | ETHAN — Architecture cible P1 (hybride Rust + Python, socle Open WebUI étudié) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0087 | `Obsidian/Architecture/System/ETHAN_RESPONSE_RENDERER.md` | ETHAN Response Renderer — architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0088 | `Obsidian/Architecture/System/ETHAN_WEBUI_TARGET_ARCHITECTURE.md` | ETHAN WebUI — Architecture cible | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0089 | `Obsidian/Architecture/System/OPENWEBUI_ETHAN_MAPPING.md` | Open-WebUI → ETHAN — Mapping des concepts | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0090 | `Obsidian/Architecture/System/README_ARCHITECTURE_REFERENCE.md` | ETHAN — Architecture Reference | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0091 | `Obsidian/Architecture/System/agents.md` | Agentic Logic Primitive | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0092 | `Obsidian/Architecture/System/api-core-boundary-refactoring.md` | ETHAN — Refactoring Frontière API/Core | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0093 | `Obsidian/Architecture/System/channels.md` | Channels Architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0094 | `Obsidian/Architecture/System/communication-graph.md` | Graphe de Communication ETHAN — Analyse SRE | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0095 | `Obsidian/Architecture/System/consolidation-plan.md` | ETHAN — Plan de Consolidation Architecture | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0096 | `Obsidian/Architecture/System/critical-analysis.md` | Analyse Critique de l'Architecture ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0097 | `Obsidian/Architecture/System/design-principles.md` | Design Principles | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0098 | `Obsidian/Architecture/System/document-pipeline.md` | ASR — Knowledge Document Pipeline (hypothèse) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0099 | `Obsidian/Architecture/System/duplicate-detection.md` | Duplicate Detection — Architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0100 | `Obsidian/Architecture/System/engine.md` | Inference Engine Primitive | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0101 | `Obsidian/Architecture/System/file-folder-consolidation.md` | File/Folder Consolidation — Architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0102 | `Obsidian/Architecture/System/intelligence.md` | Intelligence Primitive | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0103 | `Obsidian/Architecture/System/learning.md` | Learning & Traces | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0104 | `Obsidian/Architecture/System/llm-unification-plan.md` | ETHAN — Plan d'Unification LLM | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0105 | `Obsidian/Architecture/System/local-knowledge-api-contract.md` | ETHAN — Local Knowledge API Contract | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0106 | `Obsidian/Architecture/System/local-knowledge-domain.md` | ETHAN — Local Knowledge Domain Contract | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0107 | `Obsidian/Architecture/System/memory.md` | Memory Primitive | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0108 | `Obsidian/Architecture/System/osiris-port-management.md` | Osiris-Lab v2: Port Management & Allocation System | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0109 | `Obsidian/Architecture/System/overview.md` | Architecture Overview | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0110 | `Obsidian/Architecture/System/query-flow.md` | Query Flow | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0111 | `Obsidian/Architecture/System/security.md` | Security Architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0112 | `Obsidian/Architecture/System/skills.md` | Skills Architecture | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0113 | `Obsidian/Architecture/System/terminal-webui.md` | Terminal WebUI — PTY distant servi par ETHAN Core | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0114 | `Obsidian/Architecture/System/unified-ai-providers-review.md` | ETHAN — Unified AI Providers — Architecture Decision | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0115 | `Obsidian/Architecture/System/webui-platform-architecture-assessment.md` | ETHAN — WebUI Platform Architecture Assessment | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0116 | `Obsidian/Architecture/System/webui-platform-review.md` | ETHAN WebUI — Architecture Review | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0117 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781261826788.md` | Tu es responsable du Plugin Engine.  Tu n'as pas le droit de modifier autre chos | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0118 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` | Tu es un Distinguished Software Architect (niveau CTO Palantir / Google).  Tu es | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0119 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781265677020.md` | Tu es chargé de concevoir Osiris-Lab v2.  Ignore les implémentations existantes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0120 | `Obsidian/Archives/Conversations/cline/2026-06-13/1781324525374.md` | Tu es l’architecte logiciel principal du projet OSIRIS-Lab v2.  Tu dois considér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0121 | `Obsidian/Archives/Conversations/cline/2026-06-13/1781326479958.md` | fais moi un docker-compose.yml | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0122 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781438417220.md` | Tu es l’architecte logiciel principal du projet OSIRIS-Lab v2.  Tu dois considér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0123 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781440243749.md` | Quand tu modifies le projet OSIRIS :  - Tu dois identifier le module concerné da | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0124 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781445007397.md` | Tu fais partie de l'équipe d'ingénierie d'Osiris-Lab v2.  Les fichiers contenus | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0125 | `Obsidian/Archives/Conversations/cline/2026-06-15/1781506386208.md` | # OSIRIS META ORCHESTRATION ENGINEER  ## 1. MISSION  Concevoir la couche supérie | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0126 | `Obsidian/Archives/Conversations/cline/2026-06-16/1781448124733.md` | Tu es le Chief Technology Officer (CTO) du projet Osiris-Lab v2.  Tu es responsa | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0127 | `Obsidian/Archives/Conversations/cline/2026-06-16/1781584795579.md` | Dockerfile:14  --------------------    12 \|     # Build the GEOINT worker binary | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0128 | `Obsidian/Archives/Conversations/cline/2026-06-17/1781619688061.md` | You are an Autonomous DevOps Engineer inside a system called "Osiris Self-Healin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0129 | `Obsidian/Archives/Conversations/cline/2026-06-17/1781684089320.md` | You are a principal software architect (Google / Palantir / Microsoft-level).  Y | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0130 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781696790844.md` | ------  > [osiris-app internal] load metadata for docker.io/library/node:22-alpi | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0131 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781759466869.md` | Tu es un ingénieur senior spécialisé en architecture logicielle SOC/OSINT.  Anal | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0132 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556859.md` | Dockerfile.app:4  --------------------     2 \|     WORKDIR /app     3 \|     COPY | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0133 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556860.md` | Dockerfile.app:4  --------------------     2 \|     WORKDIR /app     3 \|     COPY | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0134 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781773490515.md` | Tu es chargé de concevoir Osiris-Lab, une plateforme d’intelligence modulaire de | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0135 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781773629795.md` | Tu es chargé de concevoir Osiris-Lab, une plateforme d’intelligence modulaire de | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0136 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781790224363.md` | [+] up 3/4  ✔ Image osiris-intel:latest          Built | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0137 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781845301775.md` | Analyse entièrement ce dépôt.  Je veux que tu comprennes :  - l'architecture com | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0138 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781847538003.md` | Supprime toutes les traces de "Cline".  Inclut :  - texte - commentaires - varia | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0139 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781852108784.md` | Tu fais partie de l'équipe d'ingénierie d'Osiris-Lab v2.  Les fichiers contenus | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0140 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781855138200.md` | Analyse la feature demandée en utilisant /docs.  1. Identifier modules impactés | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0141 | `Obsidian/Archives/Conversations/cline/2026-06-20/1781926691577.md` | zookeeper:   image: confluentinc/cp-zookeeper:7.6.0   ports:     - "2181:2181" | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0142 | `Obsidian/Archives/Conversations/cline/2026-06-20/1781927049974.md` | # PROMPT CODEX — CLEAN REPOSITORY & REBRAND TO OSIRIS-LAB  You are the Lead Soft | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0143 | `Obsidian/Archives/Conversations/cline/2026-06-21/1781928390660.md` | # Mission  Tu es un ingénieur DevOps et Software Architect senior.  Tu dois rest | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0144 | `Obsidian/Archives/Conversations/cline/2026-06-21/1782049607778.md` | You are a Senior Software Engineer responsible for safe refactoring of a product | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0145 | `Obsidian/Archives/Conversations/cline/2026-06-22/1782110267799.md` | # RFC-004 — Docker Foundation Clean Architecture  ## Role  You are a Senior Plat | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0146 | `Obsidian/Archives/Conversations/cline/2026-06-23/1782122303274.md` | # ADR-1003 — Single Entry Intent Model  ## Context  Multiple input types exist ( | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0147 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782236030293.md` | Design a full test suite for ETHAN CLI.  ---  # OBJECTIVE  Validate all CLI comm | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0148 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782277746766.md` | Design a full test suite for ETHAN CLI.  ---  # OBJECTIVE  Validate all CLI comm | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0149 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782282405489.md` | Set up the MCP server from https://github.com/VapiAI/mcp-server while adhering t | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0150 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782291853665.md` | Design a performance benchmark suite for ETHAN CLI.  ---  # OBJECTIVE  Measure C | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0151 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782299082878.md` | Design a debug mode for ETHAN CLI.  ---  # OBJECTIVE  Allow developers to inspec | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0152 | `Obsidian/Archives/Conversations/cline/2026-06-26/1782299840579.md` | Tu es un architecte logiciel senior spécialisé dans les systèmes d'IA autonomes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0153 | `Obsidian/Archives/Conversations/cline/2026-07-08/1782460736319.md` | Tu es un architecte logiciel senior spécialisé dans les assistants IA autonomes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0154 | `Obsidian/Archives/Conversations/cline/2026-07-08/1783480315445.md` | # ETHAN Systemd Services Auditor & Repair Agent  Tu es un ingénieur DevOps spéci | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0155 | `Obsidian/Archives/Conversations/cline/2026-07-09/1783498502281.md` | # ETHAN - Phase 0 : Préparation de la refonte complète du WebUI  Tu es le Lead S | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0156 | `Obsidian/Archives/Conversations/cline/2026-07-12/1783841799690.md` | You are the Lead UX Designer and Frontend Architect for the ETHAN AI Operating S | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0157 | `Obsidian/Archives/Conversations/cline/2026-07-18/1783595051689.md` | # ROLE  Tu es le Lead CTO du projet ETHAN.  Tu es responsable de la qualité glob | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0158 | `Obsidian/Archives/Conversations/cline/2026-07-19/1784446073123.md` | MISSION  Refondre complètement la commande :  ./ethan doctor  OBJECTIF  Transfor | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0159 | `Obsidian/Archives/Conversations/cline/2026-07-19/1784465617197.md` | Tu agis comme un Principal Software Architect et CTO avec plus de 20 ans d'expér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0160 | `Obsidian/Archives/Conversations/cline/2026-07-20/1784468478017.md` | Tu es un Principal Platform Engineer spécialisé dans les plateformes Linux distr | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0161 | `Obsidian/Archives/Conversations/cline/2026-07-21/1784553716546.md` | Tu interviens comme Chief Technology Officer (CTO), Enterprise Software Architec | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0162 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784629956873.md` | Tu es le CTO responsable de la stabilisation du projet ETHAN.  Tu as accès aux r | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0163 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784702896150.md` | Tu es un ingénieur DevOps/SRE senior.  Audit le runtime ETHAN.  Objectif : Faire | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0164 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784714379731.md` | Tu es le CTO responsable de la stabilisation du projet ETHAN.  Tu as accès aux r | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0165 | `Obsidian/Archives/Conversations/cline/2026-07-23/1784720147277.md` | Tu es architecte logiciel.  Maintenant que Core fonctionne :  Analyse ETHAN pour | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0166 | `Obsidian/Archives/Conversations/cline/2026-07-23/1784780539134.md` | Tu es un Lead Frontend et un expert Next.js.  Mission :  Réaliser un audit compl | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0167 | `Obsidian/Archives/Conversations/cline/2026-07-30/1784803567417.md` | Tu es Lead Frontend, UX Architect et Architecte logiciel.  Le projet ETHAN possè | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0168 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785382419039.md` | Tu es un ingénieur Senior SRE / Architecte Linux spécialisé en systemd, Docker C | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0169 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785475619469.md` | Mission : auditer entièrement la séquence de démarrage ETHAN.  Contexte :  NATS | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0170 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785478061904.md` | Session 1785478061904 | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0171 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785497242482.md` | Tu es un Senior Staff Engineer SRE + Python Architect chargé de stabiliser ETHAN | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0172 | `Obsidian/Archives/Conversations/cline/2026-08-02/1785510775651.md` | Tu es expert React UI.  Mission :  Analyser uniquement la Sidebar.  Comparer ave | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0173 | `Obsidian/Archives/Conversations/cline/2026-08-02/1785663110020.md` | Tu es un architecte logiciel senior spécialisé dans les plateformes IA.  Analyse | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0174 | `Obsidian/Archives/Conversations/cline/2026-08-03/1785676074904.md` | Améliore l'interface Chat ETHAN.  Ajouter un sélecteur de moteur IA directement | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0175 | `Obsidian/Archives/Conversations/cline/2026-08-03/1785748404435.md` | # ETHAN Architecture Audit Agent  Tu es un architecte logiciel senior chargé d'a | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0176 | `Obsidian/Archives/Conversations/cline/2026-08-04/1785763683280.md` | # ETHAN Unified Configuration Agent  Mission :  Créer un système de configuratio | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0177 | `Obsidian/Archives/Conversations/cline/2026-08-11/1786194792842.md` | # CODEX PROMPT — STANDARDIZE ALL OSIRIS-LAB WORKERS  You are the Principal Go En | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0178 | `Obsidian/Archives/Conversations/cline/2026-08-11/1786441307139.md` | # CODEX PROMPT — STANDARDIZE ALL OSIRIS-LAB WORKERS  You are the Principal Go En | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0179 | `Obsidian/Archives/Conversations/cline/2026-08-12/1785821621715.md` | # ETHAN Interface Independence Validation  Mission :  Valider que les interfaces | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0180 | `Obsidian/Archives/Conversations/cline/2026-08-12/1786516782485.md` | Tu es le CTO / Principal Software Architect nouvellement responsable de la trans | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0181 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786520589377.md` | Tu es le CTO / Principal Engineer responsable de la refonte complète de la WebUI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0182 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-01.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0183 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-02.md` | 1786588790163-part-02.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0184 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-03.md` | 1786588790163-part-03.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0185 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-04.md` | 1786588790163-part-04.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0186 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-05.md` | 1786588790163-part-05.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0187 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786592167914.md` | Tu es maintenant l'architecte principal chargé de concevoir la transformation Op | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0188 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786689632319.md` | Tu es un Senior SRE / Principal Backend Engineer spécialisé dans Docker, FastAPI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0189 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786691977752.md` | Tu es le CTO responsable de transformer Open-WebUI en ETHAN WebUI.  Utilise tous | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0190 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786694120897.md` | Tu es le CTO responsable de transformer Open-WebUI en ETHAN WebUI.  Utilise tous | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0191 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786715813776.md` | Tu es le CTO / Principal Engineer d'ETHAN.  À chaque nouvelle session de travail | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0192 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786767655858.md` | Tu es maintenant le Senior Engineer responsable de l'implémentation P0 du plan : | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0193 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786771650555.md` | Tu es maintenant le CTO effectuant une revue indépendante du travail réalisé.  T | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0194 | `Obsidian/Archives/Conversations/cline/2026-08-17/1786773027890.md` | Tu travailles sur le projet ETHAN.  OBJECTIF  Nous voulons faire évoluer l'inter | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0195 | `Obsidian/Archives/Conversations/cline/2026-08-17/1786962026659.md` | Tu travailles sur le projet ETHAN.  OBJECTIF ARCHITECTURAL  Nous allons intégrer | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0196 | `Obsidian/Archives/Conversations/cline/2026-08-18/1786966184691.md` | Nous avons maintenant deux éléments distincts :  1. ETHAN 2. Open WebUI déployé | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0197 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787028404021.md` | # ETHAN — WEBUI PLAN EXECUTION / IMPLEMENTATION MODE  Tu travailles directement | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0198 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787031131780.md` | # ETHAN — APPLY EXISTING ARCHITECTURE  Tu travailles dans le repository ETHAN : | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0199 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787040529358.md` | # ETHAN WEBUI — TRUE OPEN WEBUI FORK STRATEGY  Tu travailles dans :  /home/fatsi | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0200 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787043334788.md` | # ETHAN WEBUI — IMPLEMENTATION FROM EXISTING SPECIFICATIONS  Repository:  /home/ | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0201 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787050182381.md` | # ETHAN WEBUI — OPEN WEBUI FUNCTIONALITY  Utilise les fonctionnalités et mécanis | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0202 | `Obsidian/Archives/Conversations/cline/2026-08-19/1787051436064.md` | # ETHAN WEBUI — MASTER IMPLEMENTATION VERIFICATION  Repository:  /home/fatsio/AI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0203 | `Obsidian/Archives/Conversations/cline/2026-08-23/1787143354523.md` | # ETHAN WEBUI — FUNCTIONALITY RESTORATION AND OPEN WEBUI FIDELITY  Repository: | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0204 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-01.md` | Gérer le cycle de vie d’Odin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0205 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-02.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-02.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0206 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-03.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-03.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0207 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-04.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-04.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0208 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16882-fc47-73c2-85e1-a6093f0dbfd9.md` | Migrer God’s Eye View vers Odin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0209 | `Obsidian/Archives/Conversations/copilot/2026-04-24/b19268d9-cfc6-4cf3-b3cf-142ff2d72088.md` | Tu es un ingénieur logiciel senior expert en IA locale, systèmes d’agents LLM, R | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0210 | `Obsidian/Archives/Conversations/copilot/2026-05-25/36e60f5c-6fff-4b49-91db-77a2eb8078d6.md` | Construis maintenant le bootstrap COMPLET du projet Atas AI.  Génère UNIQUEMENT | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0211 | `Obsidian/Archives/Conversations/from-ethan-knowledge/cline/2026-08-13/1786588790163.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0212 | `Obsidian/Archives/Events/EVT-20261103T132131362051-OBSERVED-ethan-api-gateway-started.md` | ETHAN API gateway started | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0213 | `Obsidian/Archives/Events/EVT-20261103T150233966728-OBSERVED-ethan-api-gateway-started.md` | ETHAN API gateway started | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0214 | `Obsidian/Engineering/API/CONTRACTS-API.md` | Contrats API — ETHAN (WebUI ↔ Core) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0215 | `Obsidian/Engineering/API/ETHAN_REBUILD_P1_CONTRACTS.md` | ETHAN — Spécification de contrats API P1 (proposition, sans code) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0216 | `Obsidian/Engineering/API/contract-v1.md` | Contrat API ETHAN v1 — État actuel (refonte Phase 0) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0217 | `Obsidian/Engineering/API/openapi.v1.json` | openapi.v1.json | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0218 | `Obsidian/Engineering/API/openapi.yaml` | OpenAPI 3.1.0 — Jarvis OS API Reference | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0219 | `Obsidian/Engineering/Audits/00-ETAT-DES-LIEUX.md` | État des lieux — Analyse initiale du repository | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0220 | `Obsidian/Engineering/Audits/01-PHASE-A-CONSOLIDATION.md` | Phase A — Consolidation — Plan d'exécution | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0221 | `Obsidian/Engineering/Audits/02-PHASE-B-MCP.md` | Phase B — MCP — Plan d'exécution | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0222 | `Obsidian/Engineering/Audits/03-PHASE-C-SETTINGS.md` | Phase C — Settings & UX — Plan d'exécution | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0223 | `Obsidian/Engineering/Audits/04-PLAN-INTERPRETER-REPORT.md` | ETHAN WebUI — PLAN INTERPRETER REPORT | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0224 | `Obsidian/Engineering/Audits/ACCOUNTS_SUMMARY.md` | Synthèse des Audits ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0225 | `Obsidian/Engineering/Audits/ARCHITECTURE_KERNEL_CORE.md` | Audit Architecture — Kernel & Core d'ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0226 | `Obsidian/Engineering/Audits/AUDIT_INTEGRATION_2026-10-08.md` | AUDITINTEGRATION2026-10-08 | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0227 | `Obsidian/Engineering/Audits/AUDIT_REPORT.md` | Audit de l'état du code ETHAN — WebUI / backend / Core | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0228 | `Obsidian/Engineering/Audits/AUDIT_SKILLS_ECC_INTEGRATION.md` | ETHAN — Phase 1: Audit d'intégration des skills ECC | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0229 | `Obsidian/Engineering/Audits/AUTH_ARCHITECTURE.md` | Architecture Cible Authentification ETHAN OS | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0230 | `Obsidian/Engineering/Audits/AUTH_FINAL_VALIDATION.md` | Validation Finale SRE — Authentification ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0231 | `Obsidian/Engineering/Audits/AUTH_FLOW_AUDIT.md` | Audit du Flux d'Authentification ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0232 | `Obsidian/Engineering/Audits/Audit Architecture — WebUI vs Core Runtime.md` | Audit Architecture — WebUI vs Core/Runtime | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0233 | `Obsidian/Engineering/Audits/Audit Fonctionnel WebUI Dashboard (PLAN MODE).md` | 📋 Rapport Complet — Audit Fonctionnel WebUI Dashboard (PLAN MODE) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0234 | `Obsidian/Engineering/Audits/CI_CD_SECURITY_ASSESSMENT.md` | CI/CD Security Assessment — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0235 | `Obsidian/Engineering/Audits/CLINE_CHECKPOINT_INVENTORY.md` | Annexe — Inventaire des checkpoints Cline | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0236 | `Obsidian/Engineering/Audits/CLINE_RECOVERY_ANALYSIS.md` | Analyse de récupération – checkpoints Cline ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0237 | `Obsidian/Engineering/Audits/CLI_PRODUCTION_AUDIT.md` | Revue de production du CLI ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0238 | `Obsidian/Engineering/Audits/DEPENDENCY_SECURITY_INVENTORY.md` | Dependency Security Inventory — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0239 | `Obsidian/Engineering/Audits/DOCKER_IMAGE_SECURITY_ASSESSMENT.md` | Docker Image Security Assessment — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0240 | `Obsidian/Engineering/Audits/DOUBLE_AUTH_AUDIT.md` | Audit des Systèmes d'Authentification (ETHAN OS) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0241 | `Obsidian/Engineering/Audits/ETHAN_API_HEALTHCHECK_DIAGNOSTIC.md` | ETHAN — Diagnostic API Healthcheck (running/unhealthy) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0242 | `Obsidian/Engineering/Audits/ETHAN_COMPONENT_INTERFACE_INVENTORY_P0.md` | ETHAN — Inventaire des interfaces entre composants (P0) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0243 | `Obsidian/Engineering/Audits/ETHAN_ENGINEERING_ROADMAP.md` | ETHAN Engineering Roadmap | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0244 | `Obsidian/Engineering/Audits/ETHAN_MASTER_PLAN.md` | ETHAN Technical Master Plan | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0245 | `Obsidian/Engineering/Audits/ETHAN_PERSISTENT_DATA_REGISTRY_P0.md` | ETHAN — Registre des données à préserver (P0, audit seulement) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0246 | `Obsidian/Engineering/Audits/ETHAN_PUBLIC_PRIVATE_INVENTORY.md` | ETHAN — Public/Private Inventory | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0247 | `Obsidian/Engineering/Audits/ETHAN_PUBLIC_PRIVATE_SEPARATION.md` | ETHAN — Public/Private Separation and Publication Readiness | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0248 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P0_AUDIT.md` | ETHAN — Audit factuel P0 avant refonte (hybride Rust + Python, Open WebUI) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0249 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv` | ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0250 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P1_RISK_REGISTER.md` | ETHAN — Registre des risques et décisions en attente (P1) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0251 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P2_FEASIBILITY.md` | ETHAN — Rapport de faisabilité P2 (fork WebUI isolé Open WebUI v0.9.1) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0252 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P3` | ETHAN_REBUILD_P3 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0253 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P3_VERTICAL_PROTOTYPE.md` | ETHAN — Rapport P3 prototype vertical Core hybride | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0254 | `Obsidian/Engineering/Audits/ETHAN_REBUILD_P5_VALIDATION_GATE.md` | ETHAN — Rapport de validation P5 (gate avant intégration) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0255 | `Obsidian/Engineering/Audits/ETHAN_STABILITY_REPORT.md` | ETHANSTABILITYREPORT | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0256 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_ARCHITECTURE_MATRIX.md` | Matrice architecturale — Frontière ETHAN ↔ ETHAN WebUI (base Open WebUI) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0257 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_CTO_REVIEW.md` | Audit CTO — Revue Indépendante WebUI ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0258 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_GAP_ANALYSIS.md` | ETHAN WebUI Gap Analysis | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0259 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_INITIAL_ARCHITECTURE_AUDIT.md` | ETHAN WebUI Initial Architecture Audit | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0260 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_MASTER_PLAN.md` | ETHAN WebUI — Master Implementation Plan | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0261 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_MIGRATION_STRATEGY.md` | Stratégie de migration — Ancienne WebUI ETHAN → ETHAN WebUI (fork Open WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0262 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md` | Architecture cible — Models & Providers ETHAN (inspiré Open WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0263 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_OPENWEBUI_MIGRATION.md`` | ETHAN WebUI $\rightarrow$ Open-WebUI Migration Plan | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0264 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md` | Architecture cible — RAG, Knowledge, Files, MCP, Tools (inspiré Open WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0265 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md` | Architecture Settings ETHAN WebUI — inspirée Open WebUI | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0266 | `Obsidian/Engineering/Audits/ETHAN_WEBUI_V2_ARCHITECTURE.md` | ETHAN WebUI v2 – Architecture Overview | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0267 | `Obsidian/Engineering/Audits/GITHUB_ISSUES.md` | ETHAN GitHub Issues - Tickets de Correction | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0268 | `Obsidian/Engineering/Audits/GITHUB_SECURITY_ASSESSMENT.md` | GitHub Security Assessment — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0269 | `Obsidian/Engineering/Audits/GIT_BACKUP_AND_CONSOLIDATION_PLAN.md` | ETHAN — Plan de sauvegarde et consolidation Git | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0270 | `Obsidian/Engineering/Audits/GIT_SECURITY_AND_HISTORY_AUDIT.md` | Audit Git – sécurité, historique et références ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0271 | `Obsidian/Engineering/Audits/INDEX.md` | Documentation Architecture ETHAN — Index | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0272 | `Obsidian/Engineering/Audits/LLM_PROVIDERS_ARCHITECTURE.md` | Architecture Multi-Providers LLM — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0273 | `Obsidian/Engineering/Audits/OPENWEBUI_COMPONENT_REFERENCE.md` | Open-WebUI — Référence des composants et contrats | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0274 | `Obsidian/Engineering/Audits/OPENWEBUI_ETHAN_MIGRATION_ANALYSIS.md` | Analyse & Plan de Migration — Open WebUI → ETHAN WebUI | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0275 | `Obsidian/Engineering/Audits/OPENWEBUI_FORK_FEASIBILITY.md` | Open-WebUI Fork Feasibility Analysis | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0276 | `Obsidian/Engineering/Audits/OPENWEBUI_FUNCTIONAL_REFERENCE.md` | Open-WebUI — Référence fonctionnelle | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0277 | `Obsidian/Engineering/Audits/OPENWEBUI_UX_REFERENCE.md` | Open-WebUI — Référence UX | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0278 | `Obsidian/Engineering/Audits/PRODUCTION_READINESS.md` | ETHAN — Rapport Go/No-Go Production (1 an autonome) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0279 | `Obsidian/Engineering/Audits/Plan de Consolidation Architecture ETHAN.md` | Plan de Consolidation Architecture ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0280 | `Obsidian/Engineering/Audits/README_CHANGELOG.md` | README Change Log — Refactor (Project Identity & Current Architecture) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0281 | `Obsidian/Engineering/Audits/RUNTIME-001.md` | INCIDENT RUNTIME-001 : NATS ne démarre pas | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0282 | `Obsidian/Engineering/Audits/Rapport SRE & Architecture.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0283 | `Obsidian/Engineering/Audits/Rapport_SRE_Stabilisation_Final.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0284 | `Obsidian/Engineering/Audits/SECRET_EXPOSURE_ASSESSMENT.md` | Secret Exposure Assessment — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0285 | `Obsidian/Engineering/Audits/SECURITY_ASSET_INVENTORY.md` | Security Asset Inventory — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0286 | `Obsidian/Engineering/Audits/SECURITY_AUDIT.md` | Audit Sécurité ETHAN - OS IA Personnel | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0287 | `Obsidian/Engineering/Audits/SECURITY_AUDIT_RECONCILIATION.md` | Security Audit Reconciliation — ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0288 | `Obsidian/Engineering/Audits/SECURITY_AUDIT_REPORT.md` | Audit Sécurité ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0289 | `Obsidian/Engineering/Audits/SECURITY_BACKLOG.md` | ETHAN Security Backlog | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0290 | `Obsidian/Engineering/Audits/SECURITY_EVIDENCE_REGISTER.md` | Security Evidence Register — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0291 | `Obsidian/Engineering/Audits/SECURITY_PROGRAM_CHARTER.md` | Security Program Charter — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0292 | `Obsidian/Engineering/Audits/SECURITY_RISK_REGISTER.md` | Security Risk Register — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0293 | `Obsidian/Engineering/Audits/SECURITY_ROADMAP.md` | Security Roadmap — ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0294 | `Obsidian/Engineering/Audits/SECURITY_VERIFICATION_MATRIX.md` | Security Verification Matrix — ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0295 | `Obsidian/Engineering/Audits/SESSION-REPORT-2026-08-18.md` | Rapport de Clôture de Session — ETHAN WebUI | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0296 | `Obsidian/Engineering/Audits/STABILITY_REPORT.md` | ETHAN Stability Report | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0297 | `Obsidian/Engineering/Audits/Sessions/2026-11-01.md` | Archive de session — 2026-11-01 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0298 | `Obsidian/Engineering/Audits/Sessions/2026-11-02.md` | Session 2026-11-02 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0299 | `Obsidian/Engineering/Audits/Sessions/2026-11-03.md` | Session 2026-11-03 — MEM-014 Phase 1 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0300 | `Obsidian/Engineering/Audits/Sessions/2026-11-04.md` | Session 2026-11-04 — Quantar real task runtime | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0301 | `Obsidian/Engineering/Audits/TECHNICAL_DEBT_ANALYSIS.md` | 📊 Analyse de la Dette Technique ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0302 | `Obsidian/Engineering/Audits/TRUST_BOUNDARIES_REGISTER.md` | Trust Boundaries Register — ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0303 | `Obsidian/Engineering/Audits/VALIDATION_FINALE_ODIN.md` | Validation Finale Intégration ETHAN ↔ Odin | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0304 | `Obsidian/Engineering/Audits/WEBUI_CURRENT_STATE.md` | ETHAN WebUI — état actuel vérifié | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0305 | `Obsidian/Engineering/Audits/WEBUI_DOCUMENTARY_INVENTORY.md` | ETHAN WebUI Documentary Inventory | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0306 | `Obsidian/Engineering/Audits/WEBUI_IMPLEMENTATION_STATUS.md` | ETHAN WebUI Implementation Status | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0307 | `Obsidian/Engineering/Audits/WEBUI_PRIORITIES.md` | ETHAN WebUI Implementation Priorities | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0308 | `Obsidian/Engineering/Audits/api-startup-fix.md` | ETHAN API Startup Fix | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0309 | `Obsidian/Engineering/Audits/architecture-audit.md` | Audit d'Architecture ETHAN — Rapport Actualisé | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0310 | `Obsidian/Engineering/Audits/architecture-decisions-summary.md` | Réunion Architecture — Décisions en attente | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0311 | `Obsidian/Engineering/Audits/architecture-decisions.md` | Décisions Architecture — Recommandations | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0312 | `Obsidian/Engineering/Audits/architecture.md` | Architecture d'Ethan | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0313 | `Obsidian/Engineering/Audits/audit-boot-mechanism.md` | Audit d'Architecture — Mécanisme de Démarrage ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0314 | `Obsidian/Engineering/Audits/audit-ethan-up-RESUME.md` | Audit ./ethan up — Résumé | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0315 | `Obsidian/Engineering/Audits/audit-ethan-up.md` | Audit de la commande ./ethan up | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0316 | `Obsidian/Engineering/Audits/audit-plugins.md` | Audit Système de Plugins ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0317 | `Obsidian/Engineering/Audits/audit_rapport.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0318 | `Obsidian/Engineering/Audits/auth_architecture_audit.md` | ETHAN OS — Authentication Architecture Audit & Migration Plan | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0319 | `Obsidian/Engineering/Audits/auth_audit_report_3.md` | ETHAN Authentication Audit Report | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0320 | `Obsidian/Engineering/Audits/auth_flow_audit.md` | ETHAN Auth Flow — Production Audit Report | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0321 | `Obsidian/Engineering/Audits/boot-dev-extensions.md` | Boot — Extensions développement | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0322 | `Obsidian/Engineering/Audits/boot-from-scratch.md` | Boot depuis un système vierge | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0323 | `Obsidian/Engineering/Audits/boot_sequence_audit.md` | 🔬 ETHAN Boot Sequence Audit — Verified Report | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0324 | `Obsidian/Engineering/Audits/chat-agent-model-selector.md` | Sélecteurs Agent / Model du chat — WebUI ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0325 | `Obsidian/Engineering/Audits/chat-composer-simplification.md` | Simplification du composer de chat — WebUI ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0326 | `Obsidian/Engineering/Audits/chat-layout-visual-polish.md` | Chat Layout — Visual Polish (WebUI réel, port 3001) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0327 | `Obsidian/Engineering/Audits/chat-ui-deduplication.md` | Dé-duplication des contrôles du chat — WebUI ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0328 | `Obsidian/Engineering/Audits/cto-review-completed.md` | CTO Review — Corrections Appliquées | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0329 | `Obsidian/Engineering/Audits/deployment.md` | Déploiement ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0330 | `Obsidian/Engineering/Audits/desktop-auto-update.md` | Desktop auto-update | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0331 | `Obsidian/Engineering/Audits/doctor.md` | ETHAN Doctor — Diagnostic de santé | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0332 | `Obsidian/Engineering/Audits/duplicate-data-integrity.md` | Duplicate Data Integrity — Audit | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0333 | `Obsidian/Engineering/Audits/ethan-launcher.md` | ETHAN — Lanceur officiel | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0334 | `Obsidian/Engineering/Audits/ethan-up.md` | Rapport d’intégration — Système de plugins conversationnels ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0335 | `Obsidian/Engineering/Audits/file-management-regression.md` | File Management Regression — Audit & Correction | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0336 | `Obsidian/Engineering/Audits/frontend_auth_audit.md` | Audit Complet — Flux Frontend Login ETHAN | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0337 | `Obsidian/Engineering/Audits/gen_install_script.py` | (source path, published URL path) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0338 | `Obsidian/Engineering/Audits/gen_ref_pages.py` | gen_ref_pages.py | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0339 | `Obsidian/Engineering/Audits/gods-eye-view-integration.md` | Intégration God's Eye View (GEV) dans ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0340 | `Obsidian/Engineering/Audits/hardening.md` | ETHAN — Hardening & Correctifs de Sécurité | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0341 | `Obsidian/Engineering/Audits/implementation-guide-P0.md` | Guide d'Implémentation P0 — Actions Critiques | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0342 | `Obsidian/Engineering/Audits/implementation-guide-P1.md` | Guide d'Implémentation P1 — Actions Importantes | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0343 | `Obsidian/Engineering/Audits/implementation-guide-P2.md` | Guide d'Implémentation P2 — Améliorations | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0344 | `Obsidian/Engineering/Audits/implementation-guide-P3.md` | Guide d'Implémentation P3 — Optimisations | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0345 | `Obsidian/Engineering/Audits/installation.md` | Installation d'ETHAN — Debian 13 (Trixie) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0346 | `Obsidian/Engineering/Audits/odin-direct-docker-compose.md` | Migration Odin — Architecture Docker directe (sans odin-controller) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0347 | `Obsidian/Engineering/Audits/odysseus-cleanup-audit.md` | Odysseus Cleanup Audit Report | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0348 | `Obsidian/Engineering/Audits/openwebui-ethan-ui-migration.md` | Open-WebUI → ETHAN — Analyse UX et Tableau de Migration | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0349 | `Obsidian/Engineering/Audits/openwebui-migration-final-audit.md` | Audit final — Migration WebUI ETHAN vers l'expérience Open WebUI | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0350 | `Obsidian/Engineering/Audits/openwebui-shell-migration.md` | ETHAN WebUI — Migration du shell vers Open WebUI | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0351 | `Obsidian/Engineering/Audits/p1_audit_report.md` | P1 Audit Report — ETHAN WebUI | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0352 | `Obsidian/Engineering/Audits/pythonpath-fix.md` | Correction PYTHONPATH — Import core.kernel | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0353 | `Obsidian/Engineering/Audits/rag-settings-regression.md` | RAG Settings Regression — Audit & Restauration | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0354 | `Obsidian/Engineering/Audits/reference-comparison-odysseus-canirun.md` | Reference Comparison — Odysseus & CanIRun.ai | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0355 | `Obsidian/Engineering/Audits/roadmap-P0.md` | Roadmap P0 — Actions Critiques (Immédiat) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0356 | `Obsidian/Engineering/Audits/roadmap-P1.md` | Roadmap P1 — Actions Importantes (Court terme) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0357 | `Obsidian/Engineering/Audits/roadmap-P2.md` | Roadmap P2 — Améliorations (Moyen terme) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0358 | `Obsidian/Engineering/Audits/roadmap-P3.md` | Roadmap P3 — Optimisations (Long terme) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0359 | `Obsidian/Engineering/Audits/roadmap-global.md` | Roadmap Globale — Suivi des Actions Architecture | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0360 | `Obsidian/Engineering/Audits/runbook.md` | ETHAN - Runbook Opérationnel | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0361 | `Obsidian/Engineering/Audits/service-orchestration.md` | Orchestration des Services ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0362 | `Obsidian/Engineering/Audits/sidebar-openwebui-behavior.md` | Sidebar — comportement Open-WebUI (refonte v5) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0363 | `Obsidian/Engineering/Audits/sre-runbook.md` | Runbook SRE — ETHAN Cognitive OS | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0364 | `Obsidian/Engineering/Audits/sre_stability_audit.md` | ETHAN SRE Stability Audit — 2026-08-02 | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0365 | `Obsidian/Engineering/Audits/telemetry.md` | Telemetry | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0366 | `Obsidian/Engineering/Audits/transparency-readability-audit.md` | Audit — Suppression des effets de transparence (WebUI) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0367 | `Obsidian/Engineering/Audits/ui-agent-selector.md` | Sélecteur d'agent du chat — Implémentation | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0368 | `Obsidian/Engineering/Audits/ui-chat-composer.md` | Refonte du Composer de chat ETHAN (inspiré Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0369 | `Obsidian/Engineering/Audits/ui-chat-context.md` | Barre de contexte actif du chat — ChatContextBar | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0370 | `Obsidian/Engineering/Audits/ui-cleanup.md` | Nettoyage Frontend ETHAN WebUI — Rapport | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0371 | `Obsidian/Engineering/Audits/ui-config-pages-refactor.md` | Refonte UX/UI des pages de configuration — card grid (inspiré Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0372 | `Obsidian/Engineering/Audits/ui-navigation.md` | ETHAN WebUI — Navigation Refondue (style Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0373 | `Obsidian/Engineering/Audits/ui-openwebui-agent-model-selectors.md` | ETHAN WebUI — Sélecteurs Agent + Model (niveau Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0374 | `Obsidian/Engineering/Audits/ui-openwebui-config-pages.md` | ETHAN WebUI — Refonte des pages vers les patterns Open-WebUI | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0375 | `Obsidian/Engineering/Audits/ui-openwebui-final-audit.md` | Audit final — WebUI ETHAN post-refonte (cohérence Open-WebUI) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0376 | `Obsidian/Engineering/Audits/ui-openwebui-refactor-audit.md` | Audit WebUI ETHAN — Refonte UX inspirée d'Open-WebUI | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0377 | `Obsidian/Engineering/Audits/ui-openwebui-shell-implementation.md` | Implémentation — Refonte Shell WebUI (inspiration Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0378 | `Obsidian/Engineering/Audits/ui-openwebui-target-architecture.md` | Architecture UX cible — WebUI ETHAN (référence Open-WebUI) | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0379 | `Obsidian/Engineering/Audits/webui-navigation-first-experience.md` | Première expérience de navigation — WebUI ETHAN | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0380 | `Obsidian/Engineering/Audits/webui-port-3001-validation.md` | WebUI ETHAN — Validation du port officiel 3001 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0381 | `Obsidian/Engineering/Audits/webui-port-3001.md` | Migration WebUI ETHAN → port 3001 | Audit | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0382 | `Obsidian/Engineering/Audits/webui-ux-polish-audit.md` | Audit UX / Polish — WebUI ETHAN (phase TEST · CORRECTION · POLISH) | Audit | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0383 | `Obsidian/Engineering/BUILD/api-server.md` | API Server | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0384 | `Obsidian/Engineering/BUILD/docker.md` | Docker Deployment | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0385 | `Obsidian/Engineering/BUILD/index.md` | Deployment | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0386 | `Obsidian/Engineering/BUILD/launchd.md` | launchd Service (macOS) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0387 | `Obsidian/Engineering/BUILD/systemd.md` | systemd Service (Linux) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0388 | `Obsidian/Engineering/Benchmarks/BASELINE_VALIDATION.md` | ETHAN — Baseline Validation | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0389 | `Obsidian/Engineering/Benchmarks/ETHAN_ROADMAP.md` | ETHAN — Technical Roadmap Proposal | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0390 | `Obsidian/Engineering/Benchmarks/ETHAN_SECURITY_ASSESSMENT.md` | ETHAN — Security Assessment | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0391 | `Obsidian/Engineering/Benchmarks/ETHAN_TECHNICAL_BASELINE.md` | ETHAN — Technical Baseline | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0392 | `Obsidian/Engineering/Benchmarks/ETHAN_TECHNICAL_DEBT.md` | ETHAN — Technical Debt | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0393 | `Obsidian/Engineering/Benchmarks/ETHAN_TEST_BASELINE.md` | ETHAN — Test Baseline | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0394 | `Obsidian/Engineering/Benchmarks/knowledge-bottleneck-analysis.md` | Knowledge Bottleneck Analysis | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0395 | `Obsidian/Engineering/Benchmarks/knowledge-performance-baseline.md` | Knowledge Performance Baseline | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0396 | `Obsidian/Engineering/Benchmarks/knowledge-postgres-environment.md` | Isolated PostgreSQL Test Environment — Knowledge/RAG | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0397 | `Obsidian/Engineering/Benchmarks/knowledge-postgres-validation.md` | Knowledge PostgreSQL Validation - Current State | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0398 | `Obsidian/Engineering/Development/ETHAN_WEBUI_FORK_STRATEGY.md` | Stratégie de Maintenance — Fork Open-WebUI → ETHAN WebUI | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0399 | `Obsidian/Engineering/Development/contributing.md` | Contributing Guide | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0400 | `Obsidian/Engineering/Development/mining-nvidia-validation.md` | NVIDIA Pearl Mining Validation Runbook | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0401 | `Obsidian/Engineering/Development/mining.md` | Adding a Mining Provider | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0402 | `Obsidian/Engineering/Development/pearl-model-enablement.md` | Pearl Model Enablement | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0403 | `Obsidian/Engineering/Development/release-checklist.md` | Release Checklist | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0404 | `Obsidian/Engineering/Development/roadmap.md` | Roadmap | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0405 | `Obsidian/Engineering/Runbooks/ETHAN_REBUILD_P1_RUNBOOK.md` | ETHAN — Runbook P1 (installation, sauvegarde, restauration, diagnostic, rollback) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0406 | `Obsidian/Engineering/Runbooks/QUANTAR_REAL_TASK_RUNTIME_AUDIT.md` | QUANTARREALTASKRUNTIMEAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0407 | `Obsidian/Engineering/Runbooks/backup-volumes-procedure.md` | Procédure de sauvegarde des volumes Docker ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0408 | `Obsidian/Engineering/Runbooks/webui-refresh.md` | WebUI refresh procedure — no OS reboot | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0409 | `Obsidian/Engineering/Security/CTO_SECURITY_ARCHITECTURE_REVIEW.md` | CTO Security Architecture Review — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0410 | `Obsidian/Engineering/Security/ETHAN_CONSTITUTION.md` | Constitution d'ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0411 | `Obsidian/Engineering/Security/RED_TEAM_SECURITY_REVIEW.md` | Red Team Security Review — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0412 | `Obsidian/Engineering/Security/SECURITY_TEST_PLAN.md` | Security Test Plan — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0413 | `Obsidian/Engineering/Security/WEBUI_AUTH_ARCHITECTURE.md` | ETHAN WebUI — Architecture d'Authentification Cryptographique | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0414 | `Obsidian/Engineering/Security/WEBUI_AUTH_CURRENT_STATE.md` | ETHAN WebUI — État Actuel de l'Authentification | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0415 | `Obsidian/Engineering/Security/WEBUI_AUTH_SETUP.md` | ETHAN WebUI — Guide de Setup Authentification Cryptographique | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0416 | `Obsidian/Engineering/Security/WEBUI_AUTH_THREAT_MODEL.md` | ETHAN WebUI — Modèle de Menace Authentification | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0417 | `Obsidian/Engineering/Security/public-release-allowlist-denylist.md` | Public Release Allowlist / Denylist | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0418 | `Obsidian/Engineering/Specs/2026-05-05-apple-silicon-pearl-mining-design.md` | Spec B — Apple Silicon enablement for Pearl mining | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0419 | `Obsidian/Engineering/Specs/2026-05-05-apple-silicon-pearl-mining-plan-v1.md` | Apple Silicon Pearl mining v1 — implementation plan | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0420 | `Obsidian/Engineering/Specs/2026-05-05-pearl-coordination-discussion-draft.md` | Pearl coordination thread — draft | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0421 | `Obsidian/Engineering/Specs/2026-05-05-vllm-pearl-mining-integration-design.md` | Spec A — vLLM-Pearl mining integration (v1) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0422 | `Obsidian/Engineering/Specs/2026-05-05-vllm-pearl-mining-integration-plan.md` | vLLM-Pearl mining integration — implementation plan | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0423 | `Obsidian/Engineering/Specs/2026-09-30-cartographie-interfaciale.md` | Cartographie interfaciale — qui expose quelle capacité ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0424 | `Obsidian/Engineering/Specs/2026-09-30-ux-refonte-cartographie.md` | WebUI — Cartographie UX (route → composant → API → Core) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0425 | `Obsidian/Engineering/Specs/2026-09-30-webui-settings-honesty.md` | WebUI — Refonte Settings « honnête » (anti-fantôme) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0426 | `Obsidian/Engineering/Specs/2026-10-01-cartographie-webui-ux.md` | Cartographie WebUI → API → Core (préalable obligatoire à la refonte UX) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0427 | `Obsidian/Engineering/Specs/CLI_CONTRACT.md` | Contrat officiel du CLI ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0428 | `Obsidian/Engineering/Specs/ETHAN_CAPABILITIES_UX.md` | ETHAN — Design UX des Capacités (Knowledge, Skills, Tools, Memory) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0429 | `Obsidian/Engineering/Specs/ETHAN_WEBUI_UX_ANALYSIS.md` | Analyse UX — Open-WebUI comme référence visuelle pour ETHAN WebUI | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0430 | `Obsidian/Engineering/Specs/ETHAN_WEBUI_UX_PARITY_SPEC.md` | ETHAN WebUI — Spécification de parité UX avec Open-WebUI | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0431 | `Obsidian/Engineering/Specs/RFC-0001-email-inbox.md` | RFC-0001 — Email Inbox ETHAN | Spécification | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0432 | `Obsidian/Engineering/Specs/RFC-0002-deep-research.md` | RFC-0002 — Deep Research ETHAN | Spécification | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0433 | `Obsidian/Engineering/Specs/RFC-0003-cookbook.md` | RFC-0003 — Cookbook ETHAN (recettes de workflows) | Spécification | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0434 | `Obsidian/Engineering/Specs/application-capability-discovery.md` | Spécification — Découverte de capacités applicatives (MEM-014 Phase 2) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0435 | `Obsidian/Engineering/Specs/application-catalog-phase41.md` | Contrat de catalogue applicatif — MEM-014 Phase 41 | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0436 | `Obsidian/Engineering/Specs/application-compliance.md` | Spécification — Moteur de conformité (MEM-014 Phase 5) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0437 | `Obsidian/Engineering/Specs/application-contract-validator.md` | Documentation — Validateur contractuel (MEM-014 Phase 1) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0438 | `Obsidian/Engineering/Specs/application-identity.md` | Conventions d'identité applicative (MEM-014 Phase 1) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0439 | `Obsidian/Engineering/Specs/application-integration-contract.md` | Spécification — Contrat d'intégration applicative (MEM-014 Phase 4) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0440 | `Obsidian/Engineering/Specs/application-integration-readiness.md` | Spécification — Préparation à l'intégration applicative (MEM-014 Phase 13) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0441 | `Obsidian/Engineering/Specs/application-manifest.md` | Spécification — Manifeste d'application ETHAN (MEM-014 Phase 1) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0442 | `Obsidian/Engineering/Specs/application-manifest.schema.json` | application-manifest.schema.json | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0443 | `Obsidian/Engineering/Specs/application-observability-engineering-memory.md` | Spécification — Observabilité et Engineering Memory (MEM-014 Phase 7) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0444 | `Obsidian/Engineering/Specs/application-permissions-hrot.md` | Spécification — Permissions et Human Root of Trust (MEM-014 Phase 3) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0445 | `Obsidian/Engineering/Specs/application-persistence-mem014.md` | Spécification — Persistance durable MEM-014 (Phase 8) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0446 | `Obsidian/Engineering/Specs/application-resilience-lifecycle.md` | Spécification — Résilience et cycle de vie (MEM-014 Phase 6) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0447 | `Obsidian/Engineering/Specs/capability-registry.md` | Spécification — Capability Registry (MEM-014 Phase 9) | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0448 | `Obsidian/Engineering/Tests-Validation/agent-qa-runbook.md` | Agent QA Runbook | Note | Obsidian/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0449 | `Obsidian/INDEX.md` | INDEX — Mémoire technique ETHAN | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0450 | `Obsidian/Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md` | ETHAN — Architecture d'intelligence partagée pour les applications indépendantes | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0451 | `Obsidian/Knowledge/Architecture/EM-SERVICE-ARCHITECTURE.md` | ETHAN — Architecture du Engineering Memory Service | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0452 | `Obsidian/Knowledge/Architecture/ETHAN_APPLICATION_INTEGRATION_CONTRACT.md` | ETHAN Application Integration Contract | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0453 | `Obsidian/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` | ETHAN — Architecture de la mémoire technique | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0454 | `Obsidian/Knowledge/Architecture/MEMORY_DATA_MODEL.md` | ETHAN — Modèle de données de la mémoire technique | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0455 | `Obsidian/Knowledge/Architecture/RECORD_TEMPLATES.md` | ETHAN — Modèles d'enregistrement | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0456 | `Obsidian/Knowledge/INDEX_ETHAN_KNOWLEDGE.md` | ETHAN Knowledge Base — Index | Document | Obsidian/ | Conserver | Connaissance technique (Obsidian) | Faible |
| DOC-0457 | `Obsidian/Knowledge/Syntheses/by-agent/cline-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0458 | `Obsidian/Knowledge/Syntheses/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0459 | `Obsidian/Knowledge/Syntheses/by-agent/codex-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0460 | `Obsidian/Knowledge/Syntheses/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0461 | `Obsidian/Knowledge/Syntheses/by-agent/copilot-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0462 | `Obsidian/Knowledge/Syntheses/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0463 | `Obsidian/Knowledge/Sécurité/PERMISSION_MODEL.md` | ETHAN — Modèle de permissions pour l'Engineering Memory | Document | Obsidian/ | Conserver | Modèle de permission / sécurité | Faible |
| DOC-0464 | `Obsidian/Metadata/REGISTRY.md` | ETHAN — Registre de routage de la mémoire | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0465 | `Obsidian/Operational-Memory/BLOCKERS.md` | BLOCKERS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0466 | `Obsidian/Operational-Memory/DECISIONS.md` | DECISIONS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0467 | `Obsidian/Operational-Memory/DOCUMENTATION_AUDIT_REPORT_2026-11-04.md` | Audit de la documentation ETHAN — Phase A / Phase B | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0468 | `Obsidian/Operational-Memory/DOCUMENTATION_INVENTORY.md` | Inventaire documentaire ETHAN — Phase A / Phase B (réorganisation) | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0469 | `Obsidian/Operational-Memory/MEMORY_GOVERNANCE.md` | ETHAN — Gouvernance de la mémoire technique | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0470 | `Obsidian/Operational-Memory/PROJECT_STATE.md` | PROJECTSTATE — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0471 | `Obsidian/Operational-Memory/TASKS.md` | TASKS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0472 | `Obsidian/Operational-Memory/sources/docs-memory/DECISIONS.md` | Décisions — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0473 | `Obsidian/Operational-Memory/sources/docs-memory/PROJECT_STATE.md` | État courant — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0474 | `Obsidian/Operational-Memory/sources/docs-memory/README.md` | Mémoire inter-sessions Codex — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0475 | `Obsidian/Operational-Memory/sources/docs-memory/sessions/2026-11-01.md` | Archive de session — 2026-11-01 | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0476 | `Obsidian/Operational-Memory/sources/docs-memory/sessions/2026-11-02.md` | Session 2026-11-02 | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0477 | `Obsidian/Operational-Memory/sources/ethan-knowledge-meta/sync-state.json` | sync-state.json | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0478 | `Obsidian/README.md` | ETHAN — Mémoire technique consolidée | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0479 | `Obsidian/_meta/ADR_MEM_010_RECONCILIATION_REPORT.md` | ADR-MEM-010 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0480 | `Obsidian/_meta/ADR_MEM_011_RECONCILIATION_REPORT.md` | ADR-MEM-011 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0481 | `Obsidian/_meta/ADR_MEM_012_RECONCILIATION_REPORT.md` | ADR-MEM-012 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0482 | `Obsidian/_meta/AGENT_MEMORY_PROTOCOL_REPORT.md` | AGENTMEMORYPROTOCOLREPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0483 | `Obsidian/_meta/ARCHITECTURE_OPTIONS.md` | ARCHITECTUREOPTIONS — ETHAN Engineering Memory | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0484 | `Obsidian/_meta/AUDIT-ARCHIVES_ODSIDIAN.md` | AUDIT-ARCHIVES — Base de connaissance ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0485 | `Obsidian/_meta/CLEANUP_REPORT.md` | CLEANUP REPORT — ETHAN / OBSIDIAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0486 | `Obsidian/_meta/CONSOLIDATION_REPORT.md` | CONSOLIDATION REPORT — ETHAN / OBSIDIAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0487 | `Obsidian/_meta/CTO_RECONSTRUCTION_REPORT.md` | CTO RECONSTRUCTION REPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0488 | `Obsidian/_meta/DECISION_REGISTER.md` | DECISION REGISTER — ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0489 | `Obsidian/_meta/DELIVERY_GATE_REPORT.md` | DELIVERYGATEREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0490 | `Obsidian/_meta/DOCUMENTATION_MIGRATION_MANIFEST_2026-11-04.csv` | DOCUMENTATION_MIGRATION_MANIFEST_2026-11-04.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0491 | `Obsidian/_meta/DOCUMENTATION_MIGRATION_MANIFEST_DRYRUN_2026-11-04.csv` | DOCUMENTATION_MIGRATION_MANIFEST_DRYRUN_2026-11-04.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0492 | `Obsidian/_meta/ECOSYSTEM_ARCHITECTURE_VALIDATION_REPORT.md` | ECOSYSTEMARCHITECTUREVALIDATIONREPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0493 | `Obsidian/_meta/ECOSYSTEM_CAPABILITY_MATRIX.md` | ECOSYSTEMCAPABILITYMATRIX.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0494 | `Obsidian/_meta/ECOSYSTEM_DECISION_GAPS.md` | ECOSYSTEMDECISIONGAPS.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0495 | `Obsidian/_meta/ECOSYSTEM_DECISION_WORKBOOK.md` | ECOSYSTEMDECISIONWORKBOOK — ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0496 | `Obsidian/_meta/ETHAN_APPLICATION_INTEGRATION_COMPARISON.md` | ETHANAPPLICATIONINTEGRATIONCOMPARISON | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0497 | `Obsidian/_meta/ETHAN_PHASE_25_PLUGINS_UI_RELIABILITY.md` | ETHANPHASE25PLUGINSUIRELIABILITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0498 | `Obsidian/_meta/ETHAN_PHASE_26_RICH_RESPONSE_UI.md` | ETHANPHASE26RICHRESPONSEUI | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0499 | `Obsidian/_meta/ETHAN_PHASE_27_RICH_RESPONSE_VALIDATION.md` | ETHANPHASE27RICHRESPONSEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0500 | `Obsidian/_meta/ETHAN_PHASE_28_PLUGINS_UI_REPAIR.md` | ETHANPHASE28PLUGINSUIREPAIR | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0501 | `Obsidian/_meta/ETHAN_PHASE_29_PLUGINS_TOOLS_SEPARATION.md` | ETHANPHASE29PLUGINSTOOLSSEPARATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0502 | `Obsidian/_meta/ETHAN_PHASE_30_AUTHENTICATED_RUNTIME_VALIDATION.md` | ETHANPHASE30AUTHENTICATEDRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0503 | `Obsidian/_meta/ETHAN_PHASE_30_PLUGINS_SYSTEM_RECOVERY.md` | ETHANPHASE30PLUGINSSYSTEMRECOVERY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0504 | `Obsidian/_meta/ETHAN_PHASE_31_RICH_RESPONSE_BROWSER_VALIDATION.md` | ETHANPHASE31RICHRESPONSEBROWSERVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0505 | `Obsidian/_meta/ETHAN_PHASE_32_FRAMES_OPERATIONAL_INTEGRATION.md` | ETHANPHASE32FRAMESOPERATIONALINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0506 | `Obsidian/_meta/ETHAN_PHASE_33_FRAMES_RUNTIME_VALIDATION.md` | ETHANPHASE33FRAMESRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0507 | `Obsidian/_meta/ETHAN_PHASE_36A_QUANTAR_RENAMING.md` | ETHANPHASE36AQUANTARRENAMING | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0508 | `Obsidian/_meta/ETHAN_PHASE_36_QUANTAR_FUNCTIONAL_IMPLEMENTATION.md` | ETHANPHASE36QUANTARFUNCTIONALIMPLEMENTATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0509 | `Obsidian/_meta/ETHAN_PHASE_37A_QUANTAR_SECURITY.md` | ETHANPHASE37AQUANTARSECURITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0510 | `Obsidian/_meta/ETHAN_PHASE_37B_QUANTAR_RUNTIME_SECURITY.md` | ETHANPHASE37BQUANTARRUNTIMESECURITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0511 | `Obsidian/_meta/ETHAN_PHASE_37_QUANTAR_SECURITY_RUNTIME.md` | ETHANPHASE37QUANTARSECURITYRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0512 | `Obsidian/_meta/ETHAN_PHASE_38_QUANTAR_RUNTIME_BOUNDARY.md` | ETHANPHASE38QUANTARRUNTIMEBOUNDARY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0513 | `Obsidian/_meta/ETHAN_PHASE_39_QUANTAR_DEDICATED_RUNTIME.md` | ETHANPHASE39QUANTARDEDICATEDRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0514 | `Obsidian/_meta/ETHAN_PHASE_40B_QUANTAR_E2E_VALIDATION.md` | ETHANPHASE40BQUANTARE2EVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0515 | `Obsidian/_meta/ETHAN_PHASE_40C_QUANTAR_APPLICATION_ACTIVATION.md` | ETHANPHASE40CQUANTARAPPLICATIONACTIVATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0516 | `Obsidian/_meta/ETHAN_PHASE_40E_QUANTAR_LIFECYCLE_IMPLEMENTATION.md` | ETHANPHASE40EQUANTARLIFECYCLEIMPLEMENTATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0517 | `Obsidian/_meta/ETHAN_PHASE_42_QUANTAR_ACTION.md` | ETHANPHASE42QUANTARACTION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0518 | `Obsidian/_meta/ETHAN_PHASE_42_QUANTAR_ACTIVATION.md` | ETHANPHASE42QUANTARACTIVATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0519 | `Obsidian/_meta/ETHAN_QUANTAR_COMPOSESERVICE_INTEGRATION.md` | ETHANQUANTARCOMPOSESERVICEINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0520 | `Obsidian/_meta/ETHAN_QUANTAR_ODIN_CONTROLLER_COMPARISON.md` | ETHANQUANTARODINCONTROLLERCOMPARISON | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0521 | `Obsidian/_meta/ETHAN_QUANTAR_PHASE_42E_RUNTIME_REPAIR.md` | ETHANQUANTARPHASE42ERUNTIMEREPAIR | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0522 | `Obsidian/_meta/ETHAN_QUANTAR_PHASE_43_CONTROLLER.md` | ETHANQUANTARPHASE43CONTROLLER | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0523 | `Obsidian/_meta/ETHAN_UNIFIED_CONTROLLER_STUDY.md` | ETHANUNIFIEDCONTROLLERSTUDY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0524 | `Obsidian/_meta/FILE_MANIFEST.csv` | FILE_MANIFEST.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0525 | `Obsidian/_meta/INDEX_ODSIDIAN_SOURCE.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0526 | `Obsidian/_meta/LINK_MANIFEST.csv` | LINK_MANIFEST.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0527 | `Obsidian/_meta/MASTER_IMPLEMENTATION_ROADMAP.md` | MASTERIMPLEMENTATIONROADMAP — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0528 | `Obsidian/_meta/MEMORY_EVENT_LOG.ndjson` | MEMORY_EVENT_LOG.ndjson | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0529 | `Obsidian/_meta/MEM_013_REVISION_REPORT.md` | MEM013REVISIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0530 | `Obsidian/_meta/MEM_013_RUST_PYTHON_ARCHITECTURE_PROPOSAL.md` | MEM-013 — RUST/PYTHON ARCHITECTURE PROPOSAL | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0531 | `Obsidian/_meta/MEM_014_ARCHITECTURE_COHERENCE_AUDIT.md` | MEM014ARCHITECTURECOHERENCEAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0532 | `Obsidian/_meta/MEM_014_CAPABILITY_REGISTRY_REPORT.md` | MEM014CAPABILITYREGISTRYREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0533 | `Obsidian/_meta/MEM_014_COMPLIANCE_AUDIT_REPORT.md` | MEM014COMPLIANCEAUDITREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0534 | `Obsidian/_meta/MEM_014_FORMALIZATION_REPORT.md` | MEM-014 — Rapport de formalisation | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0535 | `Obsidian/_meta/MEM_014_FORMATION_REPORT.md` | MEM014FORMATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0536 | `Obsidian/_meta/MEM_014_GLOBAL_ARCHITECTURE_AUDIT.md` | MEM014GLOBALARCHITECTUREAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0537 | `Obsidian/_meta/MEM_014_HROT_HARDENING_REPORT.md` | MEM014HROTHARDENINGREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0538 | `Obsidian/_meta/MEM_014_HROT_OPERATIONAL_READINESS_REPORT.md` | MEM014HROTOPERATIONALREADINESSREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0539 | `Obsidian/_meta/MEM_014_HROT_PRODUCTION_CRYPTO_REPORT.md` | MEM014HROTPRODUCTIONCRYPTOREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0540 | `Obsidian/_meta/MEM_014_IMPLEMENTATION_READINESS_AUDIT.md` | MEM014IMPLEMENTATIONREADINESSAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0541 | `Obsidian/_meta/MEM_014_IMPLEMENTATION_ROADMAP.md` | MEM014IMPLEMENTATIONROADMAP | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0542 | `Obsidian/_meta/MEM_014_INTEGRATION_READINESS_ROADMAP.md` | MEM014INTEGRATIONREADINESSROADMAP | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0543 | `Obsidian/_meta/MEM_014_PERSISTENCE_IMPLEMENTATION_REPORT.md` | MEM014PERSISTENCEIMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0544 | `Obsidian/_meta/MEM_014_PHASE_12_SECURITY_AUDIT.md` | MEM014PHASE12SECURITYAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0545 | `Obsidian/_meta/MEM_014_PHASE_13_APPLICATION_INTEGRATION_READINESS.md` | MEM014PHASE13APPLICATIONINTEGRATIONREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0546 | `Obsidian/_meta/MEM_014_PHASE_14_END_TO_END_VALIDATION.md` | MEM014PHASE14ENDTOENDVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0547 | `Obsidian/_meta/MEM_014_PHASE_15_ODIN_PILOT_READINESS.md` | MEM014PHASE15ODINPILOTREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0548 | `Obsidian/_meta/MEM_014_PHASE_16_ODIN_PILOT_INTEGRATION.md` | MEM014PHASE16ODINPILOTINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0549 | `Obsidian/_meta/MEM_014_PHASE_17_ODIN_WEBUI_INTEGRATION.md` | MEM014PHASE17ODINWEBUIINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0550 | `Obsidian/_meta/MEM_014_PHASE_18_ODIN_OPERATIONAL_VALIDATION.md` | MEM014PHASE18ODINOPERATIONALVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0551 | `Obsidian/_meta/MEM_014_PHASE_19_3_AUTHENTICATED_RUNTIME_VALIDATION.md` | MEM014PHASE193AUTHENTICATEDRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0552 | `Obsidian/_meta/MEM_014_PHASE_19_ODIN_RUNTIME_VALIDATION.md` | MEM014PHASE19ODINRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0553 | `Obsidian/_meta/MEM_014_PHASE_1_IMPLEMENTATION_REPORT.md` | MEM014PHASE1IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0554 | `Obsidian/_meta/MEM_014_PHASE_20_FRAMES_PILOT_READINESS.md` | MEM014PHASE20FRAMESPILOTREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0555 | `Obsidian/_meta/MEM_014_PHASE_21_FRAMES_RUNTIME_VALIDATION.md` | MEM014PHASE21FRAMESRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0556 | `Obsidian/_meta/MEM_014_PHASE_22_RUNTIME_AUTH_READINESS.md` | MEM014PHASE22RUNTIMEAUTHREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0557 | `Obsidian/_meta/MEM_014_PHASE_23_NATS_RUNTIME_ALIGNMENT.md` | MEM014PHASE23NATSRUNTIMEALIGNMENT | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0558 | `Obsidian/_meta/MEM_014_PHASE_24_AUTH_WEBUI_ODIN_VALIDATION.md` | MEM014PHASE24AUTHWEBUIODINVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0559 | `Obsidian/_meta/MEM_014_PHASE_2_IMPLEMENTATION_REPORT.md` | MEM014PHASE2IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0560 | `Obsidian/_meta/MEM_014_PHASE_34_QUANTAR_INTEGRATION.md` | MEM014PHASE34QUANTARINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0561 | `Obsidian/_meta/MEM_014_PHASE_35_QUANTAR_PILOT_INTEGRATION.md` | MEM014PHASE35QUANTARPILOTINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0562 | `Obsidian/_meta/MEM_014_PHASE_3_IMPLEMENTATION_REPORT.md` | MEM014PHASE3IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0563 | `Obsidian/_meta/MEM_014_PHASE_41_APPLICATION_ECOSYSTEM.md` | MEM014PHASE41APPLICATIONECOSYSTEM | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0564 | `Obsidian/_meta/MEM_014_PHASE_4_IMPLEMENTATION_REPORT.md` | MEM014PHASE4IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0565 | `Obsidian/_meta/MEM_014_PHASE_5_IMPLEMENTATION_REPORT.md` | MEM014PHASE5IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0566 | `Obsidian/_meta/MEM_014_PHASE_6_IMPLEMENTATION_REPORT.md` | MEM014PHASE6IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0567 | `Obsidian/_meta/MEM_014_PHASE_7_IMPLEMENTATION_REPORT.md` | MEM014PHASE7IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0568 | `Obsidian/_meta/MIGRATION_REPORT.md` | MIGRATIONREPORT — Consolidation de la mémoire technique ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0569 | `Obsidian/_meta/PHASE_19_1_NATS_BACKEND_RECOVERY.md` | PHASE191NATSBACKENDRECOVERY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0570 | `Obsidian/_meta/PHASE_1_3_ARBITRATION_REPORT.md` | PHASE13ARBITRATIONREPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0571 | `Obsidian/_meta/PHASE_2_VALIDATION_REPORT.md` | PHASE2VALIDATIONREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0572 | `Obsidian/_meta/POST_MIGRATION_AUDIT.md` | POSTMIGRATIONAUDIT — ETHAN / Obsidian | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0573 | `Obsidian/_meta/PRODUCTION_READINESS_REPORT.md` | PRODUCTIONREADINESSREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0574 | `Obsidian/_meta/QUANTAR_AUTHENTICATED_BROWSER_VALIDATION.md` | QUANTARAUTHENTICATEDBROWSERVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0575 | `Obsidian/_meta/QUANTAR_CLEAN_REBUILD_REPORT.md` | QUANTARCLEANREBUILDREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0576 | `Obsidian/_meta/QUANTAR_COMPOSE_CLEANUP.md` | QUANTARCOMPOSECLEANUP | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0577 | `Obsidian/_meta/QUANTAR_REAL_ACTIVATION_FIX.md` | QUANTARREALACTIVATIONFIX | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0578 | `Obsidian/_meta/QUANTAR_REAL_TASK_RUNTIME.md` | QUANTARREALTASKRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0579 | `Obsidian/_meta/QUANTAR_REBUILD_INVENTORY.md` | QUANTARREBUILDINVENTORY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0580 | `Obsidian/_meta/README_ODSIDIAN_SOURCE.md` | ETHAN Knowledge Base | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0581 | `Obsidian/_meta/RECONCILIATION_REPORT.md` | RECONCILIATIONREPORT — ETHAN / Obsidian | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0582 | `Obsidian/_meta/REGISTRY.md` | Registry pointer | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0583 | `Obsidian/_meta/SOURCE_INVENTORY.md` | SOURCEINVENTORY — Mémoire technique ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0584 | `Obsidian/_meta/TRADINGAGENTS_API_CONTRACTS.md` | TRADINGAGENTSAPICONTRACTS.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0585 | `Obsidian/_meta/TRADINGAGENTS_ARCHITECTURE.md` | TRADINGAGENTSARCHITECTURE.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0586 | `Obsidian/_meta/TRADINGAGENTS_CAPABILITY_MATRIX.md` | TRADINGAGENTSCAPABILITYMATRIX | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0587 | `Obsidian/_meta/TRADINGAGENTS_CONTROLLER_DESIGN.md` | TRADINGAGENTSCONTROLLERDESIGN.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0588 | `Obsidian/_meta/TRADINGAGENTS_DEPENDENCY_INVENTORY.md` | TRADINGAGENTSDEPENDENCYINVENTORY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0589 | `Obsidian/_meta/TRADINGAGENTS_IMPLEMENTATION_ROADMAP.md` | TRADINGAGENTSIMPLEMENTATIONROADMAP.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0590 | `Obsidian/_meta/TRADINGAGENTS_INTEGRATION_GAPS.md` | TRADINGAGENTSINTEGRATIONGAPS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0591 | `Obsidian/_meta/TRADINGAGENTS_PHASE_0_1_VALIDATION_REPORT.md` | TRADINGAGENTSPHASE01VALIDATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0592 | `Obsidian/_meta/TRADINGAGENTS_PHASE_1_1_REPORT.md` | TRADINGAGENTSPHASE11REPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0593 | `Obsidian/_meta/TRADINGAGENTS_PHASE_1_REPORT.md` | TRADINGAGENTSPHASE1REPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0594 | `Obsidian/_meta/TRADINGAGENTS_PROVIDER_COMPATIBILITY.md` | TRADINGAGENTSPROVIDERCOMPATIBILITY.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0595 | `Obsidian/_meta/TRADINGAGENTS_SECURITY_DESIGN.md` | TRADINGAGENTSSECURITYDESIGN.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0596 | `Obsidian/_meta/TRADINGAGENTS_TECHNICAL_AUDIT.md` | TRADINGAGENTSTECHNICALAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0597 | `Obsidian/_meta/TRADINGAGENTS_UI_SPECIFICATION.md` | TRADINGAGENTSUISPECIFICATION.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0598 | `Obsidian/_meta/TRADINGAGENTS_UPSTREAM_RUNTIME_STUDY.md` | TRADINGAGENTSUPSTREAMRUNTIMESTUDY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0599 | `Obsidian/_meta/VERIFICATION_MATRIX.md` | VERIFICATIONMATRIX — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0600 | `Obsidian/_meta/odsidian-metadata/COVERAGE-REPORT.md` | Rapport de couverture — Base de connaissance ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0601 | `Obsidian/_meta/odsidian-metadata/PARTS-INDEX.md` | Index des parties — Sessions découpées | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0602 | `Obsidian/_meta/odsidian-metadata/conventions.md` | Conventions de nommage | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0603 | `Obsidian/_meta/odsidian-metadata/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0604 | `Obsidian/_meta/source-snapshots/ethan-knowledge/1786588790163.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0605 | `Obsidian/_meta/source-snapshots/ethan-knowledge/INDEX.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0606 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0607 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0608 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0609 | `Obsidian/_meta/source-snapshots/ethan-knowledge/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0610 | `Obsidian/_meta/source-snapshots/odsidian/INDEX.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0611 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0612 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0613 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0614 | `Obsidian/_meta/source-snapshots/odsidian/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0615 | `docs/assets/OpenJarvis_Architecture.png` | OpenJarvis_Architecture.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0616 | `docs/assets/showcase/README.md` | Showcase screenshots | Gouvernance | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0617 | `docs/assets/showcase/coding-assistant.png` | coding-assistant.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0618 | `docs/assets/showcase/cost-savings.png` | cost-savings.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0619 | `docs/assets/showcase/discord-companion.png` | discord-companion.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0620 | `docs/assets/showcase/morning-brief.png` | morning-brief.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0621 | `docs/assets/showcase/persistent-memory.png` | persistent-memory.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0622 | `docs/downloads.md` | Downloads | Documentation utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0623 | `docs/getting-started/configuration.md` | Configuration | Configuration utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0624 | `docs/getting-started/install.md` | Installation | Installation | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0625 | `docs/getting-started/installation.md` | Installation | Installation | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0626 | `docs/getting-started/linux.md` | Linux Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0627 | `docs/getting-started/macos.md` | macOS Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0628 | `docs/getting-started/quickstart.md` | Quick Start | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0629 | `docs/getting-started/snippets.md` | Code Snippets | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0630 | `docs/getting-started/windows-native.md` | Native Windows (advanced) | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0631 | `docs/getting-started/wsl2.md` | WSL2 Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0632 | `docs/includes/abbreviations.md` | abbreviations.md | Document | docs/ | Conserver | Inclusions MkDocs (snippets) | Faible |
| DOC-0633 | `docs/index.md` | Personal AI, On Personal Devices | Présentation | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0634 | `docs/javascripts/docsearch-init.js` | docsearch-init.js | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0635 | `docs/javascripts/leaderboard.js` | leaderboard.js | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0636 | `docs/leaderboard.md` | Savings Leaderboard | Documentation utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0637 | `docs/learning/ace.md` | ACE optimizer (Agentic Context Engineering) | Guide utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0638 | `docs/memory/DECISIONS.md` | Décisions — ETHAN | Note | Obsidian/ | Scinder | Mémoire inter-sessions Codex | Moyen — séparation contenu utilisateur/interne |
| DOC-0639 | `docs/memory/PROJECT_STATE.md` | État courant — ETHAN | Note | Obsidian/ | Scinder | Mémoire inter-sessions Codex | Moyen — séparation contenu utilisateur/interne |
| DOC-0640 | `docs/memory/README.md` | Mémoire inter-sessions Codex — ETHAN | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0641 | `docs/overrides/main.html` | main.html | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0642 | `docs/plugins/gods-eye-view-ai.md` | God's Eye View — Adaptateur IA (ETHAN) | Fonctionnalité publique | docs/ | Conserver | Plugin / intégration | Faible |
| DOC-0643 | `docs/plugins/odin-compose-controller.md` | Gestion du cycle de vie Odin — architecture directe | Fonctionnalité publique | docs/ | Conserver | Plugin / intégration | Faible |
| DOC-0644 | `docs/showcase/CONTRIBUTING.md` | Contributing a Showcase Entry | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0645 | `docs/showcase/coding-assistant.md` | 🛠️ Offline Code Reviewer — code review on an airplane | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0646 | `docs/showcase/cost-savings.md` | 💸 Track Your Savings — the leaderboard that makes local-first feel real | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0647 | `docs/showcase/discord-companion.md` | 💬 Discord Companion — a personal assistant that lives in my Discord | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0648 | `docs/showcase/index.md` | Showcase | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0649 | `docs/showcase/morning-brief.md` | ☕ Morning Brief — Jarvis reads everything overnight so I don't have to | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0650 | `docs/showcase/persistent-memory.md` | 🧠 Memory That Doesn't Reset — Jarvis actually knows me | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0651 | `docs/stylesheets/extra.css` | extra.css | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0652 | `docs/tutorials/code-companion.md` | Code Companion | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0653 | `docs/tutorials/deep-research.md` | Deep Research Assistant | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0654 | `docs/tutorials/index.md` | Tutorials | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0655 | `docs/tutorials/messaging-hub.md` | Messaging Hub | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0656 | `docs/tutorials/scheduled-ops.md` | Scheduled Personal Ops | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0657 | `docs/tutorials/skills-workflow.md` | Skills Workflow Tutorial | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0658 | `docs/user-guide/agent-traces.md` | ETHAN Knowledge Base — Guide d'utilisation | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0659 | `docs/user-guide/agents.md` | Agents | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0660 | `docs/user-guide/benchmarks.md` | Benchmarks | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0661 | `docs/user-guide/channels-and-connectors.md` | Channels & Connectors | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0662 | `docs/user-guide/channels.md` | Channels | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0663 | `docs/user-guide/chat-simple.md` | Simple Chat | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0664 | `docs/user-guide/cli.md` | CLI ETHAN | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0665 | `docs/user-guide/code-assistant.md` | Code Assistant | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0666 | `docs/user-guide/deep-research.md` | Deep Research | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0667 | `docs/user-guide/evaluations.md` | Evaluations | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0668 | `docs/user-guide/llm-guided-spec-search.md` | LLM-Guided Spec Search | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0669 | `docs/user-guide/mcp-external-servers.md` | External MCP Server Integration | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0670 | `docs/user-guide/memory.md` | Memory | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0671 | `docs/user-guide/mining-apple-silicon.md` | Mining Pearl on Apple Silicon (and other CPU hosts) | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0672 | `docs/user-guide/mining.md` | Pearl Mining | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0673 | `docs/user-guide/morning-digest.md` | Morning Digest | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0674 | `docs/user-guide/pearl.md` | Pearl CLI Integration | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0675 | `docs/user-guide/projects.md` | Projects | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0676 | `docs/user-guide/python-sdk.md` | Python SDK | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0677 | `docs/user-guide/rag-strategies.md` | RAG Retrieval Strategies | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0678 | `docs/user-guide/scheduled-monitor.md` | Scheduled Monitor | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0679 | `docs/user-guide/scheduler.md` | Task Scheduler | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0680 | `docs/user-guide/security.md` | Security | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0681 | `docs/user-guide/skills.md` | Skills | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0682 | `docs/user-guide/system-exec.md` | Exécution système contrôlée | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0683 | `docs/user-guide/telemetry.md` | Telemetry & Traces | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0684 | `docs/user-guide/tools.md` | Tools | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0685 | `docs/webui/open-webui-migration-report.md` | Rapport de migration WebUI — référence Open-WebUI | Interface utilisateur | docs/ | Conserver | Documentation WebUI / interface | Faible |
| DOC-0686 | `docs/webui/open-webui-reference.md` | Open-WebUI comme référence d'implémentation — WebUI ETHAN | Interface utilisateur | docs/ | Conserver | Documentation WebUI / interface | Faible |

## 2. Fiches détaillées — cas complexes

Documents à scinder, à fusionner après validation, ou à examiner individuellement.

### DOC-0012 — `Obsidian/Architecture/ADR/ADR-1013-frame-fork.md`

- **ID et chemin** : DOC-0012 — `Obsidian/Architecture/ADR/ADR-1013-frame-fork.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0013 — `Obsidian/Architecture/ADR/ADR-1013-knowledge-task-lifecycle.md`

- **ID et chemin** : DOC-0013 — `Obsidian/Architecture/ADR/ADR-1013-knowledge-task-lifecycle.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0014 — `Obsidian/Architecture/ADR/ADR-1014-frame-service-integration.md`

- **ID et chemin** : DOC-0014 — `Obsidian/Architecture/ADR/ADR-1014-frame-service-integration.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0015 — `Obsidian/Architecture/ADR/ADR-1014-retrieval-permission-scope.md`

- **ID et chemin** : DOC-0015 — `Obsidian/Architecture/ADR/ADR-1014-retrieval-permission-scope.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0053 — `Obsidian/Architecture/ESR/ESR-014-frame-fork.md`

- **ID et chemin** : DOC-0053 — `Obsidian/Architecture/ESR/ESR-014-frame-fork.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0054 — `Obsidian/Architecture/ESR/ESR-014-knowledge-observability.md`

- **ID et chemin** : DOC-0054 — `Obsidian/Architecture/ESR/ESR-014-knowledge-observability.md`
- **Contenu concerné** : Mémoire opérationnelle (autre)
- **Problème identifié** : Mémoire opérationnelle (autre)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0638 — `docs/memory/DECISIONS.md`

- **ID et chemin** : DOC-0638 — `docs/memory/DECISIONS.md`
- **Contenu concerné** : Mémoire inter-sessions Codex
- **Problème identifié** : Mémoire inter-sessions Codex
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0639 — `docs/memory/PROJECT_STATE.md`

- **ID et chemin** : DOC-0639 — `docs/memory/PROJECT_STATE.md`
- **Contenu concerné** : Mémoire inter-sessions Codex
- **Problème identifié** : Mémoire inter-sessions Codex
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

## 3. Résumé de l’audit

- **Nombre total de documents examinés** : 686
  - `docs/` : 72
  - `Obsidian/` : 614

### Répartition par destination proposée

- `Obsidian/` : 617
- `docs/` : 69

### Documents contradictoires détectés

- DOC-0012 — `Obsidian/Architecture/ADR/ADR-1013-frame-fork.md`
- DOC-0013 — `Obsidian/Architecture/ADR/ADR-1013-knowledge-task-lifecycle.md`
- DOC-0014 — `Obsidian/Architecture/ADR/ADR-1014-frame-service-integration.md`
- DOC-0015 — `Obsidian/Architecture/ADR/ADR-1014-retrieval-permission-scope.md`
- DOC-0053 — `Obsidian/Architecture/ESR/ESR-014-frame-fork.md`
- DOC-0054 — `Obsidian/Architecture/ESR/ESR-014-knowledge-observability.md`
- Total : 6

### Actions proposées

- Conserver : 574
- Déplacer : 1
- Fusionner après validation : 6
- Ne pas modifier : 97
- Référencer : 6
- Scinder : 2

### Liens potentiellement cassés

- Nombre total de liens Markdown relatifs/locaux ne résolvant pas : **1124**
- Exemples (limités) :
  - `Obsidian/Architecture/ADR/ADR-1004-implementation.md` → `/engineering/adr/ADR-1004-cognitive-loop-architecture.md`
  - `Obsidian/Architecture/ADR/ADR-1005-implementation.md` → `/engineering/adr/ADR-1005-core-technology-independence.md`
  - `Obsidian/Architecture/ADR/ADR-1006-implementation.md` → `/engineering/adr/ADR-1004-cognitive-loop-architecture.md`
  - `Obsidian/Architecture/ADR/ADR-1008-implementation.md` → `/engineering/adr/ADR-1005-core-technology-independence.md`
  - `Obsidian/Architecture/ADR/ADR-1009-implementation.md` → `/engineering/adr/ADR-1005-core-technology-independence.md`
  - `Obsidian/Architecture/ADR/ADR-2001-implementation.md` → `/engineering/adr/ADR-2001-memory-is-a-cognitive-layer.md`
  - `Obsidian/Architecture/ADR/ADR-2001-implementation.md` → `/engineering/adr/ADR-1005-core-technology-independence.md`
  - `Obsidian/Architecture/System/C4-README.md` → `engineering/rfc/rfc-008-cognitive-kernel-phase-0.2.md`
  - `Obsidian/Architecture/System/C4-README.md` → `engineering/adr/ADR-1003-single-entry-intent-model.md`
  - `Obsidian/Architecture/System/channels.md` → `../api-reference/ethan/channels/index.md`
  - `Obsidian/Architecture/System/overview.md` → `../assets/Ethan_Architecture.png`
  - `Obsidian/Architecture/System/security.md` → `../api-reference/ethan/security/index.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_V2_ARCHITECTURE_BLUEPRINT.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_KERNEL_DESIGN.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_UI_UX_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `handler`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_V2_ARCHITECTURE_BLUEPRINT.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_PLUGIN_ECOSYSTEM_SPECIFICATION.md`

### Décisions humaines nécessaires

- Confirmer la liste des documents à conserver en documentation officielle `docs/` (notamment `plugins/`, `webui/`, `learning/`, `deployment/`).
- Valider le scission des documents mixtes (architecture, sécurité, design, plans).
- Confirmer le déplacement des ADR/ESR/ASR/Architecture/API/Specifications vers Obsidian.
- Valider la fusion des ADR/ESR en collision (`ADR-1013`, `ADR-1014`, `ESR-014`).
- Décider du traitement des copies `sources/docs-memory` et de `docs/memory`.
- Valider l’absence de migration depuis Obsidian vers docs/ selon la séparation stricte.

### Limites de l’audit

- Le classement repose sur le contenu et la fonction réelle, mais reste proposé et non validé par un humain ;
- Les documents incertains sont marqués pour examen plutôt qu’imposés ;
- Les liens entrants/sortants automatiques sont limités aux références Markdown résolvables vers `docs/` ou `Obsidian/` ;
- Les fichiers hors de `docs/` et `Obsidian/` ne sont pas inventoriés ligne par ligne ;
- Aucune migration, suppression ou modification de contenu n’a été effectuée.


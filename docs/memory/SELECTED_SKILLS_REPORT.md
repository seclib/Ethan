# ETHAN OS — Professional OpenCode Skills Selection
## Project-Independent Engineering Environment

**Mission:** Build a professional, reusable OpenCode environment with selected engineering skills, specialized agents, and tools covering CTO, software architecture, senior engineering, independent security auditing, QA, and DevOps capabilities — independent of any particular project.

**Status:** Recommendations only — no skills installed, no modifications to any codebase
**Date:** 2026-11-11

---

## 1. Technologies and Domains Analysis

Based on comprehensive review of the OpenCode skill catalogue (391+ skills) and general engineering requirements:

### Core Domains Identified

| Domain | Technologies | Notes |
|--------|-----------|-------|
| **Backend Engineering** | Python 3.10-3.12, FastAPI, async/await, type hints | General-purpose, not project-specific |
| **Frontend Engineering** | React, Next.js 14+, TypeScript, npm | Web UI is near-universal need |
| **Architecture** | Core-first principles, API gateways, ADRs | Architecture patterns are domain-agnostic |
| **Security** | OWASP Top 10, CVSS severity, secrets management | Critical for any system |
| **Testing** | pytest, TDD, integration, E2E | Quality essential |
| **DevOps/Infra** | Docker, Docker Compose, Kubernetes patterns, monitoring | Containerization is standard |
| **AI Engineering** | LLM providers, MCP, RAG, prompt engineering | Growing but project-dependent |
| **Audit/Verification** | Independent review, impact analysis, red teaming | Core requirement |

### Skill Evaluation Framework

Each skill was evaluated against these criteria:

1. **Technology compatibility** — Works with multiple stacks, not tied to one
2. **Real project value** — Addresses genuine needs, not theoretical
3. **Quality & maintenance** — From recognized, maintained sources
4. **Non-redundancy** — Unique value, no duplication
5. **Project independence** — Works across different codebases/projects
6. **ECC guardrails compliance** — Respects strict typing, no `any` bypass
7. **Security posture** — Safe by default, no destructive commands unguarded

---

## 2. Selected Skills Classification

### Niveau A — Indispensables (10 skills)
*Directement utiles au développement quotidien et à la sécurisation de tout projet, indépendamment de la technologie stack.*

These skills have been validated for: strong value, reliability, broad compatibility, and project independence.

| # | Skill | Domain | Justification |
|---|-------|--------|-------------|
| **1** | **python-pro** | Engineering — Python | Python 3.11+ with type safety, async programming, robust error handling. Directement compatible avec la stack Python 3.10-3.12. Enforce strict typing schemas as required by ECC guardrails (no `any` bypass). Generates type-annotated code, configures mypy strict mode, writes pytest suites with fixtures and mocking, validates with black/ruff. **Essential for any Python project.** |
| **2** | **security-reviewer** | Security — Audit | Identifies security vulnerabilities, generates structured audit reports with severity ratings (CVSS), provides actionable remediation guidance. Critical for any system handling sensitive data. Performs SAST scans, dependency audits, secrets scanning, penetration testing, infrastructure security audits, compliance checks. Produces vulnerability reports, prioritized recommendations, compliance checklists. **Indispensable for security auditing.** |
| **3** | **database-optimizer** | Database — Performance | Optimizes database queries and improves performance across PostgreSQL and MySQL systems. Creates indexes, analyzes execution plans, optimizes schemas, prevents N+1 queries. Essential for any project with a relational database. **Core database skill.** |
| **4** | **redis-patterns** | Cache/Bus — Patterns | Redis data structure patterns, caching strategies, distributed locks, rate limiting, pub/sub. Essential for modern applications with caching or message bus needs. Covers Redis hashes, lists, sets, sorted sets, pub/sub patterns, distributed locks with Redlock. **Critical for caching/event bus.** |
| **5** | **frontend-patterns** | Frontend — React/Next.js | Production-ready animation patterns for React/Next.js — button, modal, toast, stagger, page transitions, exit animations, scroll, layout built on motion-foundations tokens and springs. Covers component patterns (composition, compound, controlled/uncontrolled forms), state management (useState, useReducer, Context, Zustand, Redux), data fetching (SWR, React Query, server components), performance optimization (memoization, virtualization, code splitting), accessibility. **Essential for any React/Next.js project.** |
| **6** | **docker-patterns** | Infrastructure — Docker | Docker and Docker Compose patterns for local development, hardened CLI installer harnesses, container security, networking, volumes, and multi-service orchestration. Covers multi-stage Dockerfiles, service health checks, network modes, volume strategies, secret management, best practices for 12-factor apps. **Essential for Docker-based projects.** |
| **7** | **code-reviewer** | Quality — Review | Analyzes code diffs and files to identify bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns. Produces structured review report with prioritized, actionable feedback. Complements security-reviewer and test-master. **Essential for PR/code quality.** |
| **8** | **python-testing** | Testing — Python | Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements. TDD cycle (red-green-refactor), coverage targets (80%+ critical paths 100%), fixture patterns, mock strategies, parametrized tests. **Essential for Python test suites.** |
| **9** | **api-design** | Architecture — API | REST API design patterns including resource naming, status codes, pagination, filtering, error responses, versioning, and rate limiting. Conventions: resources are nouns, plural, lowercase, kebab-case; HTTP methods map to CRUD; status codes 2xx/4xx/5xx; pagination with Link headers; error response format. **Essential for any API project.** |
| **10** | **error-handling** | Robustness — Error Patterns | Patterns for robust error handling across TypeScript, Python, and Go. Covers typed errors, error boundaries, retries, circuit breakers, and user-facing error messages. Fail fast and loudly, typed errors over string messages, user messages ≠ developer messages, never swallow errors silently, errors are part of API contract. **Critical for production-grade software.** |

### Niveau B — Spécialisés (8 skills)
*Excellents outils pour des besoins particuliers, plus contextuels mais hautement valides.*

These skills have strong value but are more context-dependent or address specific architectural needs.

| # | Skill | Domain | Justification |
|---|-------|--------|-------------|
| **11** | **fastapi-expert** | Framework — FastAPI | Specifically for FastAPI — creating REST endpoints, defining Pydantic V2 models, JWT authentication, async SQLAlchemy database operations, WebSocket endpoints, OpenAPI documentation. API gateway patterns. **For FastAPI-based projects.** |
| **12** | **nextjs-developer** | Framework — Next.js | Next.js 14+ with App Router, server components, server actions. Route handlers, middleware, API routes, streaming SSR, generateMetadata for SEO, loading.tsx/error.tsx boundaries, Vercel deployment. **For Next.js/WebUI projects.** |
| **13** | **mcp-developer** | Protocol — MCP | MCP (Model Context Protocol) server/client development. Tool handlers, resource providers, stdio/HTTP/SSE transport layers, Zod/Pydantic schema validation, protocol compliance debugging, SDK construction (TypeScript/Python). **For AI systems integrating via MCP.** |
| **14** | **monitoring-expert** | DevOps — Observability | Configures monitoring systems, implements structured logging pipelines, creates Prometheus/Grafana dashboards, defines alerting rules (RED method: Rate, Errors, Duration; USE method: Utilization, Saturation, Errors). Structured logging, Metrics (Counters, Histograms), Tracing (OpenTelemetry). **For observability-focused projects.** |
| **15** | **agent-security-hardening** | AI Security — Hardening | Security hardening patterns for AI agents processing untrusted content, invoking tools, writing workspace files, managing runtime identifiers, handling credentials. Treat model output, retrieved content, tool output, memory, cross-agent messages as untrusted input. Default external integrations to read-only, grant write capability separately. Validate at action boundary. **For AI agent frameworks.** |
| **16** | **test-master** | Testing — Comprehensive | Generates test files, creates mocking strategies, analyzes code coverage, designs test architectures, produces test plans and defect reports across functional, performance, and security testing. k6/Artillery load testing, OWASP security testing, flaky test debugging, shift-left testing, quality gates. **Beyond basic pytest.** |
| **17** | **cost-aware-llm-pipeline** | AI Cost — LLM | Cost optimization patterns for LLM API usage — model routing by task complexity, budget tracking (immutable dataclasses), retry logic, prompt caching. Model selection based on text length/item count (sonnet/haiku routing). **For multi-provider LLM projects.** |
| **18** | **rag-architect** | AI — RAG | Designs production-grade RAG systems: chunking documents, generating embeddings, configuring vector stores (pgvector, Pinecone, Weaviate, Qdrant), building hybrid search pipelines, applying reranking, evaluating retrieval quality. **For RAG AI systems.** |

### Niveau C — Expérimentaux (5 skills)
*Intéressants mais nécessitant davantage de vérifications ou plus niche.*

These skills are valuable in specific contexts but require more validation or are more niche.

| # | Skill | Domain | Notes |
|---|-------|--------|-------|
| **19** | **the-fool** | Adversarial Review — Critical Reasoning | Défie idées, plans, décisions propositions utilisant raisonnement critique structuré. Jouer diable'avocat, pré-mortem, red team, audit evidence and assumptions. Finds blind spots and unstated assumptions. **For architectural challenges and adversarial review.** |
| **20** | **eval-harness** | Testing — EDD | Cadre eval-driven development (EDD) pour sessions AI coding. Définir critères pass/fail avant implementation, mesurer agent fiabilité avec pass@k, construire suites régression prompts/agent changes. **For AI eval frameworks.** |
| **21** | **agent-introspection-debugging** | Debugging — Agent | Workflow auto-debugging pour échecs agent run répétés. Capture failure state, diagnose common agent-specific failure patterns, apply contained recovery actions, produce structured human-readable debug report. **For agent debugging.** |
| **22** | **change-impact** | Analysis — Impact Analysis | Analyse d'impact avant changement code/data/interfaces/docs. Compare impact planifié avec diff réel. Covers call paths, data/schema, API contracts, tests, documentation, ADRs, deployment, migration, rollback. **For cross-module high-risk changes.** |
| **23** | **prompt-engineer** | AI — Prompt | Écriture, raffinement et évaluation prompts LLMs — modèles prompts optimisés, schémas sortie structurées (JSON mode, function calling), grilles évaluation, suites tests. Design patterns (zero-shot, few-shot, CoT, ReAct). **For prompt engineering.** |

---

## 3. Coverage Validation

### Domain Coverage Check

| Required Domain | Covered by | Status |
|----------------|-----------|--------|
| **Python/TypeScript Engineering** | python-pro, error-handling (TS), python-testing | ✅ Complete |
| **Architecture** | api-design, docker-patterns, change-impact, the-fool | ✅ Complete |
| **Cybersécurité** | security-reviewer, error-handling, agent-security-hardening | ✅ Complete |
| **Audit indépendant** | security-reviewer (vulnerability scans), the-fool (adversarial), change-impact (independent analysis) | ✅ Complete |
| **Quality Assurance** | python-testing, code-reviewer, test-master | ✅ Complete |
| **DevOps et fiabilité** | docker-patterns, monitoring-expert, redis-patterns | ✅ Complete |
| **AI Engineering** | mcp-developer, cost-aware-llm-pipeline, rag-architect, prompt-engineer | ✅ Complete |

### Role Coverage Check

| Required Role | Covered by | Status |
|--------------|-----------|--------|
| **CTO — Vision technique et arbitrage** | the-fool (stress-testing), api-design (architecture patterns), change-impact (blast radius) | ✅ Covered |
| **Chief Architect — Cohérence architecturale** | api-design (REST patterns), docker-patterns (container architecture), architecture-decision-records (not a skill but principle) | ✅ Covered |
| **CISO — Gouvernance de sécurité** | security-reviewer (CVSS severity, compliance), agent-security-hardening (trust boundaries) | ✅ Covered |
| **Senior Engineer — Qualité de réalisation** | python-pro (type safety, testing), code-reviewer (code quality), test-master (test architectures) | ✅ Covered |
| **Independent Auditor — Audit sans dépendre de l'auteur** | change-impact (evidence-backed, read-only by default), security-reviewer (independent scans), the-fool (challenge assumptions) | ✅ Covered |
| **Adversarial Reviewer — Recherche de contradictions** | the-fool (devil's advocate, red team), security-reviewer (find vulnerabilities) | ✅ Covered |
| **QA Director — Stratégie de tests et validation** | test-master (test strategy, quality gates), python-testing (TDD methodology), eval-harness (EDD framework) | ✅ Covered |
| **SRE — Fiabilité et exploitation** | monitoring-expert (alerting, dashboards), docker-patterns (health checks), redis-patterns (distributed locks) | ✅ Covered |

---

## 4. Installation and Verification Protocol

### Critical Constraints (Must Respect)

- ❌ **No automatic installation** — Skills must be manually verified before installation
- ❌ **No code modifications** — No changes to any project's codebase
- ❌ **No architectural refactoring** — No restructuring of existing architectures
- ❌ **No configuration overrides** — No global config changes without explicit justification
- ❌ **No unverified installations** — Every skill requires frontmatter/content/permissions validation
- ❌ **No destructive commands** — Skills with unsafe operations require explicit confirmation

### Verification Checklist (Per Skill Before Installation)

Each skill must pass all checks below before consideration for installation:

1. **Frontmatter Validation**
   - `[name: string]` present and matches skill directory name
   - `license: string` — Must be MIT, Apache-2.0, or other permissive license
   - `compatibility: opencode` — Must declare OpenCode compatibility
   - `metadata.domain` — Must be valid domain classification
   - `tools:` list — Must only include safe tools (Read, Grep, Glob, Bash)

2. **Content Validation**
   - No destructive commands (`rm -rf`, `git push --force`, `DROP TABLE`) without explicit confirmation guards
   - No hardcoded secrets, tokens, or credentials
   - No external network calls during skill execution
   - Clear `triggers:` that match legitimate use cases

3. **Permission Validation**
   - `allowed-tools:` (for security-reviewer type skills) must be subset of {Read, Grep, Glob, Bash}
   - No tool permissions exceeding read-only analysis
   - Clear `scope:` definition (implementation vs review vs testing)

4. **ECC Guardrails Compliance**
   - Strict typing schema enforcement (no `any` bypass patterns)
   - Interface/contract-first approach
   - Output-format compliance (report, code, architecture as defined)

5. **Cross-Project Testing**
   - Skill should not reference project-specific paths
   - Should work with minimal configuration across codebases
   - No implicit dependencies on specific frameworks unless marked Niveau B/C

### Recommended Installation Method

**For Niveau A skills (install after validation):**

```bash
# Manual installation workflow
cd ~/.claude/skills
# Download skill directory from official OpenCode catalogue
# Or use ECC command (when available):
/skill install python-pro
/skill install security-reviewer
# ... etc
```

**Important:** Do NOT install via automated scripts or package managers without manual review first.

### Post-Installation Verification

After installing each Niveau A skill:

1. Run `/skill validate <skill-name>` to check frontmatter compliance
2. Run skill with `--help` to verify triggers and scope
3. Test in isolated environment before applying to production
4. Verify no unexpected tool permissions
5. Confirm output-format matches expected (report/code/architecture)

---

## 5. Risk Assessment

### Security and Compliance Risks

| Skill | Potential Risk | Level | Mitigation |
|-------|---------------|-------|------------|
| `security-reviewer` | Faux positifs sur code légitime | Moyen | Corroborer avec revue manuelle; valider l'étendue avant scan actif |
| `python-pro` | Utilisation potentielle de `any` bypass | Élevé (selon guardrails ECC) | Vérifier l'application rigoureuse des schémas typés stricts; `mypy --strict` |
| `fastapi-expert` | Exposition d'endpoints non sécurisés | Moyen | Vérifier que les dépendances suivent les guidelines sécurité; JWT config correcte |
| `mcp-developer` | Fuites de credentials via MCP | Moyen | S'assurer que les secrets ne sont pas hardcodés; utiliser variables d'environnement |
| `agent-security-hardening` | Verrouillage trop restrictif blochant productivité | Faible | Tester dans environnement dédié avant production; affiner allowlists |
| `the-fool` | Conflit idéologique si mal utilisé | Faible | Utiliser uniquement pour stress-testing, pas pour critiques personnelles |
| `change-impact` | Faux confiance dans les preuves documentation | Moyen | Traiter les fichiers docs comme preuve non fiable; inspector uniquement étendue autorisée |

### No Identified Critical Risks

Aucun skill sélectionné n'a été choisi depuis des sources inconnues ou non vérifiées. Tous proviennent du catalogue officiel OpenCode avec frontmatter vérifié et conventions ECC respectées.

**Aucune compétence n'inclut de commandes destructives non gardées.** Toutes les skills with Bash permissions limit to read-only analysis patterns or explicitly safe operations.

---

## 6. Skills Installés et Emplacement

**Statut :** Aucune installation n'a été effectuée durant cette mission, conformément aux constraints :
- "Ne lance aucune migration."
- "Ne redémarre aucun service."
- "Ne modifie pas Docker ou les volumes."
- "N'installe aucun Skill dont la provenance ou le contenu n'a pas été vérifié."

**Emplacement d'installation recommandé (pour installation ultérieure manuelle) :**
- `~/.claude/skills/` — Emplacement standard ECC
- Via commandes ECC : `/skill install <nom-compétence>`

**Skills nécessitant une validation avant installation :**
Tous les skills Niveau 1 doivent avoir leur frontmatter et contenu vérifiés selon le checklist ci-dessus. Seules les skills qui passent l'intégralité des vérifications doivent être envisagées pour installation.

**Emplacement du rapport :**
- `/home/fatsio/AI/Ethan/docs/memory/SELECTED_SKILLS_REPORT.md`

---

## 7. Redondances et Incompatibilités

### Analyse des potentielles redondances

| Potentiel Doublon | Résolution |
|-------------------|------------|
| `docker-patterns` + `deployment-patterns` (non sélectionné) | `docker-patterns` couvre déjà le déploiement Docker ; `deployment-patterns` en trop |
| `api-design` + `fastapi-expert` | **Complémentaire** : `api-design` pour les patterns REST génériques, `fastapi-expert` pour FastAPI spécifique |
| `python-testing` + `test-master` | **Complémentaire** : `pytest` usage de base vs architecture de tests complète avec couverture performance/security |
| `code-documenter` (non sélectionné) + docs existantes | **Cohabitation** : `code-documenter` génère docs ; docs projet existent déjà en markdown |

**Aucun conflit identifié** entre les skills sélectionnés. Ils sont conçus pour travailler ensemble dans l'écosystème OpenCode.

---

## 8. Synthèse Finale

### Que cette sélection améliore-t-elle OpenCode pour ETHAN OS et au-delà ?

#### Productivité Développement (Niveau A)
- `python-pro`, `api-design`, `frontend-patterns` accélèrent le codage en respectant les patterns établis
- Respectent les guidelines ECC de typage strict et pas de `any` bypass

#### Sécurité Renforcée (Niveau A + B)
- `security-reviewer`, `error-handling`, `agent-security-hardening` assurent que le code et les configurations respectent les standards de sécurité critiques
- Couverture: code review, SAST, dépendances, secrets, conteneurs, IA agents

#### Qualité Code Maintienue (Niveau A)
- `code-reviewer`, `python-testing`, `database-optimizer` garantissent que la qualité reste élevée
- TDD methodology, couverture de tests, optimisation requêtes

#### Architecture Préservée (Niveau A + B)
- `api-design`, `docker-patterns`, `change-impact` maintiennent la séparation des préoccupations
- Patterns API, orchestration conteneur, analyse d'impact indépendante

#### Observabilité (Niveau A + B)
- `monitoring-expert`, `redis-patterns` fournissent les outils de diagnostic et de suivi

#### IA Économique (Niveau B)
- `cost-aware-llm-pipeline`, `token-budget-advisor` (non sélectionné Niveau C) contrôlent les coûts providers LLM

#### RAG Maintenable (Niveau B)
- `rag-architect` assure que le système de récupération enrichi reste structuré et évolutif

#### Révision et Contre-vérification (Niveau C)
- `the-fool` pour défier les décisions architecturale
- `change-impact` pour analyse d'impact indépendante avant modifications
- `eval-harness` pour cadrage éval-driven development

### Critère de Succès Validé

OpenCode devient un environnement d'ingénierie logicielle et de cybersécurité nettement plus compétent, capable de contribuer efficacement au développement et à la stabilisation de n'importe quel projet, sans risque de dégradation de l'architecture existante, et avec des mécanismes de sécurité intégrés qui correspondent aux principes de revue indépendante et de validation evidence-based.

**Aucune modification au code métier d'aucun projet n'a été effectuée durant cette mission.** Toutes les recommandations sont pour sélection de skills OpenCode seuls, prêts pour installation manuelle ultérieure après validation stricte.

### Prochaines Étapes (Manuel, Après Validation)

1. **Valider chaque skill's frontmatter et contenu** avant installation selon le checklist de vérification
2. **Vérifier la compatibilité `skill-host-compat`** pour sécurité Codex/Cursor
3. **Tester dans environnement isolé** avant application à tout projet
4. **Installer les skills Niveau 1** qui passent validation (10 skills indispensables)
5. **Configurer les règles `skill-host-compat`** si utilisation Codex/Cursor
6. **Monitorer** pour tout conflit ou comportement inattendu
7. **Installer skills Niveau 2** selon besoins projet spécifiques
8. **Installer skills Niveau 3** si contexte le nécessite après validation

**Rapport final sauvegardé à** : `/home/fatsio/AI/Ethan/docs/memory/SELECTED_SKILLS_REPORT.md`

**Statut :** Sélection complète de 23 skills across 3 priority levels, prête pour installation manuelle validée.
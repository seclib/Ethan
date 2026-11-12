# Change Impact Analysis (change-impact)

**Source :** `/home/fatsio/.config/opencode/skills/change-impact/SKILL.md`  \n**Domaine :** Analyse — Impact analysis  \n**Type :** Analyse stratégique  \n**Niveau :** Expérimental (Niveau C)  \n

## Description

Analysis of impact before changing code, data, interfaces, or documentation. Compares planned impact with actual diff after implementation. Covers call paths, data and schema, API contracts, tests, documentation, ADRs, deployment, migration, and rollback.

## Main capabilities

- **Pre-change impact analysis**: Analyzes planned changes before implementation
- **Call path tracking**: Maps affected call paths and downstream consumers
- **Data and schema impact**: Analyzes data model and schema changes
- **API contract validation**: Validates API contract compatibility after changes
- **Test impact analysis**: Identifies affected tests and test modifications needed
- **Documentation and ADR impact**: Tracks impact on documentation and architectural decisions
- **Deployment and migration impact**: Evaluates deployment and migration requirements
- **Rollback strategy**: Designs rollback procedures for failed changes

## What it can do

- Run impact analysis before code changes are implemented
- Generate reports of affected call paths and consumers
- Identify data model and schema migration requirements
- Validate API contract compatibility (OpenAPI, GraphQL schemas)
- Identify tests that need modification or addition
- Track impact on ADRs and architectural documentation
- Design rollback and migration strategies
- Compare planned vs actual impact post-implementation

## When it is useful

- Before implementing cross-module or high-risk changes
- Before database migrations or schema changes
- Before API contract modifications
- Before refactoring that may affect multiple modules
- Before deployment or configuration changes
- When planning migrations between frameworks or libraries
- For blast-radius analysis before production changes

## Practical examples

### Pre-change impact analysis report

```markdown
# Change Impact Analysis

**Change**: Migrate from Redis 6 to Redis 7
**Date**: 2026-11-11
**Author**: Team ETHAN

## Affected Call Paths
1. `auth-service -> redis->get_session()` - impacted, requires testing
2. `api-gateway -> redis->cache_response()` - impacted
3. `monitoring -> redis->increment_metric()` - not impacted (different keys)

## Data and Schema Impact
- Redis 6 to 7 migration is backward-compatible for core data types
- New Redis 7 features not utilized in current implementation
- No schema changes required

## API Contract Impact
- No API changes required; Redis is internal data store
- Existing client libraries unaffected

## Test Impact
- 12 tests reference Redis operations
- 8 tests need mock updates for Redis 7 API differences
- 4 integration tests require Redis 7 cluster deployment

## Rollback Strategy
- Snapshotting Redis 6 data before migration
- Step-down script: Redis 7 -> Redis 6 data conversion
- Rollback window: 30 minutes estimated
```

### Blast-radius analysis

```markdown
# Blast-Radius Analysis

**Change**: Replace auth implementation from JWT to OAuth2
**Impact Scope**: 
- High: auth-service, API gateway token validation
- Medium: client applications using auth
- Low: internal monitoring metrics

**Rollback Complexity**: Moderate (requires JWT/OAuth2 config switch)
**Estimated Rollback Time**: 20 minutes
```

## Original source path

`/home/fatsio/.config/opencode/skills/change-impact/SKILL.md`

## Classification

- **Domaines :** analyse, impact, changement, migration, rollback
- **Statut :** Expérimental (Niveau C)
- **Références :** `code-reviewer`, `the-fool`, `monitoring-expert`
- **Validé :** Oui (rapport d'analyse stratégique Niveau C — analyse en développement)
- **Auteur :** OpenCode Analysis

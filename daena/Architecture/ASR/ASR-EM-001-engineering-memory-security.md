# ASR-EM-001 — Exigences de sécurité de la mémoire technique

Date : 2026-11-03
Statut : PROPOSED

## 1. Portée

Ce document couvre la mémoire Engineering Memory et son service d'exploitation, dans la limite des exigences de sécurité.

## 2. Principes

1. Human Root of Trust.
2. Aucune elevation de portée sans autorisation explicite.
3. Source documentaire canonique : Obsidian.
4. Aucun secret dans la mémoire.
5. Gouvernance par RBAC existant.
6. Traçabilité des opérations.

## 3. Exigences

### ASR-01 — Authentification
Toute écriture mémoire passe derrière l' authentification existante (JWT).

### ASR-02 — Autorisation
Les routes devraient distinguer au moins les permissions `READ`, `WRITE`, `APPROVE` et `ADMIN`.

### ASR-03 — Secrets
Aucun mot de passe, token, clé, cookie ou URL signed ne doit être persisté dans Obsidian.

### ASR-04 — Redaction
Les rapports et sources brutes capturant du contenu temporaire sensible doivent être redactés avant tout export public.

### ASR-05 — Audit
Chaque écriture doit produire une trace avec auteur, timestamp, event type, objet et source.

### ASR-06 — Escalade
Un agent ne peut pas s'attribuer une approbation humaine ni reclasser une proposition comme décision.

### ASR-07 — Immutabilité
Les archives brutes ne doivent pas être réécrites pour masquer un incident.

### ASR-08 — Publication
Une sortie publique doit passer par une liste blanche, un scan, une review et une autorisation.

### ASR-09 — Confidentiality boundary
`core/secrets`, `core/auth` et `core/security` gardent l'autorité locale.

### ASR-10 — Supply chain
Les dépendances documentées dans `pyproject.toml`, `uv.lock`, `package.json` et `Cargo.toml` sont hors scope d'execution directe de ce document mais doivent être auditables.

## 4. Risques

- FUITE : publication accidentelle de la mémoire.
- DRIFT : mémoire hors dépôt.
- ABUSE : agent auto-validant.
- LOSS : suppression des archives.
- INTEGRITY : redactions sans traçabilité.

## 5. Contrôles

- scan de secrets avant tout export ;
- revue humaine des changements de statut ;
- liste blanche ;
- provenance obligatoire ;
- authentification et RBAC.

---

Document lié : `ADR-EM-001-engineering-memory-architecture.md`.EOF
echo done

# ETHAN — Public/Private Separation and Publication Readiness

## 1. Résumé exécutif

- Le dépôt contient du code source ETHAN, des tests, de la documentation, des dépendances et des artefacts privés (`Odsidian/`).
- La branche `main` et la branche de travail partagent le même SHA public, mais le dépôt local contient un grand volume de changements non validés et plusieurs fichiers privés.
- Publication publique possible après une branche candidate sanitaire, pas après un simple push de la branche actuelle.
- `Odsidian/` est suivi Git et contient 106 fichiers / 98 Mo, dont des archives d'agent et des URLs CloudFront signées temporairement expirées.
- Les secrets locaux sont en `.env`, `.secrets` et fichiers de configuration clients; ils ne doivent jamais être publiés.
- Licence racine : Apache-2.0.

## 2. Inventaire et classification par répertoire

| Élément | État actuel | Destination proposée | Risque | Action |
|---|---|---|---|---|
| `core/` | Suivi | PUBLIC | Medium | Garder, Nettoyer imports mineurs |
| `interfaces/api/` | Suivi + local changes | PUBLIC | Medium | Garder, documenter |
| `interfaces/webui/` | Suivi + local changes | PUBLIC | High due generated assets | filtrer `node_modules`, `.next` |
| `interfaces/bridge/` | Suivi | PUBLIC_AFTER_REVIEW | Medium | vérifier licences |
| `tests/` | large (891 files) | PUBLIC | Medium | garder les tests sans données réelles; remplacer seeds privés |
| `docs/` | large (320 files) | PUBLIC | Medium | trier archives privées |
| `scripts/` | suivi | PUBLIC | Low | okay |
| `deploy/` | suivi | PUBLIC | Medium | documenter chaînes versions |
| `examples/` | suivi | PUBLIC_AFTER_REVIEW | License | vérifier forks licences |
| `plugins/` | suivi | PUBLIC | Medium | verifier dépendances |
| `sdk/` | suivi | PUBLIC | Medium | publication API likely |
| `install/` | suivi | PUBLIC | Low | keep |
| `archive/` | suivi | PRIVATE | Medium | déplacer archives |
| `cookbook/` | suivi | PUBLIC | Low | okay |
| `Odsidian/` | suivi, 98 Mo | PRIVATE | High | isoler et rewrite sans ce repo |
| `core/auth`, internal routes | suivi | PUBLIC | Security | keep tests focused |
| `scripts/locale-patches` | suivi | PUBLIC | Low | keep |
| `docker-compose*.yml` | suivi / untracked | PUBLIC (with lock override) | Medium | keep env placeholders only |
| `docs/security/*.md` | untracked | PUBLIC (selected) | Medium | étudier before public |
| `docs/audit/*` | untracked / tracked | PRIVATE or PRIVATE_AFTER_REVIEW | Medium | avoid proving historical audits publicly |
| `docs/engineering/baseline` | untracked | PUBLIC (selected) | Low | keep |
| `ethan` binary state | untracked | build artifact? | Low | likely gitignore |
| `.github/dependabot` | untracked | PUBLIC | Low | okay |
| `CODEOWNERS` | untracked | PUBLIC | Medium | review privacy |

## 3. Classification fichier par fichier (extrait)

`Odsidian/01-Archives/cline/*` contient de la conversation d'agent et données privées. Statut à marquer PRIVATE.

`tests/test_secret_redaction.py` contains synthetic secret fixture, likely PUBLIC after review.

`examples/frame/*` inclut d'autres licenses MIT/Apache, vérifier before release.

`interfaces/webui` public assets ok, but transient node_modules are ignored/untracked and must never be published.

## 4. Historique Git

- `origin/main` and `origin/refactor/ethan-rebuild-p0` same base SHA.
- Local worktree includes generated files/changes that should not all be published.
- 646 Cline checkpoints are local only.
- `Odsidian/` tracked files exist in shared tree and likely remote while commit; this is the principal history risk.
- Public branches likely contain all 106 files as part of base commit, so history rewriting would be needed if complete removal is required.
- Recommendations: keep current remote, create sanitized candidate branch from `9e57d1c0` without archives/config/secrets rather than rewrite public history first.

## 5. Configration et sécurité

- Non-secret URL vars can stay as examples.
- JWT_SECRET must never be published.
- Compose interpolates required variables; missing vars break startup.
- CORS must be configured for selected deployment, not wildcard in production.
- WebSocket origins must be allowlisted.
- `.env` should never be committed as data.
- `.gitignore` should be audited before candidate branch creation.

## 6. Licences et dépendances

- Root license Apache-2.0.
- Example `jarvis-os` MIT.
- Example `craft-fonts` MIT/Apache; preserve notices.
- Example `frame` has its own LICENSE.
- Dependencies include Rust and Node addons; obligations to check subprojects.
- No consolidated license file for all subprojects found; publication gate must scan.

## 7. Architecture publique cible

Release candidate should contain:

- selected `core/`, `interfaces/`, selected `tests/`, `docs/`, `scripts/`, `deploy/`, root OSS files.
- exclude `.env`, `.secrets`, `node_modules`, `.venv`, runtime archives.
- optional `Odsidian` moved to a private companion repository.
- CI build and policy review.

## 8. Publication gate

1. secret scanning (Gitleaks / custom).
2. private data scanning for `Odsidian` paths.
3. license compliance scan.
4. dependency audit.
5. tests & typecheck.
6. build.
7. docs verification.
8. human review.

Blocking: secret, PII, license noncompliance.

## 9. Migration strategy

- Build a sanitary candidate branch from current public SHA.
- Apply only reviewed source, docs, tests, build.
- Review all staged files with `git diff --cached` and explicit allowlist.
- Ensure tags do not include archives.
- Do not touch original branch or files.

## 10. Risques de publication

- Private archives and conversation history.
- Signed URLs (expired but metadata).
- Local envs / API tokens.
- Docker socket? Example config may reveal local path.

No git mutation was performed.

## Verdict

**Publication not safe from current branch without a curated sanitary release branch.** The candidate should be built from public base with an explicit allowlist, private separation, and hardened CI before any push.


## Verification addendum

### LICENSE
- `LICENSE` is valid text (10773 bytes), SHA256 `ac617ecddb7ffeb27a239c6c9c8145212306baa90e23ee694849bf3cefb10743`, leading whitespace only.
- `pyproject.toml` declares Apache-2.0.
- No license replacement was performed.

### Remote visibility
- `origin` = `git@github.com:seclib/Ethan.git`.
- Branches visible to the tooling are `main` and `refactor/ethan-rebuild-p0`, both pointing to the same public SHA.
- Visibility could not be automatically verified beyond Git remote references; GitHub visibility remains unknown without authenticated API calls.
- `Odsidian/` is present in the tracked base tree (`git ls-tree -r main --name-only | grep '^Odsidian/'` returned 106 files); therefore the risk of historical public exposure is confirmed.

### Odsidian inventory
- File-by-file inventory has been created at `docs/audit/ETHAN_PUBLIC_PRIVATE_INVENTORY.md`.
- Every tracked `Odsidian` path is classified `PRIVATE`.
- Inventory contains relative path, size, MIME type, HEAD presence, tracked-history presence, classification and rationale.
- Content was not reproduced to avoid exposing private data or signed URL parameters.
- Signed URL markers are present in 27 files. One examined example had `Expires=1781699779`, below the current epoch, so it is expired.

### Historical strategy
- A. Sanitize the working tree by constructing a candidate branch with an explicit allowlist; no history rewrite.
- B. Keep raw private data in a separate archive.
- C. Rewrite remote history only if full historical removal is legally / operationally required; this would affect clones, forks, tags and collaborator references.

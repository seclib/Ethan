# Secret Exposure Assessment — ETHAN

## Verified local hygiene
- `.env` exists locally and is ignored by `.gitignore`.
- `.env.postgres-test` exists locally.
- `.secrets/jwt.key` exists locally with restrictive mode 600.
- `.gitignore` retains `.env.example` as template.
- `.next/` is ignored locally.

## Historical scan
- A Gitleaks scan limited to `main` produced 114 findings.
- All scanned findings are test artifacts, fixture strings, docs references or generated Next.js manifests.
- No live production secret was confirmed in current working repository.
- Full all-refs scan was not completed.
- A developer’s local workspace includes secrets and artifacts that must not be included in published release.

## Potential risks
- `.env` and `.env.postgres-test` pair values locally.
- `.secrets/jwt.key` is persisted local only.
- Standalone output `.next` is generated practice with manifest keys.
- default admin hash globally visible in SQL template.
- generated cache and local dataset in user profile, not controlled repo.

## Recommendations
- Never publish based only on `git ls-files`; always perform allowlist publish.
- Run complete history/refs scanners in isolated environment.
- Rotate local credentials if needed.
- Strip all local artifacts from candidate release.
- Avoid mention of `.env` secret values in logs/reports.
- Redact before publication.

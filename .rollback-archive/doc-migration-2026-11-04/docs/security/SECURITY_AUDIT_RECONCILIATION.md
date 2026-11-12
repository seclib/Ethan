# Security Audit Reconciliation — ETHAN

## Contradictions resolved

| Topic | Earlier audit claim | Current verified source | Resolution |
|---|---|---|---|
| SECURITY.md | Missing | Now present at repository root | VERIFIED present, though content must be reviewed before publication |
| CODEOWNERS | Missing | Now present | VERIFIED present, ownership assignment still requires maintainership review |
| Dependabot | Missing | `.github/Dependabot.yml` now present | VERIFIED present, not destination branch protection |
| CodeQL | Not available | No CodeQL workflow visible | VERIFIED unknown scanner gap |
| Git secret scan | Pass claimed | Gitleaks produced 114 findings, all false positives or generated artifacts | No production secret confirmed, but full history incomplete |
| Session revocation | No mechanism | No `token_version` or session store in schema/current auth | VERIFIED absence of central revocation |
| WebUI proxy | API route sets cookies | `interfaces/webui/src/app/api/[...path]/route.ts` confirmed | PARTIAL: secure status lit dynamically |
| API key ownership | uncertain | `api_keys.py` routes use query `user`; manager scopes and soft revoke verified | PARTIALLY VERIFIED |
| Default admin | starter hash remains | SQL files verified | VERIFIED weak bootstrap |
| Docker socket | only odin-controller | compose verified | VERIFIED narrow fixed controller |
| Network exposure | loopback only | compose `127.0.0.1` bindings verified | VERIFIED config, not firewall |
| Realm/settings protection | all public? | public only health/cache/ docs and auth public | VERIFIED by `is_public_path` |

## Contradictions still open

- `API key user` is parsed as scalar query instead of an identity-derived principal. This may be intentional but is security relevant and needs tests.
- Full all-refs Gitleaks scan remains unresolved due local checkpoint refs and scan runtime.
- Fine `Cosign` / SHA pinning still unimplemented.
- WebSocket security report remains vulnerable until current code is secured.
- starter account can still be addressed.
- history tests yet to use real DB and Playwright browsers.
- `docs/security/SECURITY_PROGRAM_CHARTER.md` / asset inventory are product docs, not runtime evidence.
- Known source structure has large local generated artifacts (`Odsidian`, `.next`, examples) that must be excluded from any publication.

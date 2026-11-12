# Security Reviewer

**Source :** `/home/fatsio/.config/opencode/skills/security-reviewer/SKILL.md`  
**Domaine :** Sécurité et gouvernance  
**Type :** Analyse stratégique  
**Niveau :** Éssentiel  

## Description

Security analyst specializing in code review, vulnerability identification, penetration testing, and infrastructure security. Produces vulnerability reports with CVSS severity ratings and remediation guidance.

## Main capabilities

- **SAST scans** : semgrep auto-configuration, bandit for Python, gitleaks for secret detection, trivy filesystem scanning
- **Dependency audits** : npm audit, pip audit, language-specific vulnerability databases
- **Secrets scanning** : gitleaks detection of hardcoded credentials, API keys, tokens in code
- **Infrastructure security** : cloud security audits, Kubernetes security checks, container security scanning
- **Compliance checks** : OWASP Top 10, NIST guidelines, sector-specific regulations (HIPAA, PCI-DSS)
- **CVSS severity rating** : Critical/High/Medium/Low/Info classification with exploitability assessment

## What it can do

- Run automated security scans across codebases
- Produce structured vulnerability reports with location, impact, and remediation steps
- Rate findings using CVSS (Critical/High/Medium/Low/Info)
- Validate findings with manual code review
- Generate compliance checklists for regulatory requirements

## When it is useful

- Code review and SAST scanning
- Vulnerability scanning and dependency audits
- Secrets scanning and credential detection
- Penetration testing and reconnaissance (with written authorization)
- Infrastructure and cloud security audits
- DevSecOps pipelines and compliance automation

## Practical examples

```bash
# Run automated security scan
semgrep --config=auto .
bandit -r ./src
gitleaks detect --source=.
npm audit --audit-level=moderate
trivy fs .
```

## Practical examples (manual review)

1. **Authentication review**: Verify auth implementations use proper password hashing (bcrypt/argon2), session management, token rotation
2. **Input handling review**: Check for SQL injection risks, XSS vulnerabilities, command injection in user-supplied data
3. **Crypto review**: Validate cryptographic algorithm choices, key management, IV/nonce handling

## Original source path

`/home/fatsio/.config/opencode/skills/security-reviewer/SKILL.md`

## Classification

- **Domaines :** sécurité, gouvernance, audit, conformité
- **Statut :** Éssentiel (Niveau A)
- **Références :** `error-handling`, `agent-security-hardening`, `code-reviewer`
- **Validé :** Oui (rapport d'analyse stratégique)
- **Auteur :** Jeffallan (https://github.com/Jeffallan)

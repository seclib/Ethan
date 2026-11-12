# Code Reviewer (code-reviewer)

**Source :** `/home/fatsio/.config/opencode/skills/code-reviewer/SKILL.md`  \n**Domaine :** Qualité — Revue de code  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Analyzes code diffs and files to identify bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns. Produces structured review report with prioritized, actionable feedback. Complements security-reviewer and test-master.

## Main capabilities

- **Bug identification**: Identifies logical bugs, edge case failures, and runtime errors in code
- **Security vulnerability detection**: Detects SQL injection, XSS, insecure deserialization, and other common vulnerabilities
- **Code smell detection**: Identifies code smells such as long methods, large classes, duplicated code
- **N+1 query detection**: Finds ORM-generated N+1 query patterns
- **Naming issue detection**: Identifies inconsistent or unclear naming conventions
- **Architectural concern analysis**: Evaluates code against architectural patterns and design principles

## What it can do

- Analyze pull request diffs and provide line-by-line feedback
- Detect common security vulnerabilities in code
- Identify code maintainability issues and suggested refactoring
- Flag N+1 query patterns in ORM usage
- Validate naming conventions against project standards
- Produce structured review reports with severity classification
- Add comments to code review discussions with specific references

## When it is useful

- Pull request code reviews and quality gates
- Identifying security vulnerabilities during development
- Improving code maintainability and readability
- Detecting ORM query performance issues
- Enforcing coding standards and naming conventions
- Complementing automated linting and testing tools

## Practical examples

### SQL injection detection

```python
# Before (vulnerable)
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# After (safe)
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### N+1 query detection in Django

```python
# Before (N+1)
for author in authors:
    print(author.article_count)  # Triggers N queries

# After (fixed with annotate)
from django.db.models import Count
authors = Author.objects.annotate(article_count=Count('articles'))
```

### Code review report structure

```markdown
# Code Review Report

## Summary
- **Files changed**: 5
- **Lines added**: 120
- **Lines removed**: 85

## Issues Found
### [SEC] SQL Injection Risk (Critical)
- **File**: `users.py:45`
- **Issue**: Direct string concatenation in SQL query
- **Recommendation**: Use parameterized queries

### [STYLE] Variable naming (Medium)
- **File**: `utils.py:12`
- **Issue**: Variable `user_id` should be `user_id` per style guide
- **Recommendation**: Rename to follow naming convention

### [PERF] N+1 query pattern (High)
- **File**: `report.py:30`
- **Issue**: Loop triggers N database queries
- **Recommendation**: Use `annotate()` or `prefetch_related()`
```
```

## Original source path

`/home/fatsio/.config/opencode/skills/code-reviewer/SKILL.md`

## Classification

- **Domaines :** qualité, revue de code, sécurité, naming
- **Statut :** Indispensable (Niveau A)
- **Références :** `security-reviewer`, `test-master`, `error-handling`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis

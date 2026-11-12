# Agent Security Hardening (agent-security-hardening)

**Source :** `/home/fatsio/.config/opencode/skills/agent-security-hardening/SKILL.md`  \n**Domaine :** Sécurité IA — Hardening  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Security hardening patterns for AI agents processing untrusted content, invoking tools, writing workspace files, managing runtime identifiers, and handling credentials. Treats model output, retrieved content, tool output, memory, and cross-agent messages as untrusted input. Defaults external integrations to read-only, grants write capability separately, and validates at action boundary.

## Main capabilities

- **Untrusted input validation**: Treats model output, retrieved content, tool output, memory, and cross-agent messages as untrusted
- **Read-only default**: Defaults external integrations to read-only mode
- **Write capability separation**: Grants write capability separately and explicitly
- **Action boundary validation**: Validates at action boundary before executing writes
- **Credential management**: Secure handling of API keys, tokens, and sensitive credentials
- **Content sanitization**: Sanitizes and validates all external content before processing

## What it can do

- Validate model output before processing or caching
- Sandbox tool execution with read-only permissions where possible
- Implement credential rotation and secret management
- Sandbox agent workspace writes with path validation
- Audit cross-agent message flows for security compliance
- Generate security hardening reports for AI agent frameworks

## When it is useful

- Building AI agent frameworks that process untrusted model output
- Configuring tool integration for AI assistants
- Deploying agent systems in production environments
- Setting up credential management for agent integrations
- Implementing content safety filters for retrieved data
- Hardening agent runtimes against prompt injection

## Practical examples

### Read-only tool integration

```python
# Default to read-only; grant write explicitly
@tool(permissions=["read"])
def search_documents(query: str) -> list[dict]:
    """Search documents with read-only permission."""
    results = document_store.search(query)
    return results

# Write operation requires explicit permission
@tool(permissions=["write"])
def create_document(content: str) -> dict:
    """Create document with write permission."""
    doc_id = document_store.save(content)
    return {"id": doc_id}
```

### Action boundary validation

```python
def validate_action_boundary(action: str, payload: dict) -> bool:
    """Validate at action boundary before execution."""
    if action == "write":
        # Validate payload paths are not project-critical
        if "/etc/" in payload.get("path", ""):
            return False
    return True
```

### Credential management pattern

```python
# Never hardcode credentials; use environment variables
API_KEY = os.getenv("API_KEY_NAME")
if not API_KEY:
    raise ValueError("API key not configured")
```

## Original source path

`/home/fatsio/.config/opencode/skills/agent-security-hardening/SKILL.md`

## Classification

- **Domaines :** sécurité IA, hardening, credentials, input validation
- **Statut :** Spécialisé (Niveau B)
- **Références :** `security-reviewer`, `error-handling`, `the-fool`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis

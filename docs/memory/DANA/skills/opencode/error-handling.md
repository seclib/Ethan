# Error Handling (error-handling)

**Source :** `/home/fatsio/.config/opencode/skills/error-handling/SKILL.md`  \n**Domaine :** Robustness — Patterns d'erreurs  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Patterns for robust error handling across TypeScript, Python, and Go. Covers typed errors, error boundaries, retries, circuit breakers, and user-facing error messages. Fail fast and loudly, typed errors over string messages, user messages ≠ developer messages, never swallow errors silently.

## Main capabilities

- **Typed errors**: Uses custom error types over string message exceptions
- **Error boundaries**: Implements error boundaries in frontend and backend contexts
- **Retry patterns**: Implements exponential backoff and jitter for transient failures
- **Circuit breakers**: Prevents cascading failures with circuit breaker pattern
- **User-facing messages**: Separates developer-facing error messages from user messages
- **Error classification**: Classifies errors as client, server, or system errors

## What it can do

- Define custom error types with proper inheritance and error codes
- Implement error boundaries in React (component-level error handling)
- Set up retry logic with exponential backoff for API calls
- Configure circuit breakers to prevent cascading failures
- Separate user-facing error messages from developer/logging messages
- Classify errors for appropriate handling and monitoring

## When it is useful

- Building production-grade software requiring fault tolerance
- Implementing resilient API clients and services
- Designing error handling that prevents cascading failures
- Separating technical errors from user-facing messages
- Adding retry and circuit breaker patterns to microservices
- Improving error observability and logging

## Practical examples

### Custom typed error in Python

```python
class ApplicationError(Exception):
    """Base application error with error code."""
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(ApplicationError):
    """404 Not Found error."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            error_code="NOT_FOUND",
            status_code=404
        )
```

### Retry with exponential backoff

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Retry function with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(delay)
```

### Circuit breaker pattern

```python
from pybreaker import CircuitBreaker

# Circuit breaker configured to trip after 3 failures
cb = CircuitBreaker(fail_max=3, reset_timeout=60)

@cb
def call_external_service():
    return external_service_api_call()
```

## Original source path

`/home/fatsio/.config/opencode/skills/error-handling/SKILL.md`

## Classification

- **Domaines :** robustesse, gestion d'erreurs, circuit breaker, typed errors
- **Statut :** Indispensable (Niveau A)
- **Références :** `agent-security-hardening`, `monitoring-expert`, `change-impact`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis

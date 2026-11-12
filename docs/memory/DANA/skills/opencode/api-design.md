# API Design (api-design)

**Source :** `/home/fatsio/.config/opencode/skills/api-design/SKILL.md`  \n**Domaine :** Architecture — API  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

REST API design patterns including resource naming, status codes, pagination, filtering, error responses, versioning, and rate limiting. Conventions: resources are nouns, plural, lowercase, kebab-case; HTTP methods map to CRUD; status codes 2xx/4xx/5xx; pagination with Link headers; error response format.

## Main capabilities

- **Resource naming**: Establishes consistent resource naming conventions (plural, lowercase, kebab-case)
- **HTTP status codes**: Defines appropriate status code usage for CRUD operations and error conditions
- **Pagination**: Implements Link header pagination with proper rel values (first, prev, next, last)
- **Filtering**: Supports query parameter filtering for resource selection
- **Error responses**: Defines consistent error response format with codes and messages
- **Versioning**: Implements API versioning strategies (URL prefix, header-based)
- **Rate limiting**: Configures request rate limiting per endpoint or client

## What it can do

- Design RESTful API schemas with proper resource naming
- Define HTTP status code usage (2xx for success, 4xx for client errors, 5xx for server errors)
- Implement pagination with Link headers and cursor/offset based options
- Create query parameter filtering systems for API consumers
- Define error response formats with error codes and messages
- Set up API versioning strategies for backward compatibility
- Configure rate limiting middleware for endpoint protection

## When it is useful

- Designing new RESTful APIs from scratch
- Establishing API design conventions for team projects
- Creating API documentation and contracts
- Implementing API versioning for evolving services
- Adding rate limiting to protect endpoints from abuse
- Standardizing error handling across microservice architectures

## Practical examples

### RESTful resource naming

```http
# Good practices
GET /api/v1/users          # List users
GET /api/v1/users/123     # Get user by ID
POST /api/v1/users         # Create new user
PUT /api/v1/users/123      # Update user
DELETE /api/v1/users/123   # Delete user

# Avoid
GET /getUser               # Verb-based (not RESTful)
GET /user/123/info         # Nested unnecessarily
```

### Pagination with Link headers

```http
# Response with pagination
HTTP/1.1 200 OK
Link: <https://api.example.com/users?page=2>; rel="next"
Link: <https://api.example.com/users?page=5>; rel="last"
Total-Count: 150

# Client request
GET /api/v1/users?page=1&per_page=20
```

### Error response format

```json
# Standard error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Must be a valid email address"
    },
    "request_id": "c5a7e3f2-1a2b-3c4d-5e6f-7g8h9i0j1k2l"
  }
}
```

### API versioning (URL prefix)

```http
# v1 endpoints
GET /api/v1/users
POST /api/v1/users

# v2 endpoints (backward compatible)
GET /api/v2/users
POST /api/v2/users
```

## Original source path

`/home/fatsio/.config/opencode/skills/api-design/SKILL.md`

## Classification

- **Domaines :** architecture, API, REST, conception
- **Statut :** Indispensable (Niveau A)
- **Références :** `python-pro`, `monitoring-expert`, `change-impact`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis

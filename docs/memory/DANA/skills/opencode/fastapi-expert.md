# FastAPI Expert (fastapi-expert)

**Source :** `/home/fatsio/.config/opencode/skills/fastapi-expert/SKILL.md`  \n**Domaine :** Framework — FastAPI  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Specifically for FastAPI — creating REST endpoints, defining Pydantic V2 models, JWT authentication, async SQLAlchemy database operations, WebSocket endpoints, and OpenAPI documentation. API gateway patterns.

## Main capabilities

- **REST endpoint creation**: Creates FastAPI routes with proper path operation configuration
- **Pydantic V2 models**: Defines data validation and serialization using Pydantic V2 models
- **JWT authentication**: Implements JWT-based authentication flows with token management
- **Async SQLAlchemy**: Implements async database operations using SQLAlchemy async API
- **WebSocket endpoints**: Creates real-time communication endpoints with FastAPI WebSocket support
- **OpenAPI documentation**: Generates automatic OpenAPI schema and documentation

## What it can do

- Define FastAPI applications with routers and path operations
- Create Pydantic V2 models for request/response validation
- Implement OAuth2 password flow and JWT token generation
- Set up async database sessions with SQLAlchemy
- Create WebSocket connections with authentication
- Generate comprehensive OpenAPI documentation with proper tagging and descriptions

## When it is useful

- Building new APIs with FastAPI framework
- Adding JWT authentication to existing FastAPI applications
- Implementing WebSocket communication in FastAPI projects
- Creating API gateways or microservice architectures
- Generating interactive API documentation for consumers

## Practical examples

### FastAPI route with Pydantic model

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items/")
async def create_item(item: Item) -> Item:
    return item
```

### JWT authentication dependency

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Verify JWT token and return current user."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"id": user_id, "scopes": payload.get("scopes", [])}
```

## Original source path

`/home/fatsio/.config/opencode/skills/fastapi-expert/SKILL.md`

## Classification

- **Domaines :** framework, FastAPI, API, async, authentication
- **Statut :** Spécialisé (Niveau B)
- **Références :** `api-design`, `mcp-developer`, `monitoring-expert`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis

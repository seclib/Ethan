"""ETHAN API — Ollama Proxy Endpoint

This module provides a secure proxy for frontend applications to access Ollama
without exposing the internal endpoint directly. It masks internal URLs and
restricts allowed paths to prevent abuse.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
import httpx
import os
import json
from typing import Dict, Any

router = APIRouter(
    prefix="/v1/proxy",
    tags=["proxy"]
)

# Whitelist of allowed paths to prevent open relay
ALLOWED_PATHS = {
    "/api/generate",
    "/api/chat",
    "/api/embed",
    "/api/show",
    "/api/pull",
    "/api/push",
    "/api/delete",
    "/api/ps",
    "/api/version",
    "/v1/models",
    "/v1/chat/completions",
    "/api/tags",
}

@router.api_route("/ollama/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
async def proxy_ollama(path: str, request: Request):
    """
    Proxy requests to Ollama service.
    
    This endpoint ensures that:
    1. The internal OLLAMA_URL is never exposed to the frontend
    2. Only specific, safe paths are accessible
    3. Request/response headers are sanitized
    """
    # Security: Check for allowed paths only
    normalized_path = path if path.startswith("/api/") or path.startswith("/v1/") else f"/api/{path}"
    
    if normalized_path not in ALLOWED_PATHS:
        raise HTTPException(
            status_code=403,
            detail=f"Path '{normalized_path}' is not allowed"
        )
    
    # Get the configured Ollama endpoint
    base_ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    target_url = f"{base_ollama_url.rstrip('/')}/{normalized_path}"
    
    # Prepare request body
    body = await request.body()
    
    # Filter headers to only include safe ones
    filtered_headers = {}
    for key, value in request.headers.items():
        # Skip hop-by-hop headers and auth tokens
        if key.lower() in ['host', 'authorization', 'content-length', 'transfer-encoding']:
            continue
        filtered_headers[key] = value
    
    # Set correct content type if not provided
    if "content-type" not in filtered_headers and body:
        filtered_headers["content-type"] = request.headers.get("content-type", "application/json")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=filtered_headers,
                content=body if body else None,
                follow_redirects=True
            )
            
        # Return the proxied response
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
            headers={"X-Proxied-By": "ETHAN-Core"}
        )
        
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach Ollama service"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Ollama service timed out"
        )
    except Exception as e:
        # Log error securely without exposing internal details
        print(f"Proxy error for path {normalized_path}: {str(e)[:100]}...")
        raise HTTPException(
            status_code=500,
            detail="Internal proxy error"
        )
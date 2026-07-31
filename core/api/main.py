"""ETHAN API — REST API Gateway"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
import os
import nats
from nats.aio.client import Client as NATSClient
from fastapi import Response

app = FastAPI(
    title="ETHAN API",
    description="Cognitive Runtime API Gateway",
    version="1.0.0"
)

# Models
class MessageRequest(BaseModel):
    content: str
    session_id: str
    model: Optional[str] = "default"
    stream: bool = False

class MessageResponse(BaseModel):
    content: str
    session_id: str
    done: bool
    metadata: Optional[Dict[str, Any]] = None

class StatusResponse(BaseModel):
    runtime: Dict[str, Any]
    services: List[Dict[str, Any]]

class ServiceRequest(BaseModel):
    services: List[str]

# Global NATS client
nats_client: Optional[NATSClient] = None

@app.on_event("startup")
async def startup():
    """Connect to NATS on startup"""
    global nats_client
    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    startup_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )
    for attempt in range(1, 11):
        try:
            remaining = startup_deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError("API dependency startup deadline exceeded")
            nats_client = await asyncio.wait_for(
                nats.connect(nats_url), timeout=min(10, remaining)
            )
            print("✓ Connected to NATS")
            break
        except Exception as e:
            nats_client = None
            if attempt == 10:
                print(f"✗ Failed to connect to NATS after {attempt} attempts: {e}")
                raise
            wait = min(attempt * 2, 10)
            wait = min(wait, max(0.0, startup_deadline - asyncio.get_running_loop().time()))
            print(f"NATS connection failed ({e}); retrying in {wait}s")
            await asyncio.sleep(wait)

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from NATS on shutdown"""
    global nats_client
    if nats_client:
        await asyncio.wait_for(nats_client.close(), timeout=10)
        print("✓ Disconnected from NATS")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ETHAN API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/v1/health")
async def health():
    """Compatibility readiness endpoint."""
    return _health_response()


@app.get("/health")
async def root_health():
    """Readiness endpoint used by container probes."""
    return _health_response()


@app.get("/health/live")
async def health_live():
    """Liveness endpoint that only asserts the HTTP process is serving."""
    return {"status": "ok", "service": "api"}


@app.get("/health/ready")
async def health_ready():
    """Readiness alias used by the Docker healthcheck contract."""
    return _health_response()


def _health_response() -> Response | dict:
    nats_ok = nats_client is not None and nats_client.is_connected
    payload = {
        "status": "ok" if nats_ok else "degraded",
        "service": "api",
        "nats_connected": nats_ok,
    }
    if not nats_ok:
        return Response(
            content=json.dumps(payload),
            status_code=503,
            media_type="application/json",
        )
    return payload

@app.post("/v1/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Send a message to ETHAN"""
    if not nats_client:
        raise HTTPException(status_code=503, detail="NATS not connected")
    
    # Create message event
    event = {
        "type": "message.send",
        "session_id": request.session_id,
        "payload": {
            "content": request.content,
            "model": request.model,
            "stream": request.stream
        }
    }
    
    # Publish to NATS
    await nats_client.publish(
        "ethan.interface.api",
        json.dumps(event).encode()
    )
    
    # TODO: Wait for response from kernel
    # For now, return a simple response
    return MessageResponse(
        content=f"Echo: {request.content}",
        session_id=request.session_id,
        done=True,
        metadata={
            "model": request.model,
            "tokens": len(request.content.split())
        }
    )

@app.get("/v1/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    # TODO: Query runtime for actual status
    return StatusResponse(
        runtime={
            "state": "RUNNING",
            "uptime": "2h 15m",
            "pid": 12345
        },
        services=[
            {"name": "nats", "state": "running", "health": "healthy"},
            {"name": "redis", "state": "running", "health": "healthy"},
            {"name": "postgres", "state": "running", "health": "healthy"},
            {"name": "api", "state": "running", "health": "healthy"},
            {"name": "kernel", "state": "running", "health": "healthy"}
        ]
    )

@app.post("/v1/services/start")
async def start_services(request: ServiceRequest):
    """Start services via Runtime"""
    if not nats_client:
        raise HTTPException(status_code=503, detail="NATS not connected")
    
    # Create command event
    event = {
        "type": "services.start",
        "session_id": "api",
        "payload": {
            "services": request.services
        }
    }
    
    # Publish to NATS
    await nats_client.publish(
        "ethan.runtime.command",
        json.dumps(event).encode()
    )
    
    return {
        "success": True,
        "services": request.services
    }

@app.post("/v1/services/stop")
async def stop_services(request: ServiceRequest):
    """Stop services via Runtime"""
    if not nats_client:
        raise HTTPException(status_code=503, detail="NATS not connected")
    
    # Create command event
    event = {
        "type": "services.stop",
        "session_id": "api",
        "payload": {
            "services": request.services
        }
    }
    
    # Publish to NATS
    await nats_client.publish(
        "ethan.runtime.command",
        json.dumps(event).encode()
    )
    
    return {
        "success": True,
        "services": request.services
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

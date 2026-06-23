"""API Entry Point — Normalisation vers Intent

Toute entrée API est convertie en Intent via IntentRouter.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from core.context.intent import IntentRouter


app = FastAPI(title="Jarvis OS API")
router = IntentRouter()


class APIRequest(BaseModel):
    input: str
    context: Optional[Dict[str, Any]] = None


class VoiceRequest(BaseModel):
    transcript: str
    language: str = "en"
    confidence: float = 1.0
    audio_metadata: Optional[Dict[str, Any]] = None


class AutomationRequest(BaseModel):
    trigger: str
    automation_id: Optional[str] = None
    trigger_type: str = "scheduled"
    payload: Optional[Dict[str, Any]] = None


@app.post("/v1/intent/text")
async def text_intent(request: APIRequest):
    intent = await router.parse("text", request.input)
    return {"intent": intent.__dict__}


@app.post("/v1/intent/api")
async def api_intent(request: APIRequest):
    raw = {"input": request.input, "context": request.context or {}}
    intent = await router.parse("api", raw)
    return {"intent": intent.__dict__}


@app.post("/v1/intent/voice")
async def voice_intent(request: VoiceRequest):
    raw = {
        "transcript": request.transcript,
        "language": request.language,
        "confidence": request.confidence,
        "audio_metadata": request.audio_metadata or {},
    }
    intent = await router.parse("voice", raw)
    return {"intent": intent.__dict__}


@app.post("/v1/intent/automation")
async def automation_intent(request: AutomationRequest):
    raw = {
        "trigger": request.trigger,
        "automation_id": request.automation_id,
        "trigger_type": request.trigger_type,
        "payload": request.payload or {},
    }
    intent = await router.parse("automation", raw)
    return {"intent": intent.__dict__}


@app.get("/health")
async def health():
    return {"status": "ok"}
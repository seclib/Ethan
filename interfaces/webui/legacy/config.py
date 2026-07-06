from __future__ import annotations
import os
from dataclasses import dataclass

def _e(n,d): return os.getenv(n,d)

@dataclass
class Settings:
    API_URL: str = _e("ETHAN_API_URL", "http://localhost:8000")
    EVENT_REFRESH_INTERVAL: int = int(_e("ETHAN_REFRESH_INTERVAL", "2"))
    MAX_EVENTS: int = int(_e("ETHAN_MAX_EVENTS", "100"))
    DEBUG_MODE: bool = _e("ETHAN_DEBUG", "true").lower() in ("1", "true", "yes")
    API_TIMEOUT: int = int(_e("ETHAN_API_TIMEOUT", "5"))
    API_RETRIES: int = int(_e("ETHAN_API_RETRIES", "2"))
    @property
    def api(self): return self.API_URL.rstrip("/")

settings = Settings()

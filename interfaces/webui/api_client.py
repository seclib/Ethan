"""API client for ETHAN backend."""

import requests
from typing import Dict, Any, Optional

import config


class EthanAPIClient:
    """Client to interact with ETHAN API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or config.API_URL

    def send_message(self, message: str) -> Dict[str, Any]:
        """Send user message to ETHAN."""
        try:
            response = requests.post(
                f"{self.base_url}/message",
                json={"content": message},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_state(self) -> Dict[str, Any]:
        """Get current system state."""
        try:
            response = requests.get(f"{self.base_url}/state", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

    def get_events(self) -> list:
        """Get latest events."""
        try:
            response = requests.get(f"{self.base_url}/events", timeout=5)
            response.raise_for_status()
            return response.json().get("events", [])
        except Exception:
            return []

    def get_goals(self) -> list:
        """Get current goals."""
        try:
            response = requests.get(f"{self.base_url}/goals", timeout=5)
            response.raise_for_status()
            return response.json().get("goals", [])
        except Exception:
            return []

    def get_logs(self) -> list:
        """Get recent logs from system."""
        try:
            response = requests.get(f"{self.base_url}/logs", timeout=5)
            response.raise_for_status()
            return response.json().get("logs", [])
        except Exception:
            return []
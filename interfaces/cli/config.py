#!/usr/bin/env python3
"""ETHAN CLI — Configuration."""

import os
import json
from pathlib import Path

CONFIG_DIR = os.path.expanduser("~/.config/ethan")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "runtime_socket": "/run/ethan/runtime.sock",
    "runtime_http": "http://localhost:8002",
    "timeout": 30,
    "sessions_dir": "~/.local/share/ethan/sessions",
    "history_file": "~/.local/share/ethan/history",
    "max_history": 1000,
    "streaming": True,
}


class Config:
    """CLI Configuration."""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Load config from file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception:
                # Use defaults if config is invalid
                pass
    
    def save(self):
        """Save config to file."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get config value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set config value."""
        self.config[key] = value
        self.save()


# Global config instance
config = Config()
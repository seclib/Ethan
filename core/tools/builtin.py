"""Built-in tools for ETHAN Core.

These tools are native to the platform and do not require external MCP servers
or custom user-defined functions.
"""

from __future__ import annotations

from typing import Any
from datetime import datetime

from core.tools.types import Tool, RiskLevel


def get_builtin_tools() -> list[Tool]:
    """Return the list of built-in tools available natively."""
    
    return [
        Tool(
            id="builtin_web_search",
            name="web_search",
            description="Perform a web search to find current information on a topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            },
            version="1.0.0",
            category="search",
            capabilities=["search", "web"],
            risk_level=RiskLevel.LOW,
            provider="builtin"
        ),
        Tool(
            id="builtin_current_time",
            name="get_current_time",
            description="Get the current date and time.",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Optional timezone (e.g. 'UTC', 'Europe/Paris'). Defaults to system local time."
                    }
                }
            },
            version="1.0.0",
            category="utility",
            capabilities=["time", "system"],
            risk_level=RiskLevel.LOW,
            provider="builtin"
        ),
        Tool(
            id="builtin_image_generation",
            name="generate_image",
            description="Generate an image based on a prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed description of the image to generate."
                    }
                },
                "required": ["prompt"]
            },
            version="1.0.0",
            category="media",
            capabilities=["image_generation"],
            risk_level=RiskLevel.LOW,
            provider="builtin"
        ),
        Tool(
            id="builtin_code_interpreter",
            name="execute_python_code",
            description="Execute Python code in a secure sandbox.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute."
                    }
                },
                "required": ["code"]
            },
            version="1.0.0",
            category="code",
            capabilities=["execution", "python"],
            risk_level=RiskLevel.HIGH,
            sandbox_required=True,
            provider="builtin"
        )
    ]

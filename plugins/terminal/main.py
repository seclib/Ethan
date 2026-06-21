"""Terminal Plugin — Shell command execution.

Capabilities:
  - execute_command  : Execute shell commands
  - run_script       : Run scripts in various languages
  - list_directory   : List directory contents
  - read_file        : Read file contents
  - write_file       : Write content to files
  - monitor_process  : Monitor running processes
"""

import asyncio
import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TerminalPlugin:
    """Shell command execution plugin with security restrictions."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._allowed_commands = set(self.config.get("allowed_commands", [
            "ls", "cat", "head", "tail", "grep", "find",
            "ps", "df", "du", "echo", "pwd", "whoami", "date", "uname",
        ]))
        self._timeout = self.config.get("timeout", 30)
        self._max_output = self.config.get("max_output", 100000)
        self._workdir = Path(self.config.get("working_directory", "/workspace"))
        self._workdir.mkdir(parents=True, exist_ok=True)

    def _validate_command(self, command: str) -> str:
        """Validate and sanitize a command."""
        parts = shlex.split(command)
        if not parts:
            raise ValueError("Empty command")

        cmd = parts[0]
        # Check if command is in allowed list
        if cmd not in self._allowed_commands:
            raise ValueError(
                f"Command '{cmd}' is not allowed. "
                f"Allowed: {sorted(self._allowed_commands)}"
            )

        # Prevent dangerous patterns
        dangerous = ["&&", "||", ";", "|", "`", "$(", "${"]
        for pattern in dangerous:
            if pattern in command:
                raise ValueError(f"Dangerous pattern '{pattern}' in command")

        return command

    async def execute(self, command: str) -> dict[str, Any]:
        """Execute a shell command and return output."""
        validated = self._validate_command(command)

        try:
            process = await asyncio.create_subprocess_shell(
                validated,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._workdir),
                env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin"},
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self._timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "status": "timeout",
                    "stdout": "",
                    "stderr": f"Command timed out after {self._timeout}s",
                    "return_code": -1,
                }

            stdout_str = stdout.decode("utf-8", errors="replace")[:self._max_output]
            stderr_str = stderr.decode("utf-8", errors="replace")[:self._max_output]

            return {
                "status": "success" if process.returncode == 0 else "error",
                "stdout": stdout_str,
                "stderr": stderr_str,
                "return_code": process.returncode,
            }

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
            }

    async def run_script(self, code: str, language: str = "python") -> dict[str, Any]:
        """Run a script in the specified language."""
        interpreters = {
            "python": ["python3", "-c"],
            "bash": ["bash", "-c"],
            "sh": ["sh", "-c"],
            "node": ["node", "-e"],
        }

        if language not in interpreters:
            return {
                "status": "error",
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "return_code": -1,
            }

        try:
            process = await asyncio.create_subprocess_exec(
                *interpreters[language],
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._workdir),
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._timeout
            )

            return {
                "status": "success" if process.returncode == 0 else "error",
                "stdout": stdout.decode("utf-8", errors="replace")[:self._max_output],
                "stderr": stderr.decode("utf-8", errors="replace")[:self._max_output],
                "return_code": process.returncode,
            }

        except asyncio.TimeoutError:
            process.kill()
            return {
                "status": "timeout",
                "stdout": "",
                "stderr": f"Script timed out after {self._timeout}s",
                "return_code": -1,
            }
        except Exception as e:
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
            }

    async def list_directory(self, path: str = ".") -> list[dict[str, Any]]:
        """List directory contents."""
        target = self._workdir / path
        if not target.exists():
            raise FileNotFoundError(f"Path not found: {target}")

        entries = []
        for entry in sorted(target.iterdir()):
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "path": str(entry.relative_to(self._workdir)),
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
        return entries

    async def read_file(self, path: str) -> str:
        """Read file contents."""
        target = self._workdir / path
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        if not target.is_file():
            raise IsADirectoryError(f"Not a file: {target}")

        return target.read_text(encoding="utf-8", errors="replace")

    async def write_file(self, path: str, content: str) -> bool:
        """Write content to a file."""
        target = self._workdir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return True

    async def monitor_process(self) -> list[dict[str, Any]]:
        """List running processes."""
        result = await self.execute("ps aux --sort=-%mem | head -20")
        if result["status"] == "success":
            lines = result["stdout"].strip().split("\n")
            processes = []
            for line in lines[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "user": parts[0],
                        "pid": int(parts[1]),
                        "cpu": float(parts[2]),
                        "memory": float(parts[3]),
                        "command": parts[10],
                    })
            return processes
        return []


# Plugin entrypoint
plugin = TerminalPlugin

__all__ = ["TerminalPlugin", "plugin"]
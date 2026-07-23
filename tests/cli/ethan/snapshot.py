"""Snapshot engine — capture CLI outputs as golden files."""
import hashlib
import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime


class SnapshotEngine:
    """Capture and manage CLI snapshots."""

    def __init__(self, snapshot_dir="tests/cli/ethan/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(
        self,
        command: str,
        argv: list[str],
        output: str,
        exit_code: int,
        metadata: Optional[dict] = None,
    ) -> str:
        """Capture command output and save as snapshot.

        Returns: snapshot file path
        """
        normalized = self._normalize(output)
        args_hash = hashlib.md5(" ".join(argv).encode()).hexdigest()[:8]
        filename = f"{command}__{args_hash}.txt"
        path = self.snapshot_dir / filename

        snapshot = self._format_snapshot(
            command=command,
            argv=argv,
            output=normalized,
            exit_code=exit_code,
            metadata=metadata or {},
        )
        path.write_text(snapshot)
        return str(path)

    def load(self, command: str, argv: list[str]) -> str | None:
        """Load existing snapshot for comparison."""
        args_hash = hashlib.md5(" ".join(argv).encode()).hexdigest()[:8]
        filename = f"{command}__{args_hash}.txt"
        path = self.snapshot_dir / filename
        if path.exists():
            return path.read_text()
        return None

    def _normalize(self, output: str) -> str:
        """Normalize output for comparison."""
        # Strip ANSI
        output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", output)
        # Normalize line endings
        output = output.replace("\r\n", "\n").replace("\r", "\n")
        # Replace session IDs, timestamps with placeholders
        output = re.sub(
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "<SESSION_ID>",
            output,
        )
        output = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "<TIMESTAMP>", output
        )
        # Normalize trailing whitespace
        output = "\n".join(line.rstrip() for line in output.split("\n"))
        return output.strip()

    def _format_snapshot(self, **kwargs) -> str:
        """Format snapshot with metadata header."""
        header = f"""# SNAPSHOT
# Command: {kwargs['command']} {' '.join(kwargs['argv'])}
# Exit code: {kwargs['exit_code']}
# Captured: <TIMESTAMP>
# Meta: {json.dumps(kwargs.get('metadata', {}))}
# ===

"""
        return header + kwargs["output"]

    def update_all(self, command_fn_map: dict) -> list[str]:
        """Update all snapshots for given commands.

        Args:
            command_fn_map: Dict mapping command names to callable(argv)

        Returns:
            List of updated snapshot paths
        """
        updated = []
        for command, fn in command_fn_map.items():
            argv = [command]
            try:
                exit_code, output = fn(argv)
            except Exception as e:
                exit_code = 1
                output = str(e)

            path = self.capture(command, argv, output, exit_code)
            updated.append(path)

        return updated
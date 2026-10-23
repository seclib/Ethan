"""UserModel — Modèle utilisateur dialectique."""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class UserModel:
    """Modèle utilisateur persisté, mis à jour après chaque échange."""

    def __init__(
        self,
        model_path: Path | None = None,
        llm_update_fn: Callable[[str], str] | None = None,
    ):
        self._path = model_path or Path.home() / ".ethan" / "user_model.md"
        self._llm = llm_update_fn

    def load(self) -> str:
        if not self._path.exists():
            return ""
        return self._path.read_text(encoding="utf-8").strip()

    def fire(self, user_message: str, assistant_message: str) -> None:
        if self._llm is None:
            return
        asyncio.create_task(self._update(user_message, assistant_message))

    async def _update(self, user: str, assistant: str) -> None:
        try:
            current = self.load()
            prompt = (
                f"Current model:\n{current or '(empty)'}\n\n"
                f"New exchange:\nUser: {user[:500]}\nAssistant: {assistant[:500]}\n\n"
                f"Update the user model with new observations. Max 300 words."
            )
            updated = await self._llm(prompt)
            text = str(updated).strip()
            if text:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._path.write_text(text, encoding="utf-8")
                logger.debug("UserModel updated")
        except Exception as e:
            logger.warning("UserModel: update failed: %s", e)
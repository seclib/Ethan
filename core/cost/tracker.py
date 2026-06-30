"""CostTracker — suivi des dépenses LLM et API.

Stocke les coûts dans PostgreSQL (table `cost_log`) ou fichier JSONL.
Permet de recharger l'historique pour le BudgetGuard.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_COST_DIR = Path.home() / ".ethan" / "costs"
_COST_FILE = _COST_DIR / "costs.jsonl"


class CostTracker:
    """Suivi des dépenses par jour et par scope."""

    def __init__(
        self,
        pg_conn: Any = None,
        jsonl_path: str | Path | None = None,
    ) -> None:
        self._pg_conn = pg_conn
        self._jsonl_path = Path(jsonl_path) if jsonl_path else _COST_FILE
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if self._pg_conn is not None:
            self._init_pg()
        else:
            self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_pg(self) -> None:
        try:
            cursor = self._pg_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cost_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    scope TEXT NOT NULL DEFAULT 'global',
                    scope_id TEXT NOT NULL DEFAULT '',
                    provider TEXT NOT NULL DEFAULT 'unknown',
                    model TEXT NOT NULL DEFAULT '',
                    tokens_input INTEGER NOT NULL DEFAULT 0,
                    tokens_output INTEGER NOT NULL DEFAULT 0,
                    cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                    context TEXT NOT NULL DEFAULT '',
                    metadata JSONB NOT NULL DEFAULT '{}'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_log(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cost_scope ON cost_log(scope, scope_id)
            """)
            self._pg_conn.commit()
            logger.info("CostTracker: PostgreSQL table cost_log ready")
        except Exception as e:
            logger.warning("CostTracker: PG init failed, fallback JSONL: %s", e)
            self._pg_conn = None
            self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        cost_usd: float,
        provider: str = "unknown",
        model: str = "",
        tokens_input: int = 0,
        tokens_output: int = 0,
        scope: str = "global",
        scope_id: str = "",
        context: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Enregistre une dépense."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "scope": scope,
            "scope_id": scope_id,
            "provider": provider,
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost_usd": round(cost_usd, 8),
            "context": context,
            "metadata": metadata or {},
        }

        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    """INSERT INTO cost_log
                       (timestamp, scope, scope_id, provider, model, tokens_input, tokens_output, cost_usd, context, metadata)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        entry["timestamp"],
                        entry["scope"],
                        entry["scope_id"],
                        entry["provider"],
                        entry["model"],
                        entry["tokens_input"],
                        entry["tokens_output"],
                        entry["cost_usd"],
                        entry["context"],
                        json.dumps(entry["metadata"]),
                    ),
                )
                self._pg_conn.commit()
            except Exception as e:
                logger.error("CostTracker: PG write failed: %s", e)
        else:
            try:
                with self._jsonl_path.open("a") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error("CostTracker: JSONL write failed: %s", e)

    def get_monthly_totals(self) -> dict[str, float]:
        """Retourne le total des coûts du mois courant."""
        today = date.today()
        first_of_month = today.replace(day=1)

        total_cost = 0.0
        total_input = 0
        total_output = 0
        by_provider: dict[str, float] = defaultdict(float)

        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    "SELECT provider, cost_usd, tokens_input, tokens_output FROM cost_log WHERE timestamp >= %s",
                    (first_of_month.isoformat(),),
                )
                for row in cursor.fetchall():
                    by_provider[row[0]] += float(row[1])
                    total_cost += float(row[1])
                    total_input += int(row[2])
                    total_output += int(row[3])
            except Exception as e:
                logger.warning("CostTracker: PG query failed: %s", e)
        elif self._jsonl_path.exists():
            try:
                with self._jsonl_path.open("r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            ts = datetime.fromisoformat(entry["timestamp"])
                            if ts.date() >= first_of_month:
                                cost = float(entry.get("cost_usd", 0))
                                total_cost += cost
                                total_input += int(entry.get("tokens_input", 0))
                                total_output += int(entry.get("tokens_output", 0))
                                by_provider[entry.get("provider", "unknown")] += cost
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
            except Exception as e:
                logger.warning("CostTracker: JSONL read failed: %s", e)

        return {
            "cost_usd": round(total_cost, 6),
            "tokens_input": total_input,
            "tokens_output": total_output,
            "by_provider": dict(by_provider),
        }

    def get_project_cost(self, project_id: str) -> float:
        """Retourne le coût total d'un projet."""
        total = 0.0
        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    "SELECT SUM(cost_usd) FROM cost_log WHERE scope='project' AND scope_id=%s",
                    (project_id,),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    total = float(row[0])
            except Exception:
                pass
        return round(total, 6)

    def get_daily_cost(self, day: date | None = None) -> float:
        """Retourne le coût d'un jour spécifique."""
        if day is None:
            day = date.today()
        total = 0.0
        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    "SELECT SUM(cost_usd) FROM cost_log WHERE timestamp::date = %s",
                    (day.isoformat(),),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    total = float(row[0])
            except Exception:
                pass
        return round(total, 6)
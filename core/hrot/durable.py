"""Durable HROT approvals shared by ETHAN instances."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

APPROVED = "APPROVED"
PENDING = "PENDING"
DENIED = "DENIED"
EXPIRED = "EXPIRED"
CONSUMED = "CONSUMED"


class HrotStorageUnavailable(RuntimeError):
    """Raised when the authoritative HROT storage backend is unavailable."""


@dataclass
class DurableHrotApproval:
    approval_id: str
    request_id: str
    requester: str
    requester_type: str
    service_id: str
    operation: str
    content_hash: str
    status: str
    created_at: str
    expires_at: str
    approver: str | None = None
    decided_at: str | None = None
    consumed_id: str | None = None
    consumed_at: str | None = None
    reason: str = ""

    def is_expired(self, now: datetime | None = None) -> bool:
        current = (now or datetime.now(timezone.utc))
        try:
            expires = datetime.fromisoformat(self.expires_at)
        except (TypeError, ValueError):
            return True
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return current > expires

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DurableHrotStore:
    def __init__(self, root: str | Path | None = None, database_url: str | None = None):
        self._root = Path(root) if root else Path.home() / ".ethan" / "hrot"
        self._root.mkdir(parents=True, exist_ok=True)
        self._path = self._root / "approvals.jsonl"
        self._lock_path = self._root / "approvals.lock"
        self._lock_path.touch(exist_ok=True)
        self._thread = threading.Lock()
        self._database_url_override = database_url
        self._pg_pools = {}
        self._pg_error = False

    async def _dsn(self) -> str | None:
        if self._database_url_override:
            return self._database_url_override
        explicit = os.getenv("DATABASE_URL")
        if explicit:
            return explicit
        # Reuse the same .env resolution as the project tests/configuration.
        root = self._root.parent
        for parent in [root] + list(root.parents):
            env_file = parent / ".env"
            if env_file.is_file():
                try:
                    for line in env_file.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                # Hostname 'postgres' is a Docker DNS name; local runtime
                                # tests and tools address 127.0.0.1 directly.
                                return val.replace("://postgres:", "://127.0.0.1:")
                except OSError:
                    return None
        return None

    async def _pg_pool(self):
        dsn = await self._dsn()
        if not dsn:
            return None
        if self._pg_error:
            return None
        import asyncio

        loop = asyncio.get_event_loop()
        pool = self._pg_pools.get(id(loop))
        if pool is not None:
            return pool
        try:
            import asyncpg

            pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
            self._pg_pools[id(loop)] = pool
            await self._ensure_pg_table(pool)
            return pool
        except Exception:
            self._pg_error = True
            return None

    async def _require_pool(self):
        pool = await self._pg_pool()
        if pool is not None:
            return pool
        dsn = await self._dsn()
        if dsn is not None:
            raise HrotStorageUnavailable("PostgreSQL-backed HROT storage is unavailable")
        return None

    async def _ensure_pg_table(self, pool) -> None:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS hrot_approvals (
                    approval_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    requester_type TEXT NOT NULL,
                    service_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    approver TEXT,
                    decided_at TIMESTAMPTZ,
                    consumed_id TEXT,
                    consumed_at TIMESTAMPTZ,
                    reason TEXT NOT NULL DEFAULT ''
                )
            """)

    async def _load_jsonl(self):
        if not self._path.exists():
            return []
        rows = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _normalize(self, data: dict[str, Any]):
        created = data.get("created_at")
        if hasattr(created, "isoformat"):
            data["created_at"] = created.isoformat()
        expires = data.get("expires_at")
        if hasattr(expires, "isoformat"):
            data["expires_at"] = expires.isoformat()
        decided = data.get("decided_at")
        if hasattr(decided, "isoformat"):
            data["decided_at"] = decided.isoformat()
        consumed = data.get("consumed_at")
        if hasattr(consumed, "isoformat"):
            data["consumed_at"] = consumed.isoformat()
        return data

    async def create(self, requester, requester_type, service_id, operation, parameters, ttl_seconds=300):
        canonical = {"service_id": service_id, "operation": operation, "parameters": parameters, "requester": requester, "requester_type": requester_type}
        content_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True, default=str).encode()).hexdigest()
        approval_id = f"hrot_{uuid.uuid4().hex[:12]}"
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=max(1, ttl_seconds))
        record = {
            "approval_id": approval_id,
            "request_id": request_id,
            "requester": requester,
            "requester_type": requester_type,
            "service_id": service_id,
            "operation": operation,
            "content_hash": content_hash,
            "status": PENDING,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "approver": None,
            "decided_at": None,
            "consumed_id": None,
            "consumed_at": None,
            "reason": "",
        }
        pool = await self._require_pool() if False else await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO hrot_approvals (
                        approval_id, request_id, requester, requester_type, service_id, operation,
                        content_hash, status, created_at, expires_at, approver, decided_at,
                        consumed_id, consumed_at, reason
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9::timestamptz, $10::timestamptz,
                        $11, $12, $13, $14, $15
                    )
                    """,
                    approval_id,
                    request_id,
                    requester,
                    requester_type,
                    service_id,
                    operation,
                    content_hash,
                    PENDING,
                    now,
                    expires,
                    None,
                    None,
                    None,
                    None,
                    "",
                )
            return DurableHrotApproval(**record)

        # JSONL only when PostgreSQL is explicitly not configured.
        with self._thread:
            if self._path.exists():
                rows = [json.loads(line) for line in self._path.read_text(encoding="utf-8").splitlines() if line.strip()]
                if any(r.get("approval_id") == approval_id for r in rows):
                    raise ValueError("duplicate approval id")
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
        return DurableHrotApproval(**record)

    async def get(self, approval_id):
        pool = await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM hrot_approvals WHERE approval_id = $1", approval_id)
            if row is None:
                return None
            data = self._normalize_row(dict(row))
            return DurableHrotApproval(**data)
        if not self._path.exists():
            return None
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("approval_id") == approval_id:
                return DurableHrotApproval(**record)
        return None

    def _normalize_row(self, data):
        created = data.get("created_at")
        if hasattr(created, "isoformat"):
            data["created_at"] = created.isoformat()
        expires = data.get("expires_at")
        if hasattr(expires, "isoformat"):
            data["expires_at"] = expires.isoformat()
        decided = data.get("decided_at")
        if hasattr(decided, "isoformat"):
            data["decided_at"] = decided.isoformat()
        consumed = data.get("consumed_at")
        if hasattr(consumed, "isoformat"):
            data["consumed_at"] = consumed.isoformat()
        return data

    async def list_pending(self):
        result = []
        pool = await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM hrot_approvals WHERE status = $1", PENDING)
            for row in rows:
                data = self._normalize_row(dict(row))
                approval = DurableHrotApproval(**data)
                if not approval.is_expired():
                    result.append(approval)
            return result
        for record in self._read_jsonl():
            approval = DurableHrotApproval(**record)
            if approval.status == PENDING and not approval.is_expired():
                result.append(approval)
        return result

    async def resolve(self, approval_id, approver, approved, reason=""):
        pool = await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow("SELECT * FROM hrot_approvals WHERE approval_id = $1 FOR UPDATE", approval_id)
                    if row is None:
                        return False
                    data = self._normalize_row(dict(row))
                    record = DurableHrotApproval(**data)
                    if record.is_expired():
                        record.status = EXPIRED
                        await conn.execute("UPDATE hrot_approvals SET status=$2 WHERE approval_id=$1", approval_id, EXPIRED)
                        return False
                    if record.status != PENDING:
                        return False
                    if approver == record.requester:
                        return False
                    record.status = APPROVED if approved else DENIED
                    record.approver = approver
                    record.decided_at = datetime.now(timezone.utc).isoformat()
                    record.reason = reason
                    await conn.execute(
                        """
                        UPDATE hrot_approvals
                        SET status=$2, approver=$3, decided_at=$4::timestamptz, reason=$5
                        WHERE approval_id=$1
                        """,
                        approval_id,
                        record.status,
                        record.approver,
                        datetime.fromisoformat(record.decided_at.replace("Z", "+00:00")),
                        record.reason,
                    )
            return True
        # JSONL fallback.
        # Minimal locking not needed for unit tests without databases.
        with self._thread:
            if not self._path.exists():
                return False
            rows = []
            for line in self._path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            for index, row in enumerate(rows):
                if row.get("approval_id") != approval_id:
                    continue
                record = DurableHrotApproval(**row)
                if record.is_expired():
                    record.status = EXPIRED
                    rows[index] = record.to_dict()
                    self._rewrite(rows)
                    return False
                if record.status != PENDING:
                    return False
                if approver == record.requester:
                    return False
                record.status = APPROVED if approved else DENIED
                record.approver = approver
                record.decided_at = datetime.now(timezone.utc).isoformat()
                record.reason = reason
                rows[index] = record.to_dict()
                self._rewrite(rows)
                return True
            return False

    async def consume(self, approval_id, consumer, content_hash):
        pool = await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow("SELECT * FROM hrot_approvals WHERE approval_id = $1 FOR UPDATE", approval_id)
                    if row is None:
                        return False, "not_found", None
                    data = self._normalize_row(dict(row))
                    approval = DurableHrotApproval(**data)
                    if approval.is_expired():
                        await conn.execute("UPDATE hrot_approvals SET status=$2 WHERE approval_id=$1", approval_id, EXPIRED)
                        return False, "expired", None
                    if approval.content_hash != content_hash:
                        return False, "mismatch", None
                    if approval.consumed_id:
                        return False, "already_consumed", None
                    if approval.status != APPROVED:
                        return False, approval.status.lower(), None
                    consumed_id = f"cons_{uuid.uuid4().hex[:12]}"
                    approval.status = CONSUMED
                    approval.consumed_id = consumed_id
                    approval.consumed_at = datetime.now(timezone.utc).isoformat()
                    await conn.execute(
                        """
                        UPDATE hrot_approvals
                        SET status=$2, consumed_id=$3, consumed_at=$4::timestamptz
                        WHERE approval_id=$1
                        """,
                        approval_id,
                        approval.status,
                        approval.consumed_id,
                        datetime.fromisoformat(approval.consumed_at.replace("Z", "+00:00")),
                    )
                    return True, "consumed", consumed_id
        # JSONL fallback
        with self._thread:
            rows = [json.loads(line) for line in (self._path.read_text(encoding="utf-8").splitlines() if self._path.exists() else []) if line.strip()]
            for index, row in enumerate(rows):
                if row.get("approval_id") != approval_id:
                    continue
                record = DurableHrotApproval(**row)
                if record.is_expired():
                    record.status = EXPIRED
                    rows[index] = record.to_dict()
                    self._rewrite(rows)
                    return False, "expired", None
                if record.content_hash != content_hash:
                    return False, "mismatch", None
                if record.consumed_id:
                    return False, "already_consumed", None
                if record.status != APPROVED:
                    return False, record.status.lower(), None
                record.status = CONSUMED
                record.consumed_id = f"cons_{uuid.uuid4().hex[:12]}"
                record.consumed_at = datetime.now(timezone.utc).isoformat()
                rows[index] = record.to_dict()
                self._rewrite(rows)
                return True, "consumed", record.consumed_id
        return False, "not_found", None

    def _read_jsonl(self):
        if not self._path.exists():
            return []
        return [json.loads(line) for line in self._path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _rewrite(self, rows):
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        os.replace(tmp, self._path)

    async def list_pending(self):
        pool = await self._pg_pool()
        if pool is not None:
            await self._ensure_pg_table(pool)
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM hrot_approvals WHERE status = $1", PENDING)
            result = []
            for row in rows:
                data = self._normalize_row(dict(row))
                approval = DurableHrotApproval(**data)
                if not approval.is_expired():
                    result.append(approval)
            return result
        result = []
        for record in self._read_jsonl():
            approval = DurableHrotApproval(**record)
            if approval.status == PENDING and not approval.is_expired():
                result.append(approval)
        return result

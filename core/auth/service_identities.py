"""Server-owned service identities for ETHAN.

This module implements the foundation layer only: persistent service registry
records, dedicated HMAC signing-key handling and strict JWT issuance/validation.

HTTP middleware integration, service provisioning workflows, AgentExecutor,
ToolContext and HROT are intentionally out of scope for this phase.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import secrets
import time
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jose import JWTError, jwt
from core.auth.principal import PrincipalType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

SERVICE_ISSUER = "ethan.service"
SERVICE_AUDIENCE = "ethan.internal"
SERVICE_ALGORITHM = "HS256"
SERVICE_KEY_ID = "service-hmac-v1"
SERVICE_TOKEN_MAX_TTL_SECONDS = 15 * 60
SERVICE_REGISTRY_DOMAIN = "service-identities"

SERVICE_KEY_ENV = "SERVICE_JWT_SECRET"
SERVICE_KEY_FILE = "service.key"

INSECURE_PLACEHOLDER = "change-me-in-prod-generate-a-random-secret-here"


def _repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(6):
        if (current / "pyproject.toml").is_file() or (current / "docker-compose.yml").is_file():
            return current
        current = current.parent
    return Path.cwd().resolve()


def _secrets_dir() -> Path:
    root = _repo_root()
    env_root = os.getenv("ETHAN_ROOT")
    if env_root and os.path.isdir(env_root):
        root = Path(env_root).resolve()
    secrets_dir = root / ".secrets"
    try:
        secrets_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(secrets_dir, 0o700)
        return secrets_dir
    except OSError:
        user_secrets = Path.home() / ".ethan" / "secrets"
        user_secrets.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(user_secrets, 0o700)
        except OSError:
            pass
        return user_secrets


def get_or_create_service_secret() -> str:
    """Resolve or create the dedicated HMAC secret used for service tokens.

    The secret is never logged, never embedded in images and never reused as
    the human JWT key.  It is persisted with restrictive permissions, exactly
    like the human JWT bootstrap secret.
    """
    env_secret = os.getenv(SERVICE_KEY_ENV, "").strip()
    if env_secret == INSECURE_PLACEHOLDER:
        raise RuntimeError("SERVICE_JWT_SECRET must not use the insecure placeholder")
    if env_secret:
        return env_secret

    key_file = _secrets_dir() / SERVICE_KEY_FILE
    if key_file.exists():
        try:
            stored = key_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"Could not read dedicated service secret from {key_file}: {exc}") from exc
        if not stored or stored == INSECURE_PLACEHOLDER:
            raise RuntimeError(f"Dedicated service secret at {key_file} is invalid or empty")
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass
        return stored

    new_secret = secrets.token_urlsafe(64)
    try:
        temp = key_file.with_suffix(key_file.suffix + ".tmp")
        temp.write_text(new_secret, encoding="utf-8")
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        os.replace(temp, key_file)
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass
        logger.info("Generated dedicated service signing secret at %s", key_file)
    except OSError as exc:
        raise RuntimeError(f"Could not persist dedicated service secret to {key_file}: {exc}") from exc
    return new_secret


def _validate_operation_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_status(value: str) -> str:
    status = str(value).strip().lower()
    if status not in ("active", "disabled", "revoked"):
        raise ValueError(f"unknown service status: {value!r}")
    return status


class ServiceRegistryError(Exception):
    """Base error for service registry authority operations."""


class ServiceRegistryUnavailable(ServiceRegistryError):
    """The service registry could not be read or written authoritatively."""


class ServiceRegistryConflict(ServiceRegistryError):
    """A concurrent update prevented this service mutation."""


class ServiceIdentityManager:
    """Persistent registry for service identities.

    The manager is the authority for service permissions. Token claims may only
    restrict, never widen, the operations returned by the registry.
    """

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        *,
        signing_secret: str | None = None,
    ) -> None:
        self._store = store or CoreRecordStore()
        self._secret = str(signing_secret).strip() if signing_secret else get_or_create_service_secret()
        self._locks: dict[str, threading.Lock] = {}

    @property
    def secret(self) -> str:
        """Signing secret. Callers must never log or transmit this value."""
        return self._secret

    async def _persist_record_pg(
        self,
        sid: str,
        record: dict[str, Any],
        *,
        expected_version: int | None = None,
    ) -> None:
        pg = getattr(self._store, "_pg", None)
        if pg is None:
            await self._store.save(SERVICE_REGISTRY_DOMAIN, sid, record)
            return

        async with pg.acquire() as conn:
            async with conn.transaction():
                if expected_version is None:
                    row = await conn.fetchrow(
                        "SELECT 1 FROM core_domain_records WHERE domain = $1 AND record_id = $2",
                        SERVICE_REGISTRY_DOMAIN,
                        sid,
                    )
                    if row is not None:
                        raise ServiceRegistryConflict(f"service identity already exists: {sid}")
                    await conn.execute(
                        """
                        INSERT INTO core_domain_records (domain, record_id, record, updated_at)
                        VALUES ($1, $2, $3::jsonb, NOW())
                        """,
                        SERVICE_REGISTRY_DOMAIN,
                        sid,
                        json.dumps(record),
                    )
                else:
                    result = await conn.execute(
                        """
                        UPDATE core_domain_records
                        SET record = $3::jsonb, updated_at = NOW()
                        WHERE domain = $1 AND record_id = $2
                          AND (record ->> 'version')::int = $4
                        """,
                        SERVICE_REGISTRY_DOMAIN,
                        sid,
                        json.dumps(record),
                        expected_version,
                    )
                    if str(result) != "UPDATE 1":
                        raise ServiceRegistryConflict(f"concurrent update for service identity: {sid}")

        self._store._memory[(SERVICE_REGISTRY_DOMAIN, sid)] = self._store._clone(record)
        redis = getattr(self._store, "_redis", None)
        if redis is not None:
            try:
                await redis.set(
                    self._store._cache_key(SERVICE_REGISTRY_DOMAIN, sid),
                    json.dumps(record),
                    ex=getattr(self._store, "_cache_ttl", 300),
                )
            except Exception as exc:  # noqa: BLE001 - cache is not authoritative
                logger.debug("Service registry cache refresh failed: %s", exc)

    async def _mutate_service(
        self,
        service_id: str,
        mutator: Any,
        *,
        require_active: bool = True,
    ) -> dict[str, Any] | None:
        if not isinstance(service_id, str) or not service_id.strip():
            return None
        sid = service_id.strip()
        with self._lock_for(sid):
            record = await self.service_record(sid)
            if not isinstance(record, dict):
                return None
            if require_active and record.get("status") != "active":
                return None
            expected_version = int(record.get("version", 1))
            mutator(record)
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            record["version"] = expected_version + 1
            await self._persist_record_pg(sid, record, expected_version=expected_version)
            return record

    async def create_service(
        self,
        service_id: str,
        component: str,
        allowed_operations: list[str] | tuple[str, ...],
        *,
        created_by: str = "system",
        status: str = "active",
    ) -> dict[str, Any]:
        """Create an authoritative registry entry.

        Creation is administrative: there is no self-registration path.
        """
        service_id = _validate_operation_name(service_id, "service_id")
        component = _validate_operation_name(component, "component")
        status_value = _validate_status(status)
        operations = [
            _validate_operation_name(operation, "allowed_operations")
            for operation in allowed_operations
        ]
        if "admin" in {operation.lower() for operation in operations}:
            raise ValueError("SERVICE identities may not include administrative operations")
        with self._lock_for(service_id):
            if await self.service_record(service_id) is not None:
                raise ValueError(f"service identity already exists: {service_id}")

            now = datetime.now(timezone.utc).isoformat()
            record = {
                "service_id": service_id,
                "component": component,
                "credential_id": str(uuid.uuid4()),
                "rotation_id": str(uuid.uuid4()),
                "status": status_value,
                "allowed_operations": sorted(set(operations)),
                "created_at": now,
                "updated_at": now,
                "created_by": _validate_operation_name(created_by, "created_by"),
                "version": 1,
            }
            await self._persist_record_pg(service_id, record, expected_version=None)
            logger.info("Created service identity %s for component %s", service_id, component)
            return record

    async def service_record(self, service_id: str) -> dict[str, Any] | None:
        if not isinstance(service_id, str) or not service_id.strip():
            return None
        sid = service_id.strip()
        pg = getattr(self._store, "_pg", None)
        if pg is not None:
            try:
                row = await pg.fetchrow(
                    "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2",
                    SERVICE_REGISTRY_DOMAIN,
                    sid,
                )
            except Exception as exc:  # noqa: BLE001 - storage failure must remain visible
                logger.warning("Service registry authority unavailable for %s: %s", sid, exc)
                raise ServiceRegistryUnavailable(f"service registry unavailable: {sid}") from exc
            if row is None:
                return None
            return self._store._decode(row["record"])

        try:
            return await self._store.get(SERVICE_REGISTRY_DOMAIN, sid)
        except Exception as exc:  # noqa: BLE001 - in-memory storage failure is unavailable
            logger.warning("Service registry authority unavailable for %s: %s", sid, exc)
            raise ServiceRegistryUnavailable(f"service registry unavailable: {sid}") from exc

    def _lock_for(self, service_id: str) -> threading.Lock:
        lock = self._locks.get(service_id)
        if lock is None:
            lock = threading.Lock()
            self._locks[service_id] = lock
        return lock

    async def _atomic_rotate_pg(
        self,
        sid: str,
        key: str | None,
        initial_record: dict[str, Any],
    ) -> tuple[str, dict[str, Any] | None]:
        pg = getattr(self._store, "_pg", None)
        if pg is None:
            return "fallback", None

        async with pg.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2 FOR UPDATE",
                    SERVICE_REGISTRY_DOMAIN,
                    sid,
                )
                if row is None:
                    return "missing", None
                service = self._store._decode(row["record"])
                if not isinstance(service, dict) or service.get("status") != "active":
                    return "inactive", None

                operation_id = None
                if key:
                    operation_id = ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key)
                    op_row = await conn.fetchrow(
                        "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2 FOR UPDATE",
                        "service-admin-operations",
                        operation_id,
                    )
                    if isinstance(op_row, dict) or op_row is not None:
                        operation = self._store._decode(op_row["record"])
                        if isinstance(operation.get("result"), dict):
                            result = operation["result"]
                            return ("recovered", self._rotate_result(service, result))

                expected_version = int(service.get("version", 1))
                old_credential_id = service.get("credential_id")
                new_credential_id = str(uuid.uuid4())
                new_rotation_id = str(uuid.uuid4())
                service["credential_id"] = new_credential_id
                service["rotation_id"] = new_rotation_id
                service["updated_at"] = datetime.now(timezone.utc).isoformat()
                service["version"] = expected_version + 1
                if key is not None:
                    service["last_rotation_request_id"] = key

                result = await conn.execute(
                    """
                    UPDATE core_domain_records
                    SET record = $3::jsonb, updated_at = NOW()
                    WHERE domain = $1 AND record_id = $2
                      AND (record ->> 'version')::int = $4
                    """,
                    SERVICE_REGISTRY_DOMAIN,
                    sid,
                    json.dumps(service),
                    expected_version,
                )
                if str(result) != "UPDATE 1":
                    return "conflict", None

                if key:
                    operation_record = {
                        "operation_id": operation_id,
                        "service_id": sid,
                        "operation": "rotate_credential",
                        "request_key": key,
                        "status": "completed",
                        "result": {
                            "credential_id": new_credential_id,
                            "rotation_id": new_rotation_id,
                            "version": expected_version + 1,
                        },
                        "version": 1,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    await conn.execute(
                        """
                        INSERT INTO core_domain_records (domain, record_id, record, updated_at)
                        VALUES ($1, $2, $3::jsonb, NOW())
                        ON CONFLICT (domain, record_id) DO UPDATE
                        SET record = EXCLUDED.record, updated_at = NOW()
                        """,
                        "service-admin-operations",
                        operation_id,
                        json.dumps(operation_record),
                    )
                return "rotated", service

        self._store._memory[(SERVICE_REGISTRY_DOMAIN, sid)] = self._store._clone(service)
        return "local-fallback", service

    async def list_services(self) -> list[dict[str, Any]]:
        records = await self._store.list(SERVICE_REGISTRY_DOMAIN)
        return [record for record in records if isinstance(record, dict)]

    async def disable_service(self, service_id: str) -> dict[str, Any] | None:
        return await self._update_status(service_id, "disabled")

    async def revoke_service(self, service_id: str) -> dict[str, Any] | None:
        return await self._update_status(service_id, "revoked")

    @staticmethod
    @staticmethod
    def _rotate_result(service_record: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        return {
            "service_id": service_record.get("service_id"),
            "component": service_record.get("component"),
            "status": service_record.get("status"),
            "allowed_operations": service_record.get("allowed_operations", []),
            "credential_id": result.get("credential_id"),
            "rotation_id": result.get("rotation_id"),
            "version": result.get("version"),
        }

    @staticmethod
    def _admin_operation_id(service_id: str, operation: str, key: str) -> str:
        return "admin-operation:" + hashlib.sha256(
            f"{service_id}:{operation}:{key}".encode("utf-8")
        ).hexdigest()

    async def _admin_operation_record(self, operation_id: str) -> dict[str, Any] | None:
        pg = getattr(self._store, "_pg", None)
        if pg is not None:
            try:
                row = await pg.fetchrow(
                    "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2",
                    "service-admin-operations",
                    operation_id,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Service admin operation registry unavailable for %s: %s", operation_id, exc)
                raise ServiceRegistryUnavailable(f"service admin operation registry unavailable: {operation_id}") from exc
            if row is None:
                return None
            return self._store._decode(row["record"])

        try:
            return await self._store.get("service-admin-operations", operation_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Service admin operation registry unavailable for %s: %s", operation_id, exc)
            raise ServiceRegistryUnavailable(f"service admin operation registry unavailable: {operation_id}") from exc

    async def _persist_admin_operation(
        self,
        operation_id: str,
        *,
        expected_version: int | None,
        record: dict[str, Any],
    ) -> bool:
        pg = getattr(self._store, "_pg", None)
        if pg is not None:
            async with pg.acquire() as conn:
                async with conn.transaction():
                    if expected_version is None:
                        row = await conn.fetchrow(
                            "SELECT 1 FROM core_domain_records WHERE domain = $1 AND record_id = $2",
                            "service-admin-operations",
                            operation_id,
                        )
                        if row is not None:
                            return False
                        await conn.execute(
                            "INSERT INTO core_domain_records (domain, record_id, record, updated_at) VALUES ($1, $2, $3::jsonb, NOW())",
                            "service-admin-operations",
                            operation_id,
                            json.dumps(record),
                        )
                    else:
                        result = await conn.execute(
                            "UPDATE core_domain_records SET record = $3::jsonb, updated_at = NOW() WHERE domain = $1 AND record_id = $2 AND (record ->> 'version')::int = $4",
                            "service-admin-operations",
                            operation_id,
                            json.dumps(record),
                            expected_version,
                        )
                        if str(result) != "UPDATE 1":
                            return False
            self._store._memory[("service-admin-operations", operation_id)] = self._store._clone(record)
            return True

        existing = await self._store.get("service-admin-operations", operation_id)
        if expected_version is None and isinstance(existing, dict):
            return False
        await self._store.save("service-admin-operations", operation_id, record)
        return True


    async def rotate_credential(
        self,
        service_id: str,
        *,
        request_key: str | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(service_id, str) or not service_id.strip():
            return None
        sid = service_id.strip()
        key = None if request_key is None else str(request_key).strip() or None

        pg = getattr(self._store, "_pg", None)
        if pg is None:
            with self._lock_for(sid):
                initial_record = await self.service_record(sid)
                if not isinstance(initial_record, dict):
                    return None
                if initial_record.get("status") != "active":
                    return None
                if key:
                    operation_id = ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key)
                    stored_operation = await self._admin_operation_record(operation_id)
                    if (
                        isinstance(stored_operation, dict)
                        and isinstance(stored_operation.get("result"), dict)
                    ):
                        result = stored_operation["result"]
                        return ServiceIdentityManager._rotate_result(initial_record, result)

                expected_version = int(initial_record.get("version", 1))
                updated_record = dict(initial_record)
                updated_record["credential_id"] = str(uuid.uuid4())
                updated_record["rotation_id"] = str(uuid.uuid4())
                updated_record["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated_record["version"] = expected_version + 1
                if key is not None:
                    updated_record["last_rotation_request_id"] = key

                try:
                    await self._persist_record_pg(sid, updated_record, expected_version=expected_version)
                except ServiceRegistryConflict:
                    winner = await self.service_record(sid)
                    if isinstance(winner, dict) and key is not None and winner.get("last_rotation_request_id") == key:
                        return winner
                    return None

                if key:
                    operation_id = ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key)
                    operation_record = {
                        "operation_id": operation_id,
                        "service_id": sid,
                        "operation": "rotate_credential",
                        "request_key": key,
                        "status": "completed",
                        "result": {
                            "credential_id": updated_record["credential_id"],
                            "rotation_id": updated_record["rotation_id"],
                            "version": updated_record["version"],
                        },
                        "version": 1,
                        "created_at": updated_record["updated_at"],
                    }
                    await self._persist_admin_operation(
                        operation_id,
                        expected_version=None,
                        record=operation_record,
                    )
                return updated_record

        return await self._atomic_rotate_pg(sid, key)

    async def _atomic_rotate_pg(
        self,
        sid: str,
        key: str | None,
    ) -> dict[str, Any] | None:
        pg = getattr(self._store, "_pg", None)
        if pg is None:
            return None
        async with pg.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2 FOR UPDATE",
                    "service-identities",
                    sid,
                )
                if row is None:
                    return None
                service = self._store._decode(row["record"])
                if not isinstance(service, dict) or service.get("status") != "active":
                    return None
                if key:
                    operation_id = ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key)
                    op_row = await conn.fetchrow(
                        "SELECT record FROM core_domain_records WHERE domain = $1 AND record_id = $2 FOR UPDATE",
                        "service-admin-operations",
                        operation_id,
                    )
                    if op_row is not None:
                        operation = self._store._decode(op_row["record"])
                        if isinstance(operation.get("result"), dict):
                            return ServiceIdentityManager._rotate_result(service, operation["result"])
                        if str(operation.get("status") or "").strip().lower() == "pending":
                            # Never re-run a mutation whose previous attempt is
                            # unresolved; the operation must be investigated.
                            return None
                old_version = int(service.get("version", 1))
                new_credential_id = str(uuid.uuid4())
                new_rotation_id = str(uuid.uuid4())
                service["credential_id"] = new_credential_id
                service["rotation_id"] = new_rotation_id
                service["updated_at"] = datetime.now(timezone.utc).isoformat()
                service["version"] = old_version + 1
                if key is not None:
                    service["last_rotation_request_id"] = key
                result = await conn.execute(
                    "UPDATE core_domain_records SET record = $3::jsonb, updated_at = NOW() WHERE domain = $1 AND record_id = $2 AND (record ->> \'version\')::int = $4",
                    "service-identities",
                    sid,
                    json.dumps(service),
                    old_version,
                )
                if str(result) != "UPDATE 1":
                    raise ServiceRegistryConflict(f"concurrent rotation for service identity: {sid}")
                if key:
                    operation_id = ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key)
                    operation_record = {
                        "operation_id": operation_id,
                        "service_id": sid,
                        "operation": "rotate_credential",
                        "request_key": key,
                        "status": "completed",
                        "result": {
                            "credential_id": new_credential_id,
                            "rotation_id": new_rotation_id,
                            "version": old_version + 1,
                        },
                        "version": 1,
                        "created_at": service["updated_at"],
                    }
                    await conn.execute(
                        """
                        INSERT INTO core_domain_records (domain, record_id, record, updated_at)
                        VALUES ($1, $2, $3::jsonb, NOW())
                        ON CONFLICT (domain, record_id) DO UPDATE
                        SET record = EXCLUDED.record, updated_at = NOW()
                        """,
                        "service-admin-operations",
                        operation_id,
                        json.dumps(operation_record),
                    )
                self._store._memory[("service-identities", sid)] = self._store._clone(service)
                if key:
                    self._store._memory[("service-admin-operations", ServiceIdentityManager._admin_operation_id(sid, "rotate_credential", key))] = self._store._clone(operation_record)
                return service

    async def update_allowed_operations(
        self,
        service_id: str,
        allowed_operations: list[str] | tuple[str, ...],
    ) -> dict[str, Any] | None:
        service_key = service_id.strip() if isinstance(service_id, str) else service_id
        with self._lock_for(service_key):
            record = await self.service_record(service_id)
            if not isinstance(record, dict) or record.get("status") != "active":
                return None
            operations = [
                _validate_operation_name(operation, "allowed_operations")
                for operation in allowed_operations
            ]
            if "admin" in {operation.lower() for operation in operations}:
                raise ValueError("SERVICE identities may not include administrative operations")
            old_version = int(record.get("version", 1))
            record["allowed_operations"] = sorted(set(operations))
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            record["version"] = old_version + 1
            await self._persist_record_pg(
                service_id,
                record,
                expected_version=old_version,
            )
            return record

    async def issue_token(
        self,
        service_id: str,
        *,
        allowed_operations: list[str] | tuple[str, ...] | None = None,
        ttl_seconds: int = SERVICE_TOKEN_MAX_TTL_SECONDS,
    ) -> str:
        record = await self.service_record(service_id)
        if not isinstance(record, dict) or record.get("status") != "active":
            raise ValueError("active service identity is required to issue a token")

        registry_operations = set(record.get("allowed_operations") or [])
        requested_operations = registry_operations
        if allowed_operations is not None:
            requested_operations = registry_operations & {
                _validate_operation_name(operation, "allowed_operations")
                for operation in allowed_operations
            }
        requested_operations -= {"admin", "Admin", "ADMIN"}
        if not requested_operations:
            raise ValueError("effective service operations are empty")
        if any(operation.lower() == "admin" for operation in requested_operations):
            raise ValueError("SERVICE tokens may not carry administrative operations")

        ttl = min(int(ttl_seconds), SERVICE_TOKEN_MAX_TTL_SECONDS)
        if ttl <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = int(time.time())
        payload = {
            "typ": "service",
            "iss": SERVICE_ISSUER,
            "aud": SERVICE_AUDIENCE,
            "sub": service_id,
            "service_id": service_id,
            "component": record.get("component"),
            "credential_id": record.get("credential_id"),
            "rotation_id": record.get("rotation_id"),
            "allowed_operations": sorted(requested_operations),
            "iat": now,
            "exp": now + ttl,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(
            payload,
            self._secret,
            algorithm=SERVICE_ALGORITHM,
            headers={"kid": SERVICE_KEY_ID},
        )

    async def _update_status(self, service_id: str, status: str) -> dict[str, Any] | None:
        service_key = service_id.strip() if isinstance(service_id, str) else service_id
        with self._lock_for(service_key):
            record = await self.service_record(service_id)
            if not isinstance(record, dict):
                return None
            old_version = int(record.get("version", 1))
            record["status"] = status
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            record["version"] = old_version + 1
            await self._persist_record_pg(
                service_id,
                record,
                expected_version=old_version,
            )
            return record


class ServiceTokenValidator:
    """Strict validator for service JWTs."""

    def __init__(
        self,
        registry: ServiceIdentityManager,
        *,
        signing_secret: str | None = None,
        key_id: str = SERVICE_KEY_ID,
        issuer: str = SERVICE_ISSUER,
        audience: str = SERVICE_AUDIENCE,
        max_ttl_seconds: int = SERVICE_TOKEN_MAX_TTL_SECONDS,
    ) -> None:
        self.registry = registry
        self._secret = str(signing_secret).strip() if signing_secret else registry.secret
        self.key_id = key_id
        self.issuer = issuer
        self.audience = audience
        self.max_ttl_seconds = max_ttl_seconds

    async def validate(
        self,
        token: str,
        *,
        required_operation: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Return ``(record, payload)`` if valid, otherwise ``None``.

        Validation is fail-closed. Registry unavailability is represented by
        ``None``; callers must not convert that into a valid identity.
        """
        if not isinstance(token, str) or not token.strip():
            return None

        try:
            header = jwt.get_unverified_header(token)
        except JWTError:
            return None

        if header.get("alg") != SERVICE_ALGORITHM or header.get("typ", "").upper() != "JWT":
            return None
        if header.get("kid") != self.key_id:
            return None

        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[SERVICE_ALGORITHM],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": False,
                    "verify_iss": True,
                    "verify_aud": True,
                    "require": ["exp", "iat", "jti", "iss", "aud", "typ", "sub", "service_id"],
                },
            )
        except JWTError:
            return None

        if payload.get("typ") != "service":
            return None
        if payload.get("iss") != self.issuer or payload.get("aud") != self.audience:
            return None

        service_id = str(payload.get("service_id") or "").strip()
        component = str(payload.get("component") or "").strip()
        credential_id = str(payload.get("credential_id") or "").strip()
        rotation_id = str(payload.get("rotation_id") or "").strip()
        jti = str(payload.get("jti") or "").strip()
        if not service_id or not component or not credential_id or not rotation_id or not jti:
            return None

        try:
            issued_at = int(payload.get("iat"))
            expires_at = int(payload.get("exp"))
        except (TypeError, ValueError):
            return None
        now = int(time.time())
        if issued_at > now + 5:
            return None
        if expires_at - issued_at <= 0 or expires_at - issued_at > self.max_ttl_seconds:
            return None
        if expires_at <= now:
            return None

        record = await self.registry.service_record(service_id)
        if not isinstance(record, dict):
            return None
        if record.get("status") != "active":
            return None
        if credential_id != record.get("credential_id"):
            return None
        if rotation_id != record.get("rotation_id"):
            return None
        if component != record.get("component"):
            return None

        token_operations = {
            str(operation).strip()
            for operation in (payload.get("allowed_operations") or [])
            if str(operation).strip()
        }
        registry_operations = {
            str(operation).strip()
            for operation in (record.get("allowed_operations") or [])
            if str(operation).strip()
        }
        if any(operation.lower() == "admin" for operation in token_operations | registry_operations):
            return None
        if token_operations and not token_operations.issubset(registry_operations):
            return None
        effective_operations = registry_operations & (token_operations or registry_operations)
        if not effective_operations:
            return None
        if required_operation and required_operation not in effective_operations:
            return None

        return record, payload

    @staticmethod
    def payload_to_principal(
        record: dict[str, Any],
        payload: dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> None:
        """Reserved for later HTTP integration phases.

        The principal construction for SERVICE belongs with the middleware once
        service authentication is wired.  Keeping this placeholder here documents
        that dependency without prematurely changing HTTP contracts.
        """
        if not isinstance(record, dict) or not isinstance(payload, dict):
            raise ValueError("service validation result is required")
        if PrincipalType.SERVICE.value != PrincipalType.SERVICE.value:
            raise ValueError("invalid principal type")


# Compatibility alias used by future phases.
ServiceRegistry = ServiceIdentityManager
ServiceTokenIssuer = ServiceIdentityManager

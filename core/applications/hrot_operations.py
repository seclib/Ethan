"""Operational HROT components for ETHAN (MEM-014 Phase 11)."""

from __future__ import annotations

import base64
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from uuid import uuid4

from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.applications.hrot_crypto import (
    HrotProofStatus,
    Ed25519HumanSigner,
    Ed25519HumanVerifier,
    Ed25519TrustedKey,
    HrotApprovalContext,
    HrotApprovalProof,
)
from core.applications.persistence import ApplicationStateStore
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class HrotOperationalError(ValueError):
    """Raised for operational HROT errors."""


class HrotOperationStatus(StrEnum):
    PENDING = "pending"
    PRESENTED = "presented"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIGNED = "signed"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass(slots=True)
class TrustedKeyReference:
    key_id: str
    authority_id: str
    public_key_b64: str
    is_active: bool = True
    is_revoked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HrotApprovalRequest:
    request_id: str
    app_id: str
    instance_id: str
    capability: str
    permission: str
    resource: str
    action: str
    context: dict[str, Any] = field(default_factory=dict)
    human_authority_id: str = "human"
    manifest_fingerprint: str | None = None
    contract_fingerprint: str | None = None
    capability_version: str | None = None
    contract_version: str | None = None
    status: HrotOperationStatus = HrotOperationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    def validate(self) -> None:
        if not self.request_id.strip():
            raise HrotOperationalError("request_id is required")
        if not self.app_id.strip() or not self.instance_id.strip():
            raise HrotOperationalError("application identity is required")
        if not self.capability.strip() or not self.permission.strip():
            raise HrotOperationalError("capability and permission are required")
        if not self.resource.strip() or not self.action.strip():
            raise HrotOperationalError("resource and action are required")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise HrotOperationalError("expires_at must be after created_at")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["expires_at"] = None if self.expires_at is None else self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HrotApprovalRequest":
        return cls(
            request_id=str(data["request_id"]),
            app_id=str(data["app_id"]),
            instance_id=str(data["instance_id"]),
            capability=str(data["capability"]),
            permission=str(data["permission"]),
            resource=str(data["resource"]),
            action=str(data["action"]),
            context=dict(data.get("context", {})),
            human_authority_id=str(data.get("human_authority_id", "human")),
            manifest_fingerprint=data.get("manifest_fingerprint"),
            contract_fingerprint=data.get("contract_fingerprint"),
            capability_version=data.get("capability_version"),
            contract_version=data.get("contract_version"),
            status=HrotOperationStatus(str(data.get("status", "pending"))),
            created_at=datetime.fromisoformat(str(data["created_at"]).replace("Z", "+00:00")),
            expires_at=None if data.get("expires_at") is None else datetime.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00")),
        )


class HrotKeyStorage(Protocol):
    """Interface for a trusted key-storage component."""

    def available(self) -> bool: ...
    def reference(self) -> TrustedKeyReference | None: ...
    def sign(self, request: HrotApprovalRequest, nonce: str, ttl: object) -> bytes: ...
    def verify_access(self) -> bool: ...


class SoftwareEncryptedKeyStorage:
    """A passphrase-protected software key store.

    This is a convenience implementation for isolated environments. It is not
    equivalent to a hardware security module, TPM or OS secret service.
    """

    def __init__(self, path: str | Path, salt_path: str | Path | None = None) -> None:
        self.path = Path(path)
        self.salt_path = Path(salt_path) if salt_path is not None else self.path.with_suffix(self.path.suffix + ".salt")
        self._private_key: Ed25519PrivateKey | None = None
        self._key_id: str | None = None
        self._authority_id: str | None = None

    def available(self) -> bool:
        return self.path.exists() and self.salt_path.exists()

    def generate(self, key_id: str, authority_id: str, passphrase: str) -> TrustedKeyReference:
        # Explicit human-initiated generation only.
        salt = os.urandom(16)
        self.salt_path.write_bytes(salt)
        self.salt_path.chmod(0o600)
        private_key = Ed25519PrivateKey.generate()
        encrypted = _encrypt_private_key(private_key, passphrase, salt)
        self.path.write_bytes(encrypted)
        self.path.chmod(0o600)
        self._private_key = private_key
        self._key_id = key_id
        self._authority_id = authority_id
        self._write_reference(key_id, authority_id, private_key.public_key())
        return TrustedKeyReference(
            key_id=key_id,
            authority_id=authority_id,
            public_key_b64=_public_key_b64(private_key.public_key()),
        )

    def unlock(self, passphrase: str) -> bool:
        if not self.available():
            return False
        salt = self.salt_path.read_bytes()
        encrypted = self.path.read_bytes()
        try:
            private_key_bytes = _decrypt_private_key(encrypted, passphrase, salt)
        except InvalidToken:
            return False
        # Ed25519 private keys are 32 bytes; cryptography accepts the seed.
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        self._private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes[:32])
        _ = self
        metadata = self._read_reference()
        self._key_id = metadata.get("key_id")
        self._authority_id = metadata.get("authority_id")
        return True

    def lock(self) -> None:
        self._private_key = None

    def reference(self) -> TrustedKeyReference | None:
        metadata = self._read_reference() if self.path.exists() else None
        if metadata is None:
            return None
        return TrustedKeyReference(
            key_id=metadata["key_id"],
            authority_id=metadata["authority_id"],
            public_key_b64=metadata["public_key_b64"],
            is_active=metadata.get("is_active", True),
            is_revoked=metadata.get("is_revoked", False),
        )

    def verify_access(self) -> bool:
        return self._private_key is not None

    def sign(self, request: HrotApprovalRequest, issued_at: datetime, expires_at: datetime, nonce: str) -> bytes:
        if self._private_key is None:
            raise HrotOperationalError("key storage is locked")
        ref = self.reference()
        if ref is None or ref.is_revoked:
            raise HrotOperationalError("signing key is unavailable or revoked")
        context = HrotApprovalContext(
            approval_id=request.request_id,
            human_authority_id=request.human_authority_id,
            app_id=request.app_id,
            instance_id=request.instance_id,
            capability=request.capability,
            permission=request.permission,
            resource=request.resource,
            action=request.action,
            context_fingerprint=HrotApprovalContext.fingerprint_context(request.context),
            manifest_fingerprint=request.manifest_fingerprint,
            contract_fingerprint=request.contract_fingerprint,
            capability_version=request.capability_version,
            contract_version=request.contract_version,
            issued_at=issued_at,
            expires_at=expires_at,
            nonce=nonce,
        )
        signer = Ed25519HumanSigner(self._private_key, key_id=ref.key_id, authority_id=ref.authority_id)
        proof = signer.sign(context)
        # Only the signature bytes are returned; the signer never releases the key.
        return proof.signature

    def _write_reference(self, key_id: str, authority_id: str, public_key) -> None:
        metadata = {
            "key_id": key_id,
            "authority_id": authority_id,
            "public_key_b64": _public_key_b64(public_key),
            "is_active": True,
            "is_revoked": False,
        }
        ref_path = self.path.with_suffix(self.path.suffix + ".pub")
        ref_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
        ref_path.chmod(0o600)

    def _read_reference(self) -> dict[str, Any] | None:
        ref_path = self.path.with_suffix(self.path.suffix + ".pub")
        if not ref_path.exists():
            return None
        try:
            return json.loads(ref_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None


@dataclass(slots=True)
class HrotTrustStore:
    """Persistence helper for proof consumption and revocation."""

    store: ApplicationStateStore

    def is_consumed(self, proof_id: str) -> bool:
        try:
            return any(record.get("proof_id") == proof_id for record in self.store.load_records("hrot_consumed_proofs"))
        except Exception:
            return False

    def consume(self, proof_id: str, consumed_at: datetime | None = None) -> None:
        when = consumed_at or datetime.now(timezone.utc)
        self.store.save_record("hrot_consumed_proofs", proof_id, {
            "proof_id": proof_id,
            "consumed_at": when.isoformat(),
        })

    def is_key_revoked(self, key_id: str) -> bool:
        try:
            return any(record.get("key_id") == key_id for record in self.store.load_records("hrot_revoked_keys"))
        except Exception:
            return False

    def revoke_key(self, key_id: str, reason: str = "", revoked_at: datetime | None = None) -> None:
        when = revoked_at or datetime.now(timezone.utc)
        self.store.save_record("hrot_revoked_keys", key_id, {
            "key_id": key_id,
            "reason": reason,
            "revoked_at": when.isoformat(),
        })

    def save_request(self, request: HrotApprovalRequest) -> None:
        self.store.save_record("hrot_approval_requests", request.request_id, request.to_dict())

    def get_request(self, request_id: str) -> HrotApprovalRequest | None:
        for payload in self.store.load_records("hrot_approval_requests"):
            if payload.get("request_id") == request_id:
                try:
                    return HrotApprovalRequest.from_dict(payload)
                except Exception:
                    return None
        return None


@dataclass(slots=True)
class OperationalHrotService:
    """Facade for operational approval without exposing private keys."""

    key_storage: HrotKeyStorage
    trust_store: HrotTrustStore
    verifier: Ed25519HumanVerifier | None = None
    policy: dict[str, Any] = field(default_factory=dict)

    def create_request(self, request: HrotApprovalRequest) -> HrotApprovalRequest:
        request.validate()
        self.trust_store.save_request(request)
        return request

    def present(self, request_id: str) -> HrotApprovalRequest | None:
        request = self.trust_store.get_request(request_id)
        if request is None:
            return None
        if request.status == HrotOperationStatus.PENDING:
            request.status = HrotOperationStatus.PRESENTED
            self.trust_store.save_request(request)
        return request

    def approve_and_sign(
        self,
        request_id: str,
        passphrase: str | None = None,
        ttl_seconds: int = 300,
        *,
        nonce: str | None = None,
    ) -> HrotApprovalProof:
        request = self.trust_store.get_request(request_id)
        if request is None:
            raise HrotOperationalError(f"unknown request: {request_id}")
        if request.status not in {HrotOperationStatus.PENDING, HrotOperationStatus.PRESENTED}:
            raise HrotOperationalError(f"request is not approvable: {request.status.value}")
        ref = self.key_storage.reference()
        if ref is None or ref.is_revoked or not self.key_storage.available():
            raise HrotOperationalError("signing key is unavailable")
        if not self.key_storage.verify_access() and (passphrase is None or not self.key_storage.unlock(passphrase)):
            raise HrotOperationalError("key storage is locked")
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        real_nonce = nonce or uuid4().hex
        signature = self.key_storage.sign(request, issued_at=now, expires_at=expires, nonce=real_nonce)
        context = HrotApprovalContext(
            approval_id=request.request_id,
            human_authority_id=request.human_authority_id,
            app_id=request.app_id,
            instance_id=request.instance_id,
            capability=request.capability,
            permission=request.permission,
            resource=request.resource,
            action=request.action,
            context_fingerprint=HrotApprovalContext.fingerprint_context(request.context),
            manifest_fingerprint=request.manifest_fingerprint,
            contract_fingerprint=request.contract_fingerprint,
            capability_version=request.capability_version,
            contract_version=request.contract_version,
            issued_at=now,
            expires_at=expires,
            nonce=real_nonce,
        )
        proof = HrotApprovalProof(context=context, key_id=ref.key_id, signature=signature)
        request.status = HrotOperationStatus.SIGNED
        self.trust_store.save_request(request)
        return proof

    def verify_proof(
        self,
        proof: HrotApprovalProof,
        *,
        expected_request: HrotApprovalRequest | None = None,
        consume: bool = False,
    ) -> tuple[HrotVerificationResult, bool]:
        trusted_key = self.key_storage.reference()
        if trusted_key is None:
            trusted_key_list = []
        else:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            import base64
            trusted_key_list = [Ed25519TrustedKey(
                key_id=trusted_key.key_id,
                public_key=_public_key_from_b64(trusted_key.public_key_b64),
                authority_id=trusted_key.authority_id,
                active=trusted_key.is_active,
                revoked=trusted_key.is_revoked or self.trust_store.is_key_revoked(trusted_key.key_id),
            )]
        verifier = self.verifier or Ed25519HumanVerifier(trusted_key_list)
        if expected_request is not None:
            expected = HrotApprovalContext(
                approval_id=expected_request.request_id,
                human_authority_id=expected_request.human_authority_id,
                app_id=expected_request.app_id,
                instance_id=expected_request.instance_id,
                capability=expected_request.capability,
                permission=expected_request.permission,
                resource=expected_request.resource,
                action=expected_request.action,
                context_fingerprint=HrotApprovalContext.fingerprint_context(expected_request.context),
                manifest_fingerprint=expected_request.manifest_fingerprint,
                contract_fingerprint=expected_request.contract_fingerprint,
                capability_version=expected_request.capability_version,
                contract_version=expected_request.contract_version,
                issued_at=proof.context.issued_at,
                expires_at=proof.context.expires_at,
                nonce=proof.context.nonce,
            )
        else:
            expected = proof.context
        result = verifier.verify(proof, expected, consumed_check=False)
        consumed_replay = self.trust_store.is_consumed(proof.proof_id)
        if result.valid and consumed_replay:
            result = HrotVerificationResult(HrotProofStatus.REPLAY_DETECTED, "proof already consumed", proof.proof_id)
        if result.valid and consume:
            verifier.consume(proof.proof_id)
            self.trust_store.consume(proof.proof_id)
        return result, (result.valid and not consumed_replay)

    def revoke_key(self, key_id: str, reason: str = "") -> None:
        self.trust_store.revoke_key(key_id, reason=reason)

    def is_key_revoked(self, key_id: str) -> bool:
        return self.trust_store.is_key_revoked(key_id)


from cryptography.hazmat.primitives import serialization


def _encrypt_private_key(private_key, passphrase: str, salt: bytes) -> bytes:
    seed = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    fernet = _fernet_from_passphrase(passphrase, salt)
    return fernet.encrypt(seed)


def _decrypt_private_key(encrypted: bytes, passphrase: str, salt: bytes) -> bytes:
    fernet = _fernet_from_passphrase(passphrase, salt)
    return fernet.decrypt(encrypted)


def _fernet_from_passphrase(passphrase: str, salt: bytes):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
    from cryptography.fernet import Fernet

    return Fernet(key)


def _public_key_b64(public_key) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def _public_key_from_b64(value: str):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    return Ed25519PublicKey.from_public_bytes(base64.b64decode(value))


# Imports at runtime to avoid heavy top-level side effects.
from core.applications.hrot_crypto import HrotVerificationResult


__all__ = [
    "HrotApprovalRequest",
    "HrotKeyStorage",
    "HrotOperationalError",
    "HrotOperationStatus",
    "HrotTrustStore",
    "OperationalHrotService",
    "SoftwareEncryptedKeyStorage",
    "TrustedKeyReference",
]

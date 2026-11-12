"""Cryptographic Human Root of Trust for ETHAN (MEM-014 Phase 10).

This module uses Ed25519 via the already-available cryptography library.
It defines a versioned proof, canonicalization, signing and independent
verification. It does not expose private keys outside the signer.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping, Sequence
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

HROT_PROTOCOL_VERSION = "1.0.0"


class HrotProofStatus(StrEnum):
    VALID = "valid"
    INVALID_SIGNATURE = "invalid_signature"
    UNKNOWN_KEY = "unknown_key"
    REVOKED_KEY = "revoked_key"
    EXPIRED_PROOF = "expired_proof"
    CONTEXT_MISMATCH = "context_mismatch"
    REPLAY_DETECTED = "replay_detected"
    REVOKED_PROOF = "revoked_proof"
    UNSUPPORTED_VERSION = "unsupported_version"
    VERIFIER_ERROR = "verifier_error"


@dataclass(frozen=True, slots=True)
class HrotApprovalContext:
    """All data covered by the human approval signature."""

    protocol_version: str = HROT_PROTOCOL_VERSION
    approval_id: str = ""
    request_id: str = ""
    human_authority_id: str = ""
    app_id: str = ""
    instance_id: str = ""
    capability: str = ""
    permission: str = ""
    resource: str = ""
    action: str = ""
    context_fingerprint: str = ""
    manifest_fingerprint: str | None = None
    contract_fingerprint: str | None = None
    capability_version: str | None = None
    contract_version: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    nonce: str = ""

    def validate(self) -> None:
        if self.protocol_version != HROT_PROTOCOL_VERSION:
            raise ValueError("unsupported protocol version")
        if not self.approval_id.strip():
            raise ValueError("approval_id is required")
        if not self.human_authority_id.strip():
            raise ValueError("human_authority_id is required")
        if not self.app_id.strip() or not self.instance_id.strip():
            raise ValueError("application identity is required")
        if not self.capability.strip() or not self.permission.strip():
            raise ValueError("capability and permission are required")
        if not self.resource.strip() or not self.action.strip():
            raise ValueError("resource and action are required")
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        if not self.nonce.strip():
            raise ValueError("nonce is required")

    def canonical_bytes(self) -> bytes:
        payload = {
            "protocol_version": self.protocol_version,
            "approval_id": self.approval_id,
            "request_id": self.request_id,
            "human_authority_id": self.human_authority_id,
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "capability": self.capability,
            "permission": self.permission,
            "resource": self.resource,
            "action": self.action,
            "context_fingerprint": self.context_fingerprint,
            "manifest_fingerprint": self.manifest_fingerprint,
            "contract_fingerprint": self.contract_fingerprint,
            "capability_version": self.capability_version,
            "contract_version": self.contract_version,
            "issued_at": self.issued_at.astimezone(timezone.utc).isoformat(),
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
            "nonce": self.nonce,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return canonical.encode("utf-8")

    @classmethod
    def fingerprint_context(cls, context: Mapping[str, Any]) -> str:
        canonical = json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        import hashlib
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class HrotApprovalProof:
    """Cryptographically signed human approval proof."""

    context: HrotApprovalContext
    key_id: str
    signature: bytes
    proof_id: str = ""

    def __post_init__(self) -> None:
        if not self.proof_id:
            object.__setattr__(self, "proof_id", self.context.approval_id)
        if not self.key_id.strip():
            raise ValueError("key_id is required")
        if not self.signature:
            raise ValueError("signature is required")
        self.context.validate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.context.protocol_version,
            "approval_id": self.context.approval_id,
            "request_id": self.context.request_id,
            "human_authority_id": self.context.human_authority_id,
            "app_id": self.context.app_id,
            "instance_id": self.context.instance_id,
            "capability": self.context.capability,
            "permission": self.context.permission,
            "resource": self.context.resource,
            "action": self.context.action,
            "context_fingerprint": self.context.context_fingerprint,
            "manifest_fingerprint": self.context.manifest_fingerprint,
            "contract_fingerprint": self.context.contract_fingerprint,
            "capability_version": self.context.capability_version,
            "contract_version": self.context.contract_version,
            "issued_at": self.context.issued_at.isoformat(),
            "expires_at": self.context.expires_at.isoformat(),
            "nonce": self.context.nonce,
            "key_id": self.key_id,
            "signature": base64.b64encode(self.signature).decode("ascii"),
            "proof_id": self.proof_id,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "HrotApprovalProof":
        ctx = HrotApprovalContext(
            protocol_version=str(data.get("protocol_version", HROT_PROTOCOL_VERSION)),
            approval_id=str(data.get("approval_id", "")),
            request_id=str(data.get("request_id", "")),
            human_authority_id=str(data.get("human_authority_id", "")),
            app_id=str(data.get("app_id", "")),
            instance_id=str(data.get("instance_id", "")),
            capability=str(data.get("capability", "")),
            permission=str(data.get("permission", "")),
            resource=str(data.get("resource", "")),
            action=str(data.get("action", "")),
            context_fingerprint=str(data.get("context_fingerprint", "")),
            manifest_fingerprint=data.get("manifest_fingerprint"),
            contract_fingerprint=data.get("contract_fingerprint"),
            capability_version=data.get("capability_version"),
            contract_version=data.get("contract_version"),
            issued_at=datetime.fromisoformat(str(data.get("issued_at")).replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(str(data.get("expires_at")).replace("Z", "+00:00")),
            nonce=str(data.get("nonce", "")),
        )
        signature = base64.b64decode(str(data.get("signature", "")))
        return cls(context=ctx, key_id=str(data.get("key_id", "")), signature=signature, proof_id=str(data.get("proof_id", "")) or str(data.get("approval_id", "")))


@dataclass(slots=True)
class HrotVerificationResult:
    status: HrotProofStatus
    message: str
    proof_id: str | None = None

    @property
    def valid(self) -> bool:
        return self.status == HrotProofStatus.VALID


class HrotVerificationError(ValueError):
    pass


@dataclass(slots=True)
class Ed25519TrustedKey:
    key_id: str
    public_key: Ed25519PublicKey
    authority_id: str
    active: bool = True
    revoked: bool = False


class Ed25519HumanSigner:
    """Signer wrapper; private key stays in this object only."""

    def __init__(self, private_key: Ed25519PrivateKey, key_id: str, authority_id: str) -> None:
        self._private_key = private_key
        self.key_id = key_id
        self.authority_id = authority_id

    def public_key(self) -> Ed25519PublicKey:
        return self._private_key.public_key()

    def sign(self, context: HrotApprovalContext) -> HrotApprovalProof:
        context.validate()
        message = context.canonical_bytes()
        signature = self._private_key.sign(message)
        return HrotApprovalProof(context=context, key_id=self.key_id, signature=signature)


class Ed25519HumanVerifier:
    """Independent verifier holding only trusted public keys."""

    def __init__(self, trusted_keys: Sequence[Ed25519TrustedKey] | None = None) -> None:
        self._keys: dict[str, Ed25519TrustedKey] = {}
        for key in trusted_keys or []:
            self.register_key(key)
        self._consumed: set[str] = set()

    def register_key(self, key: Ed25519TrustedKey) -> None:
        self._keys[key.key_id] = key

    def revoke_key(self, key_id: str) -> None:
        if key_id in self._keys:
            self._keys[key_id].revoked = True

    def is_consumed(self, proof_id: str) -> bool:
        return proof_id in self._consumed

    def consume(self, proof_id: str) -> None:
        self._consumed.add(proof_id)

    def verify(
        self,
        proof: HrotApprovalProof | Mapping[str, Any],
        expected_context: HrotApprovalContext | Mapping[str, Any],
        *,
        expected_manifest_fingerprint: str | None = None,
        expected_contract_fingerprint: str | None = None,
        consumed_check: bool = True,
    ) -> HrotVerificationResult:
        try:
            proof_obj = proof if isinstance(proof, HrotApprovalProof) else HrotApprovalProof.from_mapping(proof)
            if isinstance(expected_context, Mapping):
                expected = HrotApprovalContext(**{
                    k: v for k, v in expected_context.items() if k in HrotApprovalContext.__dataclass_fields__
                })
            else:
                expected = expected_context

            # Field-by-field context binding first.
            if proof_obj.context.protocol_version != HROT_PROTOCOL_VERSION:
                return HrotVerificationResult(HrotProofStatus.UNSUPPORTED_VERSION, "unsupported protocol version", proof_obj.proof_id)
            if proof_obj.context.app_id != expected.app_id or proof_obj.context.instance_id != expected.instance_id:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "application identity mismatch", proof_obj.proof_id)
            if proof_obj.context.capability != expected.capability or proof_obj.context.permission != expected.permission:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "capability or permission mismatch", proof_obj.proof_id)
            if proof_obj.context.resource != expected.resource or proof_obj.context.action != expected.action:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "resource or action mismatch", proof_obj.proof_id)
            if proof_obj.context.context_fingerprint != expected.context_fingerprint:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "authorization context mismatch", proof_obj.proof_id)
            if proof_obj.context.manifest_fingerprint != expected_manifest_fingerprint and expected_manifest_fingerprint is not None:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "manifest fingerprint mismatch", proof_obj.proof_id)
            if proof_obj.context.contract_fingerprint != expected_contract_fingerprint and expected_contract_fingerprint is not None:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "contract fingerprint mismatch", proof_obj.proof_id)
            if proof_obj.context.capability_version != expected.capability_version and expected.capability_version is not None:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "capability version mismatch", proof_obj.proof_id)
            if proof_obj.context.contract_version != expected.contract_version and expected.contract_version is not None:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "contract version mismatch", proof_obj.proof_id)
            now = datetime.now(timezone.utc)
            if now >= proof_obj.context.expires_at:
                return HrotVerificationResult(HrotProofStatus.EXPIRED_PROOF, "proof has expired", proof_obj.proof_id)
            if now < proof_obj.context.issued_at:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "proof issued in the future", proof_obj.proof_id)

            trusted_key = self._keys.get(proof_obj.key_id)
            if trusted_key is None:
                return HrotVerificationResult(HrotProofStatus.UNKNOWN_KEY, "unknown trusted key", proof_obj.proof_id)
            if trusted_key.revoked:
                return HrotVerificationResult(HrotProofStatus.REVOKED_KEY, "trusted key is revoked", proof_obj.proof_id)
            if not trusted_key.active:
                return HrotVerificationResult(HrotProofStatus.VERIFIER_ERROR, "trusted key is inactive", proof_obj.proof_id)
            if trusted_key.authority_id != proof_obj.context.human_authority_id:
                return HrotVerificationResult(HrotProofStatus.CONTEXT_MISMATCH, "authority identity mismatch", proof_obj.proof_id)

            if consumed_check and proof_obj.proof_id in self._consumed:
                return HrotVerificationResult(HrotProofStatus.REPLAY_DETECTED, "proof already consumed", proof_obj.proof_id)

            try:
                trusted_key.public_key.verify(proof_obj.signature, proof_obj.context.canonical_bytes())
            except InvalidSignature:
                return HrotVerificationResult(HrotProofStatus.INVALID_SIGNATURE, "invalid signature", proof_obj.proof_id)

            if consumed_check:
                self._consumed.add(proof_obj.proof_id)
            return HrotVerificationResult(HrotProofStatus.VALID, "proof is valid", proof_obj.proof_id)
        except Exception as exc:
            return HrotVerificationResult(HrotProofStatus.VERIFIER_ERROR, str(exc), getattr(proof, "proof_id", None))


# Aliases
HrotVerifier = Ed25519HumanVerifier
HumanTrustVerifier = Ed25519HumanVerifier
CryptographicHumanTrustVerifier = Ed25519HumanVerifier


__all__ = [
    "HROT_PROTOCOL_VERSION",
    "HrotApprovalContext",
    "HrotApprovalProof",
    "HrotProofStatus",
    "HrotVerificationResult",
    "Ed25519HumanSigner",
    "Ed25519HumanVerifier",
    "Ed25519TrustedKey",
    "HrotVerifier",
    "HumanTrustVerifier",
]

"""Central compliance engine for ETHAN applications (MEM-014 Phase 5)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from core.applications.contracts import ExtensionContract
from core.applications.models import (
    ApplicationManifest,
    ValidationError,
    ValidationStatus,
)
from core.applications.permissions import manifest_fingerprint
from core.applications.validator import ContractValidator


RULE_CATALOG_VERSION = "1.0.0"


class ComplianceResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComplianceStatus(StrEnum):
    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_EVALUATED = "NOT_EVALUATED"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ComplianceCheck:
    check_id: str
    category: str
    result: ComplianceResult
    severity: Severity
    description: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_version: str = RULE_CATALOG_VERSION
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "result": self.result.value,
            "severity": self.severity.value,
            "description": self.description,
            "message": self.message,
            "evidence_refs": list(self.evidence_refs),
            "rule_version": self.rule_version,
        }


@dataclass(slots=True)
class ComplianceReport:
    evaluation_id: str
    evaluated_at: datetime
    target_id: str | None
    manifest_digest: str | None
    contract_digest: str | None
    status: ComplianceStatus
    checks: tuple[ComplianceCheck, ...]
    error: str | None = None

    @property
    def passed_count(self) -> int:
        return sum(check.result == ComplianceResult.PASS for check in self.checks)

    @property
    def failed_count(self) -> int:
        return sum(check.result == ComplianceResult.FAIL for check in self.checks)

    @property
    def warning_count(self) -> int:
        return sum(check.result == ComplianceResult.WARN for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "target_id": self.target_id,
            "manifest_digest": self.manifest_digest,
            "contract_digest": self.contract_digest,
            "status": self.status.value,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "warning_count": self.warning_count,
            "error": self.error,
            "checks": [check.to_dict() for check in self.checks],
        }

    @property
    def compliant(self) -> bool:
        return self.status == ComplianceStatus.COMPLIANT


@dataclass(frozen=True, slots=True)
class ComplianceRule:
    check: Callable[["ComplianceContext"], ComplianceCheck] = field(compare=False)
    rule_id: str = ""
    category: str = ""
    description: str = ""
    severity: Severity = Severity.MEDIUM
    required: bool = False
    rule_version: str = RULE_CATALOG_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "required": self.required,
            "rule_version": self.rule_version,
        }


@dataclass(slots=True)
class ComplianceContext:
    manifest: ApplicationManifest | None
    manifest_raw: Mapping[str, Any] | None
    contract: ExtensionContract | None
    contract_raw: Mapping[str, Any] | None
    evidence: Mapping[str, Any]
    engine: "ComplianceEngine"


class ComplianceEngine:
    """Reproducible compliance evaluator with deterministic rules."""

    def __init__(self, store: Any | None = None, capability_registry: Any | None = None) -> None:
        self._store = store
        self._capability_registry = capability_registry
        self._rules: list[ComplianceRule] = self._build_rules()
        self._evaluations: dict[str, ComplianceReport] = {}
        if store is not None:
            try:
                for payload in store.load_records("compliance_reports"):
                    pass
            except Exception:
                pass

    @property
    def rules(self) -> tuple[ComplianceRule, ...]:
        return tuple(self._rules)

    def evaluate(
        self,
        manifest: ApplicationManifest | Mapping[str, Any] | None = None,
        contract: ExtensionContract | Mapping[str, Any] | None = None,
        evidence: Mapping[str, Any] | None = None,
        *,
        target_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> ComplianceReport:
        evidence_mapping = dict(evidence or {})
        context_mapping = dict(context or {})

        manifest_raw: Mapping[str, Any] | None = None
        manifest_obj: ApplicationManifest | None = None
        manifest_error: str | None = None
        if isinstance(manifest, ApplicationManifest):
            manifest_obj = manifest
            manifest_raw = manifest.to_dict()
        elif isinstance(manifest, Mapping):
            manifest_raw = manifest
            try:
                manifest_obj = ApplicationManifest.from_mapping(manifest)
            except ValidationError as exc:
                manifest_error = str(exc)
        elif manifest is None:
            manifest_obj = None
        else:
            manifest_error = "manifest must be a mapping or ApplicationManifest"

        contract_raw: Mapping[str, Any] | None = None
        contract_obj: ExtensionContract | None = None
        contract_error: str | None = None
        if isinstance(contract, ExtensionContract):
            contract_obj = contract
            contract_raw = contract.to_dict()
        elif isinstance(contract, Mapping):
            contract_raw = contract
            try:
                contract_obj = ExtensionContract.from_mapping(contract)
            except ValidationError as exc:
                contract_error = str(exc)
        elif contract is None:
            contract_obj = None
        else:
            contract_error = "contract must be a mapping or ExtensionContract"

        # If the supplied manifest is itself a validation result carrier, prefer
        # its parsed identity when available.
        if target_id is None:
            if manifest_obj is not None:
                target_id = manifest_obj.identity.app_id
            elif contract_obj is not None:
                target_id = contract_obj.identity.app_id if contract_obj.identity is not None else None

        try:
            eval_context = ComplianceContext(
                manifest=manifest_obj,
                manifest_raw=manifest_raw,
                contract=contract_obj,
                contract_raw=contract_raw,
                evidence=evidence_mapping,
                engine=self,
            )
            checks = tuple(rule.check(eval_context) for rule in self._rules)
            # Attach manifest/contract validation errors as failed evidence when needed.
            if manifest_error is not None:
                checks = (
                    ComplianceCheck(
                        check_id="COMPLIANCE_MANIFEST_VALID",
                        category="manifest",
                        result=ComplianceResult.FAIL,
                        severity=Severity.CRITICAL,
                        description="The application manifest must be structurally valid.",
                        message=manifest_error,
                        evidence_refs=("manifest",),
                    ),
                ) + checks[1:]
            if contract is not None and contract_error is not None:
                checks = _replace_check(
                    checks,
                    "COMPLIANCE_CONTRACT_VALID",
                    ComplianceCheck(
                        check_id="COMPLIANCE_CONTRACT_VALID",
                        category="contract",
                        result=ComplianceResult.FAIL,
                        severity=Severity.CRITICAL,
                        description="The extension contract must be structurally valid.",
                        message=contract_error,
                        evidence_refs=("contract",),
                    ),
                )

            status = self._overall_status(checks, manifest_error, contract_error)
            manifest_digest = None
            if manifest_obj is not None:
                manifest_digest = manifest_fingerprint(manifest_obj)
            elif isinstance(manifest_raw, Mapping):
                manifest_digest = _digest_mapping(manifest_raw)
            contract_digest = None
            if contract_obj is not None:
                contract_digest = _digest_mapping(contract_obj.to_dict())
            elif isinstance(contract_raw, Mapping):
                contract_digest = _digest_mapping(contract_raw)

            report = ComplianceReport(
                evaluation_id=str(uuid4()),
                evaluated_at=datetime.now(timezone.utc),
                target_id=target_id,
                manifest_digest=manifest_digest,
                contract_digest=contract_digest,
                status=status,
                checks=checks,
                error=None,
            )
        except Exception as exc:  # noqa: BLE001 - evaluation errors are never compliant.
            report = ComplianceReport(
                evaluation_id=str(uuid4()),
                evaluated_at=datetime.now(timezone.utc),
                target_id=target_id,
                manifest_digest=None,
                contract_digest=None,
                status=ComplianceStatus.NON_COMPLIANT,
                checks=(
                    ComplianceCheck(
                        check_id="COMPLIANCE_ENGINE_ERROR",
                        category="engine",
                        result=ComplianceResult.FAIL,
                        severity=Severity.CRITICAL,
                        description="The compliance engine must not produce a compliant result after an internal error.",
                        message=str(exc),
                        evidence_refs=("engine",),
                    ),
                ),
                error=str(exc),
            )

        self._evaluations[report.evaluation_id] = report
        if self._store is not None:
            try:
                self._store.save_record("compliance_reports", report.evaluation_id, report.to_dict())
            except Exception:
                pass
        return report

    def invalidate(self, evaluation_id: str | None = None, manifest_digest: str | None = None) -> None:
        if evaluation_id is not None:
            self._evaluations.pop(evaluation_id, None)
        if manifest_digest is not None:
            stale = [key for key, report in self._evaluations.items() if report.manifest_digest == manifest_digest]
            for key in stale:
                self._evaluations.pop(key, None)

    def get_evaluation(self, evaluation_id: str) -> ComplianceReport | None:
        return self._evaluations.get(evaluation_id)

    def list_rules(self) -> tuple[ComplianceRule, ...]:
        return self.rules

    def rule_catalog(self) -> list[dict[str, Any]]:
        return [rule.to_dict() for rule in self._rules]

    def _overall_status(
        self,
        checks: Sequence[ComplianceCheck],
        manifest_error: str | None,
        contract_error: str | None,
    ) -> ComplianceStatus:
        if manifest_error is not None or contract_error is not None:
            return ComplianceStatus.NON_COMPLIANT
        required_checks = {rule.rule_id for rule in self._rules if rule.required}
        check_by_id = {check.check_id: check for check in checks}
        for rule_id in required_checks:
            check = check_by_id.get(rule_id)
            if check is None or check.result != ComplianceResult.PASS:
                return ComplianceStatus.NON_COMPLIANT
        if any(check.result == ComplianceResult.FAIL for check in checks):
            return ComplianceStatus.PARTIALLY_COMPLIANT
        if any(check.result == ComplianceResult.WARN for check in checks):
            return ComplianceStatus.PARTIALLY_COMPLIANT
        return ComplianceStatus.COMPLIANT

    def _build_rules(self) -> list[ComplianceRule]:
        return [
            ComplianceRule(
                rule_id="COMPLIANCE_MANIFEST_VALID",
                category="manifest",
                description="The application manifest must be structurally valid.",
                severity=Severity.CRITICAL,
                required=True,
                check=_check_manifest_valid,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_CONTRACT_VALID",
                category="contract",
                description="The extension contract must be valid when supplied.",
                severity=Severity.CRITICAL,
                required=False,
                check=_check_contract_valid,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_IDENTITY_COMPLETE",
                category="identity",
                description="Application identity fields must be complete and valid.",
                severity=Severity.HIGH,
                required=True,
                check=_check_identity_complete,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_VERSION_COMPATIBLE",
                category="version",
                description="Application and contract versions must be compatible with ETHAN.",
                severity=Severity.HIGH,
                required=True,
                check=_check_version_compatible,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_CAPABILITY_PERMISSION_COHERENCE",
                category="permissions",
                description="Requested permissions must be compatible with declared capabilities.",
                severity=Severity.HIGH,
                required=True,
                check=_check_capability_permission_coherence,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_SECURITY_NO_SECRETS",
                category="security",
                description="Manifests and contracts must not contain obvious secret material.",
                severity=Severity.CRITICAL,
                required=True,
                check=_check_no_secrets,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_PROVENANCE_PRESENT",
                category="provenance",
                description="The manifest must contain a provenance source and digest.",
                severity=Severity.MEDIUM,
                required=False,
                check=_check_provenance_present,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_EVIDENCE_PRESENT",
                category="evidence",
                description="The evaluation must reference at least one piece of evidence.",
                severity=Severity.MEDIUM,
                required=True,
                check=_check_evidence_present,
            ),
            ComplianceRule(
                rule_id="COMPLIANCE_CAPABILITY_REGISTRY",
                category="capabilities",
                description="Declared capabilities present in a registry must be known.",
                severity=Severity.HIGH,
                required=False,
                check=_check_capability_registry,
            ),
        ]


def _check_manifest_valid(context: ComplianceContext) -> ComplianceCheck:
    valid = context.manifest is not None
    return ComplianceCheck(
        check_id="COMPLIANCE_MANIFEST_VALID",
        category="manifest",
        result=ComplianceResult.PASS if valid else ComplianceResult.FAIL,
        severity=Severity.CRITICAL,
        description="The application manifest must be structurally valid.",
        message="" if valid else "manifest is missing or invalid",
        evidence_refs=("manifest",),
    )


def _check_contract_valid(context: ComplianceContext) -> ComplianceCheck:
    if context.contract is None and context.contract_raw is None:
        return ComplianceCheck(
            check_id="COMPLIANCE_CONTRACT_VALID",
            category="contract",
            result=ComplianceResult.NOT_APPLICABLE,
            severity=Severity.MEDIUM,
            description="The extension contract must be valid when supplied.",
            message="no contract supplied",
            evidence_refs=("contract",),
        )
    valid = context.contract is not None
    return ComplianceCheck(
        check_id="COMPLIANCE_CONTRACT_VALID",
        category="contract",
        result=ComplianceResult.PASS if valid else ComplianceResult.FAIL,
        severity=Severity.CRITICAL,
        description="The extension contract must be valid when supplied.",
        message="" if valid else "contract is missing or invalid",
        evidence_refs=("contract",),
    )


def _check_identity_complete(context: ComplianceContext) -> ComplianceCheck:
    manifest = context.manifest
    valid = bool(
        manifest is not None
        and manifest.identity.app_id.strip()
        and manifest.identity.instance_id.strip()
        and manifest.identity.name.strip()
        and manifest.identity.publisher.strip()
        and manifest.identity.manifest_version >= 1
    )
    return ComplianceCheck(
        check_id="COMPLIANCE_IDENTITY_COMPLETE",
        category="identity",
        result=ComplianceResult.PASS if valid else ComplianceResult.FAIL,
        severity=Severity.HIGH,
        description="Application identity fields must be complete and valid.",
        message="" if valid else "application identity is incomplete",
        evidence_refs=("identity",),
    )


def _check_version_compatible(context: ComplianceContext) -> ComplianceCheck:
    manifest = context.manifest
    if manifest is None:
        return ComplianceCheck(
            check_id="COMPLIANCE_VERSION_COMPATIBLE",
            category="version",
            result=ComplianceResult.FAIL,
            severity=Severity.HIGH,
            description="Application and contract versions must be compatible with ETHAN.",
            message="manifest is missing",
            evidence_refs=("version",),
        )
    valid = manifest.identity.contract_version == "1.0.0"
    return ComplianceCheck(
        check_id="COMPLIANCE_VERSION_COMPATIBLE",
        category="version",
        result=ComplianceResult.PASS if valid else ComplianceResult.FAIL,
        severity=Severity.HIGH,
        description="Application and contract versions must be compatible with ETHAN.",
        message="" if valid else "contract version is not compatible with ETHAN",
        evidence_refs=("version", "contract_version"),
    )


def _check_capability_permission_coherence(context: ComplianceContext) -> ComplianceCheck:
    manifest = context.manifest
    contract = context.contract
    if manifest is None:
        return ComplianceCheck(
            check_id="COMPLIANCE_CAPABILITY_PERMISSION_COHERENCE",
            category="permissions",
            result=ComplianceResult.FAIL,
            severity=Severity.HIGH,
            description="Requested permissions must be compatible with declared capabilities.",
            message="manifest is missing",
            evidence_refs=("capabilities", "permissions"),
        )
    declared = {capability.name for capability in manifest.capabilities}
    requested = contract.requested_permissions if contract is not None else manifest.permissions
    compatible = True
    message = ""
    for permission in requested:
        if permission in declared:
            continue
        if declared and any(permission.startswith(cap + ":") or permission.startswith(cap + ".") or permission.startswith(cap + "/") for cap in declared):
            continue
        if not declared and requested:
            compatible = False
            message = "permissions require at least one declared capability"
            break
        if declared:
            compatible = False
            message = f"permission {permission!r} is not compatible with declared capabilities"
            break
    return ComplianceCheck(
        check_id="COMPLIANCE_CAPABILITY_PERMISSION_COHERENCE",
        category="permissions",
        result=ComplianceResult.PASS if compatible else ComplianceResult.FAIL,
        severity=Severity.HIGH,
        description="Requested permissions must be compatible with declared capabilities.",
        message=message,
        evidence_refs=("capabilities", "requested_permissions"),
    )


def _check_no_secrets(context: ComplianceContext) -> ComplianceCheck:
    from core.applications.validator import _contains_secret_material

    forbidden = False
    if context.manifest_raw is not None and _contains_secret_material(context.manifest_raw):
        forbidden = True
    if context.contract_raw is not None and _contains_secret_material(context.contract_raw):
        forbidden = True
    return ComplianceCheck(
        check_id="COMPLIANCE_SECURITY_NO_SECRETS",
        category="security",
        result=ComplianceResult.FAIL if forbidden else ComplianceResult.PASS,
        severity=Severity.CRITICAL,
        description="Manifests and contracts must not contain obvious secret material.",
        message="secret material detected" if forbidden else "",
        evidence_refs=("manifest", "contract"),
    )


def _check_provenance_present(context: ComplianceContext) -> ComplianceCheck:
    manifest = context.manifest
    present = bool(
        manifest is not None
        and manifest.provenance.source.strip()
        and manifest.provenance.digest
    )
    return ComplianceCheck(
        check_id="COMPLIANCE_PROVENANCE_PRESENT",
        category="provenance",
        result=ComplianceResult.PASS if present else ComplianceResult.WARN,
        severity=Severity.MEDIUM,
        description="The manifest must contain a provenance source and digest.",
        message="" if present else "provenance source or digest is missing",
        evidence_refs=("provenance",),
    )


def _check_evidence_present(context: ComplianceContext) -> ComplianceCheck:
    present = bool(context.evidence) or bool(
        context.manifest is not None and context.manifest.provenance.digest
    )
    return ComplianceCheck(
        check_id="COMPLIANCE_EVIDENCE_PRESENT",
        category="evidence",
        result=ComplianceResult.PASS if present else ComplianceResult.FAIL,
        severity=Severity.MEDIUM,
        description="The evaluation must reference at least one piece of evidence.",
        message="" if present else "required evidence is missing",
        evidence_refs=("evidence",),
    )



def _check_capability_registry(context: ComplianceContext) -> ComplianceCheck:
    registry = context.engine._capability_registry
    if registry is None:
        return ComplianceCheck(
            check_id="COMPLIANCE_CAPABILITY_REGISTRY",
            category="capabilities",
            result=ComplianceResult.NOT_APPLICABLE,
            severity=Severity.HIGH,
            description="Declared capabilities present in a registry must be known.",
            message="no capability registry supplied",
            evidence_refs=("capabilities",),
        )
    manifest = context.manifest
    if manifest is None:
        return ComplianceCheck(
            check_id="COMPLIANCE_CAPABILITY_REGISTRY",
            category="capabilities",
            result=ComplianceResult.FAIL,
            severity=Severity.HIGH,
            description="Declared capabilities present in a registry must be known.",
            message="manifest is missing",
            evidence_refs=("capabilities",),
        )
    unknown: list[str] = []
    for capability in manifest.capabilities:
        if hasattr(registry, "exists") and not registry.exists(capability.name):
            unknown.append(capability.name)
    return ComplianceCheck(
        check_id="COMPLIANCE_CAPABILITY_REGISTRY",
        category="capabilities",
        result=ComplianceResult.FAIL if unknown else ComplianceResult.PASS,
        severity=Severity.HIGH,
        description="Declared capabilities present in a registry must be known.",
        message="" if not unknown else "unknown capabilities: " + ", ".join(sorted(unknown)),
        evidence_refs=("capabilities", "registry"),
    )



def _replace_check(
    checks: Sequence[ComplianceCheck], check_id: str, replacement: ComplianceCheck
) -> tuple[ComplianceCheck, ...]:
    return tuple(replacement if check.check_id == check_id else check for check in checks)


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Aliases for naming flexibility.
ComplianceManager = ComplianceEngine
ComplianceValidator = ComplianceEngine
ApplicationComplianceEngine = ComplianceEngine
ComplianceService = ComplianceEngine


__all__ = [
    "ComplianceCheck",
    "ComplianceContext",
    "ComplianceEngine",
    "ComplianceManager",
    "ComplianceReport",
    "ComplianceResult",
    "ComplianceService",
    "ComplianceStatus",
    "ComplianceValidator",
    "RULE_CATALOG_VERSION",
    "Severity",
]

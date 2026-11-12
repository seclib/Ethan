"""Centralized contract validator for ETHAN application manifests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Union

import yaml

from core.applications.models import (
    CONTRACT_VERSION,
    ETHAN_CONTRACT_VERSION,
    SUPPORTED_CONTRACT_VERSIONS,
    ApplicationManifest,
    ValidationError,
    ValidationResult,
    ValidationStatus,
)

_REQUIRED_ROOT_FIELDS = ("identity",)
_ROOT_FIELDS = ApplicationManifest._ALLOWED_ROOT_FIELDS

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk|pk)_(?:live|test|prod)_[0-9A-Za-z]{10,}\b", re.IGNORECASE),
    re.compile(r"\bgh[ps]_[0-9A-Za-z]{20,}\b"),
    re.compile(r"\bxox[abp]-[0-9A-Za-z-]{10,}\b"),
    re.compile(
        r"""(?ix)
        \b(?:password|passwd|api[_-]?key|secret(?:_?key)?|token|private[_-]?key)\s*[:=]\s*\S+
        """
    ),
)


class ContractValidator:
    """Validate manifest payloads and files against the ETHAN contract."""

    def __init__(
        self,
        supported_contract_versions: frozenset[str] | set[str] | None = None,
    ) -> None:
        self.supported_contract_versions = frozenset(
            supported_contract_versions
            if supported_contract_versions is not None
            else SUPPORTED_CONTRACT_VERSIONS
        )

    def validate_manifest_data(self, data: Any) -> ValidationResult:
        """Validate an in-memory manifest mapping."""
        errors: list[str] = []
        warnings: list[str] = []
        identity = None

        if not isinstance(data, Mapping):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID.value,
                errors=("manifest must be an object",),
                warnings=(),
                identity=None,
            )

        if not data:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INCOMPLETE.value,
                errors=("manifest is empty",),
                warnings=(),
                identity=None,
            )

        if "identity" not in data:
            errors.append("manifest is missing required field: identity")
            warnings.append("identity absent")

        # Optional structural completeness signals. These do not invalidate a
        # minimal manifest but make partial declarations explicit to agents.
        for optional_field in ("capabilities", "dependencies", "provenance"):
            if optional_field not in data:
                warnings.append(f"optional manifest section absent: {optional_field}")

        try:
            manifest = ApplicationManifest.from_mapping(data)
            identity = manifest.identity
            if identity.contract_version not in self.supported_contract_versions:
                errors.append(
                    "contract_version is not compatible with ETHAN: "
                    f"{identity.contract_version!r}; supported: "
                    + ", ".join(sorted(self.supported_contract_versions))
                )
            if not identity.is_contract_compatible(self.supported_contract_versions):
                # Already covered above, kept for an explicit incompatible status.
                pass
            if _contains_secret_material(data):
                errors.append("manifest contains forbidden secret material")
        except ValidationError as error:
            errors.append(str(error))
            message = str(error)
            if "missing required field: identity" in message or "is missing required field: identity" in message:
                if identity is None:
                    pass

        # Status classification. Structural absence is incomplete, contract
        # mismatch is incompatible, everything else is invalid.
        status = self._status_from_errors(errors, data, identity)
        return ValidationResult(
            is_valid=len(errors) == 0,
            status=status,
            errors=tuple(errors),
            warnings=tuple(warnings),
            identity=identity,
        )

    def validate_manifest_file(self, path: Union[str, Path]) -> ValidationResult:
        """Validate a YAML manifest file."""
        target = Path(path)
        try:
            if not target.is_file():
                return ValidationResult(
                    False,
                    ValidationStatus.INVALID.value,
                    (f"cannot read file: not a regular file: {target}",),
                    (),
                )
            if target.stat().st_size > 1_048_576:
                return ValidationResult(
                    False,
                    ValidationStatus.INVALID.value,
                    (f"manifest file is too large: {target}",),
                    (),
                )
            payload = target.read_text(encoding="utf-8")
        except OSError as error:
            return ValidationResult(
                False,
                ValidationStatus.INVALID.value,
                (f"cannot read file: {error}",),
                (),
            )

        try:
            data = yaml.safe_load(payload)
        except yaml.YAMLError as error:
            return ValidationResult(
                False,
                ValidationStatus.INVALID.value,
                (str(error),),
                (),
            )

        if payload.strip() and data is None:
            return ValidationResult(
                False,
                ValidationStatus.INVALID.value,
                ("manifest is empty",),
                (),
            )
        if not isinstance(data, Mapping):
            return ValidationResult(
                False,
                ValidationStatus.INVALID.value,
                ("manifest root must be an object",),
                (),
            )
        return self.validate_manifest_data(data)

    # Aliases for callers that expect simpler names.
    def validate(self, data_or_path: Any) -> ValidationResult:
        if isinstance(data_or_path, Path):
            return self.validate_manifest_file(data_or_path)
        if isinstance(data_or_path, str):
            if len(data_or_path) <= 1024 and "\n" not in data_or_path and " " not in data_or_path:
                candidate = Path(data_or_path)
                try:
                    if candidate.is_file():
                        return self.validate_manifest_file(candidate)
                except OSError:
                    pass
            return self.validate_yaml(data_or_path)
        return self.validate_manifest_data(data_or_path)

    def validate_manifest(self, data_or_path: Any) -> ValidationResult:
        return self.validate(data_or_path)

    def validate_yaml(self, payload: str) -> ValidationResult:
        try:
            data = yaml.safe_load(payload)
        except yaml.YAMLError as error:
            return ValidationResult(False, ValidationStatus.INVALID.value, (str(error),), ())
        if not isinstance(data, Mapping):
            return ValidationResult(False, ValidationStatus.INVALID.value, ("manifest root must be an object",), ())
        return self.validate_manifest_data(data)

    def validate_file(self, path: Any) -> ValidationResult:
        return self.validate_manifest_file(path)

    def validate_path(self, path: Any) -> ValidationResult:
        return self.validate_manifest_file(path)

    def validate_data(self, data: Any) -> ValidationResult:
        return self.validate_manifest_data(data)

    def validate_text(self, payload: str) -> ValidationResult:
        return self.validate_yaml(payload)

    def validate_content(self, payload: str) -> ValidationResult:
        return self.validate_yaml(payload)

    def validate_dict(self, data: Any) -> ValidationResult:
        return self.validate_manifest_data(data)

    @staticmethod
    def _status_from_errors(
        errors: list[str], data: Mapping[str, Any], identity: Any
    ) -> str:
        if len(errors) == 0:
            return ValidationStatus.VALID.value
        joined = " ".join(errors)
        # Missing required fields or identity point to an incomplete manifest.
        if (
            "missing required field" in joined
            or "missing identity" in joined
            or "identity absent" in joined
            or "manifest is empty" in joined
            or "manifest root must be" in joined
            and False
        ):
            return ValidationStatus.INCOMPLETE.value
        if "identity" not in data:
            return ValidationStatus.INCOMPLETE.value
        if "contract_version is not compatible" in joined:
            return ValidationStatus.INCOMPATIBLE.value
        # contract_version syntax errors from identity are invalid, not incomplete.
        if "contract_version" in joined and "compatible" not in joined:
            # Keep explicit incompatible marker handling for version mismatch.
            if "INCOMPATIBLE" in joined.upper():
                return ValidationStatus.INCOMPATIBLE.value
            return ValidationStatus.INVALID.value
        if "is not compatible" in joined or "incompatible" in joined:
            return ValidationStatus.INCOMPATIBLE.value
        # Top-level authorized/structural errors.
        return ValidationStatus.INVALID.value




def _contains_secret_material(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in _SECRET_PATTERNS)
    if isinstance(value, Mapping):
        return any(_contains_secret_material(item) for item in value.values()) or any(
            _contains_secret_material(key) for key in value.keys()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_contains_secret_material(item) for item in value)
    return False

"""API validator — validate API responses against schemas."""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class APISchema:
    """Schema definition for API response."""
    endpoint: str
    method: str
    expected_keys: list[str]
    expected_types: dict[str, type]
    required: bool = True


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: list[str]


class APIResponseValidator:
    """Validate API responses against schemas."""

    SCHEMAS = {
        "message": APISchema(
            endpoint="/v1/message",
            method="POST",
            expected_keys=["success", "event_id", "goal_id", "message"],
            expected_types={
                "success": bool,
                "event_id": str,
                "goal_id": str,
                "message": str,
            },
        ),
        "state": APISchema(
            endpoint="/v1/state",
            method="GET",
            expected_keys=["mode", "modules_active"],
            expected_types={
                "mode": str,
                "modules_active": list,
            },
        ),
        "health": APISchema(
            endpoint="/v1/health",
            method="GET",
            expected_keys=["status", "service", "nats_connected"],
            expected_types={
                "status": str,
                "service": str,
                "nats_connected": bool,
            },
        ),
    }

    def validate(self, endpoint: str, response: dict) -> ValidationResult:
        """Validate response against schema.

        Args:
            endpoint: API endpoint (e.g., "/v1/message") or schema name
            response: Parsed JSON response

        Returns:
            ValidationResult
        """
        schema = self.SCHEMAS.get(endpoint)
        if schema is None:
            # Try matching by endpoint path
            for s in self.SCHEMAS.values():
                if s.endpoint == endpoint:
                    schema = s
                    break
        if schema is None:
            return ValidationResult(
                valid=False,
                errors=[f"No schema defined for {endpoint}"],
            )

        errors = []

        # Check required keys
        missing = [k for k in schema.expected_keys if k not in response]
        if missing:
            errors.append(f"Missing keys: {missing}")

        # Check types
        for key, expected_type in schema.expected_types.items():
            if key in response and not isinstance(response[key], expected_type):
                actual_type = type(response[key]).__name__
                errors.append(
                    f"Key '{key}': expected {expected_type.__name__}, got {actual_type}"
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )

    def register_schema(self, name: str, schema: APISchema) -> None:
        """Register a new schema for validation."""
        self.SCHEMAS[name] = schema
"""API contract tests — validate API response schemas."""
import pytest

from tests.cli/ethan.api_validator import APIResponseValidator


@pytest.fixture
def validator():
    """Provide API validator."""
    return APIResponseValidator()


class TestMessageAPI:
    """Validate /v1/message API contract."""

    def test_message_response_schema(self, validator):
        """POST /v1/message should return expected schema."""
        response = {
            "success": True,
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "goal_id": "",
            "message": "Event emitted into cognitive system",
        }

        result = validator.validate("/v1/message", response)
        assert result.valid, f"Schema validation failed: {result.errors}"

    def test_message_response_types(self, validator):
        """Response values should have correct types."""
        response = {
            "success": "true",  # Wrong: should be bool
            "event_id": 12345,  # Wrong: should be str
            "goal_id": "",
            "message": "ok",
        }

        result = validator.validate("/v1/message", response)
        assert not result.valid
        assert any("success" in str(e) for e in result.errors)
        assert any("event_id" in str(e) for e in result.errors)


class TestHealthAPI:
    """Validate /v1/health API contract."""

    def test_health_response_schema(self, validator):
        """GET /v1/health should return expected schema."""
        response = {
            "status": "ok",
            "service": "api-gateway",
            "nats_connected": True,
        }

        result = validator.validate("/v1/health", response)
        assert result.valid, f"Schema validation failed: {result.errors}"


class TestStateAPI:
    """Validate /v1/state API contract."""

    def test_state_response_schema(self, validator):
        """GET /v1/state should return expected schema."""
        response = {
            "mode": "idle",
            "modules_active": ["cli", "api"],
        }

        result = validator.validate("/v1/state", response)
        assert result.valid, f"Schema validation failed: {result.errors}"
"""Unit tests HROT — Human Root of Trust."""

import pytest

from core.human_root import HumanRoot, AuditLog, TrustRisk, ApprovalOutcome


@pytest.fixture()
def root() -> HumanRoot:
    return HumanRoot()


def test_request_returns_action_id(root: HumanRoot) -> None:
    action_id = root.request_approval(
        caller="test_user", category="system_modify",
        summary="Test critical change", risk=TrustRisk.HIGH,
    )
    assert action_id.startswith("app_")


def test_resolve_returns_approved(root: HumanRoot) -> None:
    action_id = root.request_approval(
        caller="test_user", category="system_modify",
        summary="Test change", risk=TrustRisk.LOW,
    )
    decision = root.resolve(action_id, approved=True)
    assert decision.outcome == ApprovalOutcome.APPROVED


def test_resolve_updates_audit_log(root: HumanRoot) -> None:
    action_id = root.request_approval(
        caller="test_user", category="system_modify",
        summary="Audit test", risk=TrustRisk.LOW,
    )
    root.resolve(action_id, approved=True)
    assert len(root._audit.entries()) >= 1


def test_audit_log_records_entry() -> None:
    audit = AuditLog()
    audit.record({"action_id": "app_123", "risk": TrustRisk.HIGH})
    entries = audit.entries()
    assert len(entries) == 1
    assert entries[0]["action_id"] == "app_123"


def test_is_trusted_false_for_critical(root: HumanRoot) -> None:
    action_id = root.request_approval(
        caller="test_user", category="system_modify",
        summary="Critical", risk=TrustRisk.CRITICAL,
    )
    assert root.is_human_root_trusted(action_id) is False


def test_is_trusted_true_for_low(root: HumanRoot) -> None:
    action_id = root.request_approval(
        caller="test_user", category="system_modify",
        summary="Safe", risk=TrustRisk.LOW,
    )
    assert root.is_human_root_trusted(action_id) is True

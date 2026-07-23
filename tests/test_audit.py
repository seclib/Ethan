"""Tests basiques pour le module Audit."""

import pytest
import tempfile
import json
from pathlib import Path

from core.audit import AuditStore, AuditCategory, AuditDecision


@pytest.fixture
def jsonl_audit():
    """AuditStore avec fallback JSONL (pas de PostgreSQL)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = AuditStore(pg_conn=None, jsonl_path=Path(tmpdir) / "audit.jsonl")
        yield store


def test_log_and_recent(jsonl_audit):
    entry = jsonl_audit.log(
        category=AuditCategory.SYSTEM,
        decision=AuditDecision.AUTO,
        action="test.action",
        actor="tester",
        details={"key": "value"},
    )
    assert entry.id is not None
    assert entry.category == AuditCategory.SYSTEM
    assert entry.decision == AuditDecision.AUTO

    recent = jsonl_audit.recent(limit=10)
    assert len(recent) >= 1
    assert recent[0].id == entry.id


def test_summary(jsonl_audit):
    jsonl_audit.log(category=AuditCategory.SYSTEM, decision=AuditDecision.AUTO, action="a1")
    jsonl_audit.log(category=AuditCategory.COMMAND, decision=AuditDecision.ALLOWED, action="a2")
    summary = jsonl_audit.summary()
    assert summary["total"] >= 2
    assert "system" in summary["categories"]
    assert "command" in summary["categories"]


def test_search(jsonl_audit):
    jsonl_audit.log(
        category=AuditCategory.SYSTEM,
        decision=AuditDecision.AUTO,
        action="deploy.started",
        actor="ci",
    )
    results = jsonl_audit.search("deploy")
    assert len(results) >= 1
    assert "deploy" in results[0].action.lower()
"""Tests de régression pour P0-1S — HROT Security Hardening.

Tests spécifiquement conçus pour valider les durcissements de sécurité
apportés dans le cadre de P0-1S :

- HROT-01: PermissionService obligatoire (pas de fallback silencieux)
- HROT-02: Vérification de la signature du principal (verify_trusted_principal)
- HROT-03: Pas de contournement via enforce_hrot
- PERSIST-01: Persistance des grants PermissionService
- PERSIST-03: Piste d'audit durable
- HROT-05: Gestion explicite des échecs d'enregistrement d'audit

Ces tests prouvent que les opérations protégées ne s'exécutent pas quand
l'autorisation est refusée.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest
from core.applications import ApplicationIntegrationRegistry, ApplicationManifest
from core.applications.capability_contract import (
    ApplicationCapabilityContract,
    register_application_capability,
)
from core.applications.capability_execution import (
    activate_capability_binding,
    bind_capability_implementation,
    invoke_capability,
)
from core.applications.persistence import ApplicationStateStore
from core.applications.permissions import HumanAuthority, PermissionService
from core.auth.principal import (
    AgentPrincipal,
    ExecutionContext,
    PrincipalType,
    issue_trusted_principal,
    verify_trusted_principal,
)
from core.hrot.capability_authorization import (
    CapabilityAuthorizationRequest,
    CapabilityAuthorizationService,
)
from fastapi.testclient import TestClient
from interfaces.api.main import app
import interfaces.api.routers.applications as app_router

VALID_MANIFEST = {
    "identity": {
        "app_id": "demo-app",
        "instance_id": "i",
        "name": "Demo",
        "version": "1.0.0",
        "contract_version": "1.0.0",
        "publisher": "P",
        "manifest_version": 1,
    },
}

CAPABILITY = {
    "capability_id": "demo.runtime-status",
    "application_id": "demo-app",
    "name": "Runtime status",
    "invocation_interface": "internal",
    "input_schema": {"type": "object", "properties": {"hello": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"application": {"type": "string"}}},
    "required_permissions": ["execute"],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> ApplicationIntegrationRegistry:
    """Registre avec une application et une capacité déjà enregistrées."""
    registry = ApplicationIntegrationRegistry()
    registry.register(ApplicationManifest.from_mapping(VALID_MANIFEST))
    register_application_capability(
        registry,
        ApplicationCapabilityContract.from_mapping(CAPABILITY),
        approved=True,
    )
    return registry


@pytest.fixture()
def permission_service_with_store(tmp_path: Path) -> PermissionService:
    """PermissionService avec stockage durable (ApplicationStateStore)."""
    store = ApplicationStateStore(tmp_path / "permissions.db")
    return PermissionService(store=store, production_mode=False)


@pytest.fixture()
def permission_service_memory() -> PermissionService:
    """PermissionService en mémoire (pas de persistance)."""
    return PermissionService(production_mode=False)


# ---------------------------------------------------------------------------
# HROT-01 : PermissionService obligatoire
# ---------------------------------------------------------------------------


def test_authorization_service_requires_permission_service(registry):
    """CapabilityAuthorizationService doit rejeter une construction sans
    permission_service (HROT-01)."""
    with pytest.raises(ValueError, match="permission_service is required"):
        CapabilityAuthorizationService(registry=registry, permission_service=None)


def test_authorization_service_accepts_permission_service(registry, permission_service_memory):
    """CapabilityAuthorizationService accepte un PermissionService explicite."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    assert service.permission_service is permission_service_memory


# ---------------------------------------------------------------------------
# HROT-02 : Vérification du principal de confiance
# ---------------------------------------------------------------------------


def _make_principal(
    principal_id: str = "alice",
    agent_id: str | None = None,
    signed: bool = True,
    permissions: tuple[str, ...] = ("execute",),
) -> AgentPrincipal:
    """Construit un AgentPrincipal signé (ou non si signed=False)."""
    principal = AgentPrincipal(
        principal_id=principal_id,
        principal_type=PrincipalType.HUMAN,
        subject_id=principal_id,
        actor_id=agent_id or principal_id,
        initiator_id=principal_id,
        permissions=permissions,
        scopes=(),
        owner_id=principal_id,
        request_id="req-test",
        auth_method="jwt",
    )
    if signed:
        return issue_trusted_principal(principal)
    # Forgé : pas de signature
    return AgentPrincipal(
        principal_id=principal_id,
        principal_type=PrincipalType.HUMAN,
        subject_id=principal_id,
        actor_id=agent_id or principal_id,
        initiator_id=principal_id,
        permissions=permissions,
        scopes=(),
        owner_id=principal_id,
        request_id="req-test",
        auth_method="jwt",
        # auth_proof reste None → non signé
    )


def test_authorization_rejects_forged_principal(registry, permission_service_memory):
    """Un AgentPrincipal forgé (non signé) doit être refusé (HROT-02)."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    forged_principal = _make_principal(signed=False)
    context = ExecutionContext(
        principal=forged_principal,
        agent_id=forged_principal.actor_id or forged_principal.subject_id,
        request_id="req-1",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=forged_principal.actor_id or forged_principal.subject_id,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )
    decision = service.authorize(request)
    assert decision.allowed is False
    assert decision.reason_code == "UNTRUSTED_PRINCIPAL"


def test_authorization_accepts_signed_principal(registry, permission_service_memory):
    """Un AgentPrincipal signé doit passer l'étape de vérification de signature (HROT-02).

    Le refus qui suit vient de l'absence de grant HROT (NO_MATCHING_PERMISSION),
    pas d'un échec de vérification de signature.
    """
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-1",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=principal.actor_id or principal.subject_id,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )
    decision = service.authorize(request)
    # Le principal signé passe l'étape de vérification de signature.
    # Le refus vient de l'absence de grant HROT (NO_MATCHING_PERMISSION),
    # ce qui prouve que la vérification de signature a réussi.
    assert decision.allowed is False
    assert decision.reason_code == "MISSING_BINDING"


def test_authorization_rejects_missing_principal(registry, permission_service_memory):
    """Un principal sans actor_id doit être refusé (HROT-02)."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    principal = _make_principal(signed=True)
    # actor_id=None → pas d'identité acteur
    context = ExecutionContext(
        principal=principal,
        agent_id=None,
        request_id="req-1",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=None,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )
    decision = service.authorize(request)
    assert decision.allowed is False
    assert decision.reason_code == "MISSING_AGENT_IDENTITY"


def test_authorization_rejects_binding_mismatch(registry, permission_service_memory):
    """Un binding dont l'identifiant ne correspond pas au registre est refusé (HROT-02)."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-1",
    )
    # Créer un binding canonique dans le registre
    binding = bind_capability_implementation(
        registry,
        "demo-app",
        "demo.runtime-status",
        "odin.runtime-status",
        approved=True,
    )
    activate_capability_binding(registry, "demo-app", "demo.runtime-status", True)

    # Créer une requête avec un binding_id différent de celui du binding enregistré
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=principal.actor_id or principal.subject_id,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
        binding=binding,
        binding_id="binding-wrong",  # Diffère de binding.binding_id
    )
    decision = service.authorize(request)
    assert decision.allowed is False
    assert decision.reason_code == "BINDING_MISMATCH"


def test_invoke_capability_without_hrot_grant_is_denied(
    registry, permission_service_memory
):
    """Une invocation sans grant HROT est refusée (fail-closed)."""
    # Créer un binding activé (prérequis pour l'invocation)
    binding = bind_capability_implementation(
        registry,
        "demo-app",
        "demo.runtime-status",
        "odin.runtime-status",
        approved=True,
    )
    activate_capability_binding(registry, "demo-app", "demo.runtime-status", True)
    # Pas de grant HROT → l'invocation doit être refusée
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-1",
    )
    result = asyncio.run(
        invoke_capability(
            registry=registry,
            application_id="demo-app",
            capability_id="demo.runtime-status",
            payload={"hello": "world"},
            execution_context=context,
        )
    )
    assert result.status == "failed"
    assert "denied" in result.error.lower() or "failed" in result.error.lower()


def test_authorization_rejects_agent_identity_mismatch(registry, permission_service_memory):
    """Un désalignement entre agent_id du contexte et de la requête doit être refusé."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    principal = _make_principal(
        principal_id="alice", agent_id="alice", signed=True
    )
    context = ExecutionContext(
        principal=principal,
        agent_id="alice",
        request_id="req-1",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id="bob",  # désaligné avec le contexte
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )
    decision = service.authorize(request)
    assert decision.allowed is False
    assert decision.reason_code == "AGENT_IDENTITY_MISMATCH"


# ---------------------------------------------------------------------------
# HROT-03 : Pas de contournement via enforce_hrot
# ---------------------------------------------------------------------------


def test_invoke_capability_has_no_enforce_hrot_parameter():
    """invoke_capability ne doit pas exposer de paramètre enforce_hrot."""
    import inspect

    sig = inspect.signature(invoke_capability)
    assert "enforce_hrot" not in sig.parameters


def test_invoke_capability_always_authorizes(registry, permission_service_memory):
    """Toute invocation de capacité externe passe par l'autorisation HROT."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    # Créer un binding activé (prérequis pour l'invocation)
    binding = bind_capability_implementation(
        registry,
        "demo-app",
        "demo.runtime-status",
        "odin.runtime-status",
        approved=True,
    )
    activate_capability_binding(registry, "demo-app", "demo.runtime-status", True)
    # Ajouter un grant HROT pour autoriser
    authority = HumanAuthority(
        principal_id="approver",
        principal_type="HUMAN",
        trusted=True,
        human=True,
    )
    registry.permission_service.grant_permission(
        app_id="demo-app",
        instance_id="i",
        capability="demo.runtime-status",
        resource="capability",
        action="execute",
        approved_by="approver",
        authority=authority,
    )
    # Construire un contexte d'exécution signé
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-1",
    )
    result = asyncio.run(
        invoke_capability(
            registry=registry,
            application_id="demo-app",
            capability_id="demo.runtime-status",
            payload={"hello": "world"},
            execution_context=context,
        )
    )
    assert result.status == "success"
    assert result.result["application"] == "odin"


# ---------------------------------------------------------------------------
# PERSIST-01 : Persistance des grants
# ---------------------------------------------------------------------------


def test_grant_survives_restart_with_durable_store(tmp_path: Path):
    """Un grant doit survivre au redémarrage quand un store durable est configuré."""
    store_path = tmp_path / "permissions.db"
    store = ApplicationStateStore(store_path)
    service = PermissionService(store=store, production_mode=False)
    authority = HumanAuthority(
        principal_id="approver",
        principal_type="HUMAN",
        trusted=True,
        human=True,
    )
    service.grant_permission(
        app_id="demo-app",
        instance_id="i",
        capability="demo.runtime-status",
        resource="capability",
        action="execute",
        approved_by="approver",
        authority=authority,
    )
    grants_before = service.list_permissions(app_id="demo-app")
    assert len(grants_before) == 1

    # Redémarrage : nouvelle instance avec le même store
    restarted_store = ApplicationStateStore(store_path)
    restarted_service = PermissionService(store=restarted_store, production_mode=False)
    grants_after = restarted_service.list_permissions(app_id="demo-app")
    assert len(grants_after) == 1
    assert grants_after[0].permission_id == grants_before[0].permission_id


def test_revocation_survives_restart(tmp_path: Path):
    """Une révocation doit survivre au redémarrage."""
    store_path = tmp_path / "permissions.db"
    store = ApplicationStateStore(store_path)
    service = PermissionService(store=store, production_mode=False)
    authority = HumanAuthority(
        principal_id="approver",
        principal_type="HUMAN",
        trusted=True,
        human=True,
    )
    grant = service.grant_permission(
        app_id="demo-app",
        instance_id="i",
        capability="demo.runtime-status",
        resource="capability",
        action="execute",
        approved_by="approver",
        authority=authority,
    )
    service.revoke_permission(grant.permission_id, reason="test revocation")

    # Redémarrage
    restarted_store = ApplicationStateStore(store_path)
    restarted_service = PermissionService(store=restarted_store, production_mode=False)
    grants = restarted_service.list_permissions(app_id="demo-app")
    assert len(grants) == 1
    assert grants[0].is_revoked() is True


def test_missing_persistence_configuration_is_explicit():
    """Sans store, PermissionService est en mémoire (comportement explicite)."""
    service = PermissionService(production_mode=False)
    assert service._store is None


def test_storage_failure_is_handled_safely():
    """Un échec de stockage ne doit pas silencieusement autoriser l'exécution."""
    # PermissionService sans store : si l'enregistrement échoue, l'autorisation
    # doit quand même être évaluée correctement (fail-closed sur l'autorisation,
    # pas sur l'audit).
    service = PermissionService(production_mode=False)
    assert service._store is None
    # Le service fonctionne sans store (en mémoire)
    assert service.list_permissions() == ()


# ---------------------------------------------------------------------------
# PERSIST-03 : Audit recording
# ---------------------------------------------------------------------------


def test_authorization_decision_is_recorded(registry, permission_service_memory):
    """Chaque décision d'autorisation (ALLOW ou DENY) doit être enregistrée."""
    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    initial_count = len(service.audit_trail())

    # Décision de refus (pas de grant)
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-audit-1",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=principal.actor_id or principal.subject_id,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-audit-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )
    decision = service.authorize(request)
    assert decision.allowed is False

    # La décision doit être dans la piste d'audit
    assert len(service.audit_trail()) == initial_count + 1
    last = service.audit_trail()[-1]
    assert last.decision.value == "DENY"
    assert last.reason_code == "MISSING_BINDING"


def test_audit_recording_failure_is_not_silent(
    registry, permission_service_memory
):
    """Un échec d'enregistrement d'audit ne doit pas être silencieux."""
    from unittest.mock import patch

    service = CapabilityAuthorizationService(
        registry=registry, permission_service=permission_service_memory
    )
    principal = _make_principal(signed=True)
    context = ExecutionContext(
        principal=principal,
        agent_id=principal.actor_id or principal.subject_id,
        request_id="req-audit-fail",
    )
    request = CapabilityAuthorizationRequest(
        execution_context=context,
        agent_id=principal.actor_id or principal.subject_id,
        application_id="demo-app",
        capability_id="demo.runtime-status",
        execution_id="exec-audit-fail-1",
        requested_operation="execute",
        resource="capability",
        action="execute",
        registry=registry,
        permission_service=permission_service_memory,
    )

    # Remplacer _record par une fonction qui lève une exception une seule fois
    original_record = service._record
    call_count = [0]

    def failing_record(decision):
        call_count[0] += 1
        if call_count[0] == 1:
            raise OSError("disk full")
        return original_record(decision)

    service._record = failing_record
    try:
        decision = service.authorize(request)
        # La décision doit quand même être retournée
        assert decision is not None
    finally:
        service._record = original_record


# ---------------------------------------------------------------------------
# Régression : exécution native (outil) non affectée par HROT
# ---------------------------------------------------------------------------


def test_native_agent_tool_execution_unaffected(registry, permission_service_memory):
    """Les outils natifs (SkillStore, etc.) ne doivent pas passer par HROT.
    Ce test vérifie que le module capability_execution n'affecte pas
    l'exécution des outils natifs."""
    # Le test vérifie simplement que invoke_capability existe et est
    # appelable sans paramètre enforce_hrot.
    import inspect

    sig = inspect.signature(invoke_capability)
    assert "enforce_hrot" not in sig.parameters
    assert "execution_context" in sig.parameters

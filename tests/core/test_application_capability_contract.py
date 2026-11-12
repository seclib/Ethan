from __future__ import annotations

import pytest

from core import applications
from core.applications.capability_contract import (
    ApplicationCapabilityContract,
    DuplicatedApplicationCapabilityError,
    get_application_capability_contracts,
    register_application_capability,
)
from core.applications.models import ValidationError


def _manifest():
    return {
        "identity": {
            "app_id": "demo-app",
            "instance_id": "i",
            "name": "Demo",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "P",
            "manifest_version": 1,
        }
    }


def test_valid_contract_and_idempotence():
    registry = applications.ApplicationIntegrationRegistry(store=None)
    registry.register(applications.ApplicationManifest.from_mapping(_manifest()))
    contract = ApplicationCapabilityContract(
        capability_id="demo-cap",
        application_id="demo-app",
        name="Demo",
        invocation_interface="application_api",
        input_schema={"type": "object"},
        output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        required_permissions=("read",),
    )
    first = register_application_capability(registry, contract, approved=True)
    second = register_application_capability(registry, contract, approved=True)
    assert first is second
    assert len(get_application_capability_contracts(registry)) == 1


def test_missing_required_field():
    with pytest.raises(ValidationError, match="missing required field"):
        ApplicationCapabilityContract.from_mapping({"application_id": "x", "name": "n"})


def test_unknown_field_rejected():
    with pytest.raises(ValidationError, match="unknown fields"):
        ApplicationCapabilityContract.from_mapping(
            {
                "capability_id": "c",
                "application_id": "demo-app",
                "name": "n",
                "surprise": 1,
            }
        )


def test_invalid_permission_rejected():
    with pytest.raises(ValidationError, match="unknown permission"):
        ApplicationCapabilityContract(
            capability_id="c",
            application_id="demo-app",
            name="n",
            required_permissions=("impossible-permission",),
        ).validate()


def test_invalid_timeout_rejected():
    with pytest.raises(ValidationError, match="timeout_seconds"):
        ApplicationCapabilityContract(
            capability_id="c",
            application_id="demo-app",
            name="n",
            timeout_seconds=0,
        ).validate()


def test_duplicate_capability_id_conflict():
    registry = applications.ApplicationIntegrationRegistry(store=None)
    registry.register(applications.ApplicationManifest.from_mapping(_manifest()))
    first = ApplicationCapabilityContract(
        capability_id="dup",
        application_id="demo-app",
        name="One",
        timeout_seconds=1,
    ).validate() or ApplicationCapabilityContract(
        capability_id="dup",
        application_id="demo-app",
        name="One",
        timeout_seconds=1,
    )
    register_application_capability(registry, first, approved=True)
    conflicting = ApplicationCapabilityContract(
        capability_id="dup",
        application_id="demo-app",
        name="Two",
        timeout_seconds=1,
    )
    with pytest.raises(DuplicatedApplicationCapabilityError):
        register_application_capability(registry, conflicting, approved=True)


def test_register_requires_application():
    registry = applications.ApplicationIntegrationRegistry(store=None)
    contract = ApplicationCapabilityContract(
        capability_id="c",
        application_id="missing",
        name="n",
    )
    with pytest.raises(ValueError):
        register_application_capability(registry, contract, approved=True)

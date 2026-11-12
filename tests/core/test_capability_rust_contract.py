import json

from core.capability_manager.builtin import build_manager
from core.capability_manager.rust_contract import validate_contract


def test_rust_contract_accepts_declared_python_capabilities():
    manager = build_manager()
    specs = list(getattr(manager, "_registry", {}).values())
    payload = {
        "schema_version": "ethan.capability.v1",
        "capabilities": [
            {
                "id": spec.id,
                "name": spec.name,
                "state": "DECLARED",
                "backend": spec.backend,
                "metadata": {"python_executable": spec.python_executable},
            }
            for spec in specs
        ],
    }
    result = validate_contract(json.dumps(payload))
    assert result["ok"] is True
    assert result["total"] == len(specs)


def test_rust_contract_rejects_empty_id():
    payload = {"schema_version": "ethan.capability.v1", "capabilities": [{"id": "", "state": "DECLARED"}]}
    result = validate_contract(json.dumps(payload))
    assert result["ok"] is False
    assert result["error"] == "invalid_contract"

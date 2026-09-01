"""État de sécurité — résumé sérialisable pour l'observabilité (Phase 07).

Fournit un instantané **lecture seule** du système de sécurité : politiques
chargées, capabilities actives et statistiques d'audit. Ne contient aucun
secret et n'expose aucune action de mutation.
"""

from __future__ import annotations

from typing import Any

from core.security.policy import PolicyEngine, PolicyLevel


def security_status(
    engine: PolicyEngine | None = None,
    capabilities: Any | None = None,
    audit_store: Any | None = None,
) -> dict[str, Any]:
    """Retourne un résumé sérialisable de l'état de sécurité.

    Args:
        engine: PolicyEngine à décrire (défaut : les règles par défaut CORE).
        capabilities: CapabilityManager (Phase 05) à décrire, ou None.
        audit_store: AuditStore (Core) à décrire, ou None.

    Returns:
        Dictionnaire JSON-sérialisable (aucun secret, aucune donnée sensible).
    """
    engine = engine or PolicyEngine()

    rules = engine.rules
    by_level: dict[str, int] = {}
    by_effect: dict[str, int] = {}
    categories: set[str] = set()
    for rule in rules:
        if not getattr(rule, "enabled", True):
            continue
        level = getattr(rule, "level", None)
        key = level.name if isinstance(level, PolicyLevel) else str(level)
        by_level[key] = by_level.get(key, 0) + 1
        effect = getattr(rule, "effect", None)
        by_effect[effect.value if hasattr(effect, "value") else str(effect)] = (
            by_effect.get(effect.value if hasattr(effect, "value") else str(effect), 0)
            + 1
        )
        categories.add(getattr(rule, "category", "?"))

    payload: dict[str, Any] = {
        "policies": {
            "total": len(rules),
            "by_level": by_level,
            "by_effect": by_effect,
            "categories": sorted(categories),
        },
        "capabilities": {"active": 0, "subjects": []},
        "audit": {"total": 0},
    }

    if capabilities is not None:
        try:
            active = capabilities.list_capabilities()
            subjects = sorted({c.subject for c in active})
            payload["capabilities"] = {
                "active": len(active),
                "subjects": subjects,
                "summary": capabilities.audit_summary(),
            }
        except Exception:
            payload["capabilities"] = {"active": 0, "subjects": [], "error": True}

    if audit_store is not None:
        try:
            summary = audit_store.audit_summary()
            payload["audit"] = summary
        except Exception:
            payload["audit"] = {"total": 0, "error": True}

    return payload

"""Policy Engine — Moteur d'évaluation hiérarchique des actions sensibles.

Implémente la hiérarchie à 8 niveaux et les axiomes A1..A6 définis dans
`docs/security/03-policy-hierarchy.md` :

- A1 (ordre total) : le niveau le plus haut possédant une règle l'emporte.
- A2 (non-annulation) : on s'arrête au premier niveau qui décide ; un niveau
  inférieur ne peut ni annuler ni élargir une décision supérieure.
- A3 (conflit intra-niveau) : à niveau égal, la règle la plus restrictive gagne.
- A4 (fail-closed) : aucune règle ne matche → DENY.
- A5 (pas d'inférence) : matching exact action/resource — lire ≠ écrire.
- A6 (neutralité du demandeur) : la source n'influence jamais la décision.

Le moteur est **indépendant du LLM** : il n'exécute aucun modèle et n'accepte
aucune instruction de texte comme source de règle.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Iterable

from core.security.policy.rules import default_rules
from core.security.policy.types import (
    Policy,
    PolicyDecision,
    PolicyEffect,
    PolicyError,
    PolicyLevel,
    PolicyRequest,
    PolicyResult,
)

logger = logging.getLogger(__name__)

# Niveaux dans l'ordre du plus fort (1) au plus faible (8).
_LEVELS = sorted(PolicyLevel, key=lambda level: level.value)


class PolicyEngine:
    """Moteur d'évaluation des politiques hiérarchiques."""

    def __init__(self, rules: Iterable[Policy] | None = None) -> None:
        self._rules: dict[str, Policy] = {}
        if rules is None:
            rules = default_rules()
        for rule in rules:
            self._rules[rule.id] = rule

    # ── Gestion des règles ─────────────────────────────────────────────

    @property
    def rules(self) -> list[Policy]:
        """Toutes les règles actives, dans l'ordre d'insertion."""
        return [rule for rule in self._rules.values() if rule.enabled]

    def add_rule(self, rule: Policy) -> None:
        """Ajoute (ou remplace) une règle.

        Utilisé par la gouvernance (chargement de politiques) et par les
        tests. Une règle portant un id existant est remplacée.
        """
        if not isinstance(rule, Policy):
            raise PolicyError(f"Not a Policy: {rule!r}")
        self._rules[rule.id] = rule
        logger.debug("Policy added: %s (level=%s)", rule.id, rule.level.name)

    def remove_rule(self, policy_id: str) -> bool:
        """Retire une règle. Retourne True si elle existait."""
        return self._rules.pop(policy_id, None) is not None

    def get_rule(self, policy_id: str) -> Policy | None:
        """Retourne une règle par id."""
        return self._rules.get(policy_id)

    # ── Évaluation ─────────────────────────────────────────────────────

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """Évalue une requête et retourne la décision.

        Algorithme (Phase 03 §4) :
        1. Collecter les règles matchantes.
        2. Si aucune → DENY (fail-closed, A4).
        3. Retenir le niveau le plus fort parmi les règles matchantes (A1).
        4. Dans ce niveau, prendre l'effet le plus restrictif (A3).
        5. Ne pas descendre plus bas (A2) : un niveau inférieur ne peut
           ni annuler ni élargir la décision.
        """
        # 1. Règles matchantes (A5 : matching exact action/resource/catégorie).
        matched = [
            rule for rule in self._rules.values()
            if rule.enabled
            and rule.matches(request.category, request.action, request.resource)
        ]

        # 2. Fail-closed : silence = refus (A4).
        if not matched:
            return PolicyDecision(
                result=PolicyResult.DENY,
                reason=(
                    "Aucune politique n'autorise explicitement cette action "
                    "(deny by default)."
                ),
                matched=[],
            )

        # 3. Niveau le plus fort (A1).
        matched_by_level: dict[int, list[Policy]] = defaultdict(list)
        for rule in matched:
            matched_by_level[rule.level.value].append(rule)

        top_level = min(matched_by_level)
        top_rules = matched_by_level[top_level]

        # 4. Effet le plus restrictif du niveau retenu (A3).
        top_rules_sorted = sorted(top_rules, key=lambda rule: rule.restrictivity)
        decisive = top_rules_sorted[0]
        restrictivity_score = decisive.restrictivity
        # Toutes les règles du niveau partageant l'effet le plus restrictif.
        decisive_group = [
            rule for rule in top_rules
            if rule.restrictivity == restrictivity_score
        ]

        # 5. Décision finale (A2 : on ne redescend pas).
        result = _effect_to_result(decisive.effect)
        reason = decisive.reason or _default_reason(result, request)

        logger.info(
            "Policy %s: %s %s:%s on %r -> %s (level=%s, policy=%s)",
            request.source,
            request.category,
            request.action,
            request.resource,
            result.value,
            PolicyLevel(top_level).name,
            decisive.id,
        )

        return PolicyDecision(
            result=result,
            reason=reason,
            policy_id=decisive.id,
            level=PolicyLevel(top_level),
            matched=[rule.id for rule in decisive_group],
        )

    def check(
        self,
        category: str,
        action: str,
        resource: str,
        params: dict | None = None,
        source: str = "unknown",
    ) -> PolicyDecision:
        """Raccourci pour évaluer une requête sans construire l'objet."""
        return self.evaluate(
            PolicyRequest(
                category=category,
                action=action,
                resource=resource,
                params=params or {},
                source=source,
            )
        )


def _effect_to_result(effect: PolicyEffect) -> PolicyResult:
    """Traduit l'effet d'une règle en résultat final."""
    if effect is PolicyEffect.DENY:
        return PolicyResult.DENY
    if effect is PolicyEffect.REQUIRE_CONFIRMATION:
        return PolicyResult.REQUIRE_CONFIRMATION
    return PolicyResult.ALLOW


def _default_reason(result: PolicyResult, request: PolicyRequest) -> str:
    """Raison par défaut lorsque la règle n'en fournit pas."""
    return (
        f"Action {request.category}:{request.action} sur {request.resource} "
        f"-> {result.value}"
    )

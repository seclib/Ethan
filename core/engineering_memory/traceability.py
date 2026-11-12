"""Traçabilité automatique des interventions d'ingénierie — DAĒNĀ.

P2.8.3 — Service Core qui rend toute intervention technique
**trouvable, durable et consultable** dans DAĒNĀ.

Principes
---------
* **Une seule source documentaire.** Les rapports sont des `MemoryRecord`
  écrits par l'Engineering Memory dans le vault `daena/`. Aucun second
  moteur de journalisation, aucune nouvelle base.
* **Les types existants sont réutilisés.** Le rapport d'intervention est un
  `ENGINEERING_EVENT`, une anomalie un `INCIDENT`, une dette une
  `TECHNICAL_DEBT`. Aucun type nouveau n'est introduit (P2.8.4 reste à faire).
* **Les liens plutôt que la duplication.** Un rapport référence ses anomalies,
  corrections, décisions et tests **par identifiant**. L'historique d'une
  anomalie est porté par des événements corrélés (`correlation_id`), jamais par
  la réécriture du document d'origine.
* **Aucune duplication.** L'identifiant d'intervention est déterministe : la
  même intervention ré-enregistrée avec le même contenu met à jour le même
  document au lieu d'en créer un second ; un contenu différent est signalé
  comme conflit et n'écrase rien.
* **Les secrets ne sont jamais écrits.** Tout contenu passe par une
  rédaction avant persistance, et la `SecurityPolicy` de l'Engineering Memory
  contrôle une seconde fois la charge utile structurée.
* **Les ancres projet sont utilisées** lorsqu'elles sont disponibles
  (P2.8.2) : un rapport rattaché à un projet est retrouvable par projet.

Structure d'un rapport
----------------------
Rubriques A à J (identification, état initial, travaux, corrections,
observations, sécurité, dette, tests, décisions, travaux restants). La
structure complète est conservée dans ``metadata`` (forme structurée, donc
interrogeable) et rendue en Markdown dans ``notes`` (forme lisible).
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordOrigin,
    RecordType,
    SourceOfFactLevel,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redaction des secrets
# ---------------------------------------------------------------------------

# Motifs de secrets couramment rencontres dans les rapports techniques.
# L'ordre compte : les motifs les plus spécifiques précèdent les motifs
# génériques, afin qu'une clé OpenAI ne soit pas d'abord attrapée par la
# règle « token=... ».
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"), "[REDACTE:ANTHROPIC_KEY]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[REDACTE:OPENAI_KEY]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTE:GITHUB_TOKEN]"),
    (re.compile(r"glpat-[A-Za-z0-9_\-]{16,}"), "[REDACTE:GITLAB_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTE:AWS_KEY]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9_\-]{10,}"), "[REDACTE:SLACK_TOKEN]"),
    (re.compile(r"ethan_[A-Za-z0-9_\-]{16,}"), "[REDACTE:ETHAN_API_KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), "[REDACTE:JWT]"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "[REDACTE:CLE_PRIVEE]",
    ),
    (re.compile(r"(?i)\bauthorization\b\s*:\s*bearer\s+\S+"), "authorization: Bearer [REDACTE]"),
    (
        re.compile(
            r"(?i)\b(password|passwd|secret|api[_-]?key|token|mot\s+de\s+passe|motdepasse|mdp|cle\s+api|jeton)\b"
            r"\s*[=:]\s*[\"']?([^\s\"',;]{6,})"
        ),
        r"\1=[REDACTE]",
    ),
    (re.compile(r"(?i)(://[^:/\s]+:)[^@\s]+(@)"), r"\1[REDACTE]\2"),
)


def redact(text: str) -> str:
    """Masque les secrets dans un texte destiné à un rapport.

    Args:
        text: Texte à assainir.

    Returns:
        Texte sans secret exploitable.
    """
    if not text:
        return text
    cleaned = text
    for pattern, replacement in _SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def redact_structure(value: Any) -> Any:
    """Assainit récursivement une structure (dict, liste, scalaires).

    Args:
        value: Structure à assainir.

    Returns:
        Structure équivalente, sans secret.
    """
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {key: redact_structure(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_structure(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Modele de rapport
# ---------------------------------------------------------------------------


class AnomalyState(str, Enum):
    """Etats d'une anomalie (vocabulaire impose par la demande)."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    FIXED = "FIXED"
    DEFERRED = "DEFERRED"
    BLOCKED = "BLOCKED"


class InterventionNature(str, Enum):
    """Nature d'une intervention technique."""

    FEATURE = "feature"
    BUGFIX = "bugfix"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"
    INVESTIGATION = "investigation"
    AUDIT = "audit"
    TESTING = "testing"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class ValidationLevel(str, Enum):
    """Niveaux de validation — terminologie stricte."""

    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    RUNTIME_VALIDATED = "RUNTIME_VALIDATED"
    E2E_VALIDATED = "E2E_VALIDATED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_VERIFIED = "NOT_VERIFIED"


@dataclass
class CorrectionEntry:
    """Une correction effectuee pendant l'intervention."""

    problem: str
    root_cause: str = ""
    solution: str = ""
    components: List[str] = field(default_factory=list)
    verification_tests: List[str] = field(default_factory=list)
    observed_result: str = ""


@dataclass
class AnomalyEntry:
    """Une anomalie decouverte pendant l'intervention."""

    anomaly_id: str
    description: str
    component: str = ""
    severity: str = "MEDIUM"
    impact: str = ""
    cause: str = ""
    state: AnomalyState = AnomalyState.OPEN
    reference: str = ""


@dataclass
class SecurityFindingEntry:
    """Une faille ou un probleme de securite identifie."""

    finding_id: str
    nature: str
    component: str = ""
    risk_level: str = "MEDIUM"
    impact: str = ""
    corrective_measures: str = ""
    state: str = "OPEN"
    security_tests: List[str] = field(default_factory=list)


@dataclass
class TechnicalDebtEntry:
    """Une dette technique identifiee et conservee."""

    debt_id: str
    description: str
    origin: str = ""
    justification: str = ""
    risk: str = ""
    priority: str = "MEDIUM"
    components: List[str] = field(default_factory=list)
    recommended_action: str = ""
    dependencies: List[str] = field(default_factory=list)
    state: str = "OPEN"


@dataclass
class TestResultEntry:
    """Un test execute et son resultat."""

    name: str
    command: str = ""
    passed: int = 0
    failed: int = 0
    result: str = ""
    notes: str = ""


@dataclass
class DecisionEntry:
    """Une decision architecturale prise pendant l'intervention."""

    decision: str
    rationale: str = ""
    alternatives: List[str] = field(default_factory=list)
    consequences: str = ""
    adr: str = ""


@dataclass
class InterventionReport:
    """Rapport structure d'une intervention technique.

    Les rubriques A a J sont couvertes. Les champs non renseignes restent
    vides : un rapport ne pretend pas documenter ce qui ne l'a pas ete.
    """

    intervention_id: str
    created_at: str = ""
    project_id: Optional[str] = None
    mission: str = ""
    phase: str = ""
    agent: str = ""
    session_id: str = ""
    session_title: str = ""
    nature: InterventionNature = InterventionNature.FEATURE
    status: str = "RECORDED"
    validation_level: ValidationLevel = ValidationLevel.IMPLEMENTED

    # B — Etat initial
    context: str = ""
    initial_problem: str = ""
    initial_state: str = ""
    pre_existing_anomalies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # C — Travaux realises
    work_description: str = ""
    features: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    schema_or_config_changes: List[str] = field(default_factory=list)
    change_reasons: List[str] = field(default_factory=list)

    # D — Corrections
    corrections: List[CorrectionEntry] = field(default_factory=list)

    # E — Observations et anomalies
    anomalies: List[AnomalyEntry] = field(default_factory=list)

    # F — Securite
    security_findings: List[SecurityFindingEntry] = field(default_factory=list)

    # G — Dette technique
    technical_debt: List[TechnicalDebtEntry] = field(default_factory=list)

    # H — Tests et validations
    tests: List[TestResultEntry] = field(default_factory=list)
    tests_not_run: List[str] = field(default_factory=list)
    validation_limits: List[str] = field(default_factory=list)

    # I — Decisions
    decisions: List[DecisionEntry] = field(default_factory=list)

    # J — Travaux restants
    remaining_work: List[str] = field(default_factory=list)
    deferred_actions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    persistent_risks: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # -- Serialisation ------------------------------------------------

    def to_structure(self) -> Dict[str, Any]:
        """Retourne la structure complete du rapport (forme interrogeable)."""
        return redact_structure(asdict(self))

    def render_markdown(self) -> str:
        """Rend le rapport en Markdown lisible.

        Returns:
            Corps Markdown du rapport.
        """
        lines: List[str] = []
        add = lines.append

        add(f"# Intervention {self.intervention_id}")
        add("")
        add(f"**Nature** : {self.nature.value} · **Statut** : {self.status} · "
            f"**Validation** : {self.validation_level.value}")
        if self.project_id:
            add(f"**Projet** : `{self.project_id}`")
        if self.mission or self.phase:
            add(f"**Mission** : {self.mission or '—'} · **Phase** : {self.phase or '—'}")
        if self.agent:
            add(f"**Agent / outil** : {self.agent}")
        if self.session_id:
            add(f"**Session** : `{self.session_id}`")
        add(f"**Créé le** : {self.created_at}")
        add("")

        add("## A. Identification")
        add("")
        add(f"- Identifiant : `{self.intervention_id}`")
        add(f"- Date et heure : {self.created_at}")
        add(f"- Projet : {self.project_id or 'non attribué (portee globale)'}")
        add(f"- Mission / phase : {self.mission or '—'} / {self.phase or '—'}")
        add(f"- Agent ou outil : {self.agent or '—'}")
        add(f"- Session : {self.session_id or '—'}")
        add(f"- Nature : {self.nature.value}")
        add(f"- Statut : {self.status}")
        add("")

        add("## B. État initial")
        add("")
        add(f"- Contexte technique : {self.context or '—'}")
        add(f"- Problème ou besoin initial : {self.initial_problem or '—'}")
        add(f"- État observé avant intervention : {self.initial_state or '—'}")
        add("- Anomalies déjà présentes :")
        if self.pre_existing_anomalies:
            for item in self.pre_existing_anomalies:
                add(f"  - {item}")
        else:
            add("  - aucune")
        add("- Contraintes et dépendances :")
        if self.constraints:
            for item in self.constraints:
                add(f"  - {item}")
        else:
            add("  - aucune")
        add("")

        add("## C. Travaux réalisés")
        add("")
        add(f"- Description : {self.work_description or '—'}")
        add("- Fonctionnalités développées :")
        for item in self.features or ["—"]:
            add(f"  - {item}")
        add("- Composants concernés :")
        for item in self.components or ["—"]:
            add(f"  - {item}")
        add("- Fichiers créés :")
        for item in self.files_created or ["—"]:
            add(f"  - `{item}`")
        add("- Fichiers modifiés :")
        for item in self.files_modified or ["—"]:
            add(f"  - `{item}`")
        add("- Fichiers supprimés :")
        for item in self.files_deleted or ["—"]:
            add(f"  - `{item}`")
        add("- Modifications de schéma ou de configuration :")
        for item in self.schema_or_config_changes or ["—"]:
            add(f"  - {item}")
        add("- Raisons des changements :")
        for item in self.change_reasons or ["—"]:
            add(f"  - {item}")
        add("")

        add("## D. Corrections effectuées")
        add("")
        if self.corrections:
            for correction in self.corrections:
                add(f"### {correction.problem}")
                add("")
                add(f"- Cause racine : {correction.root_cause or 'non déterminée'}")
                add(f"- Solution appliquée : {correction.solution or '—'}")
                add("- Composants concernés :")
                for item in correction.components or ["—"]:
                    add(f"  - {item}")
                add("- Tests de vérification :")
                for item in correction.verification_tests or ["—"]:
                    add(f"  - `{item}`")
                add(f"- Résultat constaté : {correction.observed_result or '—'}")
                add("")
        else:
            add("Aucune correction enregistrée.")
            add("")

        add("## E. Observations et anomalies")
        add("")
        if self.anomalies:
            add("| ID | Description | Composant | Gravité | Impact | Cause | État |")
            add("|---|---|---|---|---|---|---|")
            for anomaly in self.anomalies:
                add(
                    f"| `{anomaly.anomaly_id}` | {anomaly.description} | "
                    f"{anomaly.component or '—'} | "
                    f"{anomaly.severity} | {anomaly.impact or '—'} | "
                    f"{anomaly.cause or 'hypothèse'} | "
                    f"{anomaly.state.value} |"
                )
        else:
            add("Aucune anomalie enregistrée.")
        add("")

        add("## F. Sécurité et failles")
        add("")
        if self.security_findings:
            add("| ID | Nature | Composant | Risque | Impact | Mesures correctives | État |")
            add("|---|---|---|---|---|---|---|")
            for finding in self.security_findings:
                add(
                    f"| `{finding.finding_id}` | {finding.nature} | {finding.component or '—'} | "
                    f"{finding.risk_level} | {finding.impact or '—'} | "
                    f"{finding.corrective_measures or '—'} | {finding.state} |"
                )
        else:
            add("Aucune faille de sécurité identifiée.")
        add("")

        add("## G. Dette technique")
        add("")
        if self.technical_debt:
            add("| ID | Description | Origine | Risque | Priorité | Action recommandée | État |")
            add("|---|---|---|---|---|---|---|")
            for debt in self.technical_debt:
                add(
                    f"| `{debt.debt_id}` | {debt.description} | {debt.origin or '—'} | "
                    f"{debt.risk or '—'} | {debt.priority} | {debt.recommended_action or '—'} | "
                    f"{debt.state} |"
                )
        else:
            add("Aucune dette technique enregistrée.")
        add("")

        add("## H. Tests et validations")
        add("")
        if self.tests:
            add("| Test | Commande | Réussis | Échoués | Résultat |")
            add("|---|---|---|---|---|")
            for test in self.tests:
                add(
                    f"| {test.name} | `{test.command or '—'}` | {test.passed} | {test.failed} | "
                    f"{test.result or '—'} |"
                )
        else:
            add("Aucun test enregistré.")
        add("")
        add("- Tests non exécutés :")
        for item in self.tests_not_run or ["—"]:
            add(f"  - {item}")
        add("- Limites de validation :")
        for item in self.validation_limits or ["—"]:
            add(f"  - {item}")
        add("")

        add("## I. Décisions architecturales")
        add("")
        if self.decisions:
            for decision in self.decisions:
                add(f"### {decision.decision}")
                add("")
                add(f"- Raisons techniques : {decision.rationale or '—'}")
                add("- Alternatives étudiées :")
                for item in decision.alternatives or ["—"]:
                    add(f"  - {item}")
                add(f"- Conséquences : {decision.consequences or '—'}")
                add(f"- ADR : {decision.adr or '—'}")
                add("")
        else:
            add("Aucune décision architecturale enregistrée.")
            add("")

        add("## J. Travaux restants")
        add("")
        add("- Problèmes non résolus :")
        for item in self.remaining_work or ["—"]:
            add(f"  - {item}")
        add("- Actions différées :")
        for item in self.deferred_actions or ["—"]:
            add(f"  - {item}")
        add("- Prochaines étapes recommandées :")
        for item in self.next_steps or ["—"]:
            add(f"  - {item}")
        add("- Risques persistants :")
        for item in self.persistent_risks or ["—"]:
            add(f"  - {item}")
        add("")

        # Le corps Markdown est une surface de persistance : il est assaini
        # comme la charge utile structurée. Un secret glissé dans une
        # description ne doit pas être écrit dans le corpus.
        return redact("\n".join(lines))


def build_intervention_id(agent: str, *, now: Optional[datetime] = None) -> str:
    """Construit un identifiant d'intervention deterministe et lisible.

    Le format reprend celui des evenements d'ingenierie existants :
    ``EVT-<horodatage>-<ORIGINE>``.

    Args:
        agent: Agent ou outil intervenant (normalise en majuscules).
        now: Instant de reference (par defaut, maintenant).

    Returns:
        Identifiant d'intervention.
    """
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%S%f")
    origin = re.sub(r"[^A-Z0-9]+", "-", (agent or "unknown").upper()).strip("-") or "UNKNOWN"
    return f"EVT-{stamp}-{origin}"


# ---------------------------------------------------------------------------
# Construction depuis une charge utile externe
# ---------------------------------------------------------------------------


def _as_str_list(value: Any) -> List[str]:
    """Normalise une valeur en liste de chaines non vides."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _build_corrections(payload: Any) -> List[CorrectionEntry]:
    """Construit la liste des corrections depuis une charge utile JSON."""
    entries: List[CorrectionEntry] = []
    for item in payload or []:
        if isinstance(item, CorrectionEntry):
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(
                CorrectionEntry(
                    problem=str(item.get("problem") or ""),
                    root_cause=str(item.get("root_cause") or ""),
                    solution=str(item.get("solution") or ""),
                    components=_as_str_list(item.get("components")),
                    verification_tests=_as_str_list(item.get("verification_tests")),
                    observed_result=str(item.get("observed_result") or ""),
                )
            )
    return entries


def _build_anomalies(payload: Any) -> List[AnomalyEntry]:
    """Construit la liste des anomalies depuis une charge utile JSON."""
    entries: List[AnomalyEntry] = []
    for item in payload or []:
        if isinstance(item, AnomalyEntry):
            entries.append(item)
        elif isinstance(item, dict):
            raw_state = str(item.get("state") or AnomalyState.OPEN.value).upper()
            try:
                state = AnomalyState(raw_state)
            except ValueError:
                state = AnomalyState.OPEN
            entries.append(
                AnomalyEntry(
                    anomaly_id=str(item.get("anomaly_id") or item.get("id") or ""),
                    description=str(item.get("description") or ""),
                    component=str(item.get("component") or ""),
                    severity=str(item.get("severity") or "MEDIUM"),
                    impact=str(item.get("impact") or ""),
                    cause=str(item.get("cause") or ""),
                    state=state,
                    reference=str(item.get("reference") or ""),
                )
            )
    return entries


def _build_security_findings(payload: Any) -> List[SecurityFindingEntry]:
    """Construit la liste des failles depuis une charge utile JSON."""
    entries: List[SecurityFindingEntry] = []
    for item in payload or []:
        if isinstance(item, SecurityFindingEntry):
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(
                SecurityFindingEntry(
                    finding_id=str(item.get("finding_id") or item.get("id") or ""),
                    nature=str(item.get("nature") or ""),
                    component=str(item.get("component") or ""),
                    risk_level=str(item.get("risk_level") or "MEDIUM"),
                    impact=str(item.get("impact") or ""),
                    corrective_measures=str(item.get("corrective_measures") or ""),
                    state=str(item.get("state") or "OPEN"),
                    security_tests=_as_str_list(item.get("security_tests")),
                )
            )
    return entries


def _build_debts(payload: Any) -> List[TechnicalDebtEntry]:
    """Construit la liste des dettes depuis une charge utile JSON."""
    entries: List[TechnicalDebtEntry] = []
    for item in payload or []:
        if isinstance(item, TechnicalDebtEntry):
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(
                TechnicalDebtEntry(
                    debt_id=str(item.get("debt_id") or item.get("id") or ""),
                    description=str(item.get("description") or ""),
                    origin=str(item.get("origin") or ""),
                    justification=str(item.get("justification") or ""),
                    risk=str(item.get("risk") or ""),
                    priority=str(item.get("priority") or "MEDIUM"),
                    components=_as_str_list(item.get("components")),
                    recommended_action=str(item.get("recommended_action") or ""),
                    dependencies=_as_str_list(item.get("dependencies")),
                    state=str(item.get("state") or "OPEN"),
                )
            )
    return entries


def _build_tests(payload: Any) -> List[TestResultEntry]:
    """Construit la liste des resultats de tests depuis une charge utile JSON."""
    entries: List[TestResultEntry] = []
    for item in payload or []:
        if isinstance(item, TestResultEntry):
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(
                TestResultEntry(
                    name=str(item.get("name") or ""),
                    command=str(item.get("command") or ""),
                    passed=int(item.get("passed") or 0),
                    failed=int(item.get("failed") or 0),
                    result=str(item.get("result") or ""),
                    notes=str(item.get("notes") or ""),
                )
            )
    return entries


def _build_decisions(payload: Any) -> List[DecisionEntry]:
    """Construit la liste des decisions depuis une charge utile JSON."""
    entries: List[DecisionEntry] = []
    for item in payload or []:
        if isinstance(item, DecisionEntry):
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(
                DecisionEntry(
                    decision=str(item.get("decision") or ""),
                    rationale=str(item.get("rationale") or ""),
                    alternatives=_as_str_list(item.get("alternatives")),
                    consequences=str(item.get("consequences") or ""),
                    adr=str(item.get("adr") or ""),
                )
            )
    return entries


def report_from_payload(payload: Dict[str, Any]) -> InterventionReport:
    """Construit un rapport d'intervention depuis une charge utile externe.

    Point d'entree unique des interfaces (API HTTP, CLI, plugin) : la
    coercion des sections imbriquees est faite ici, afin que la logique
    metier reste dans le Core et que chaque interface n'ait pas a
    redefinir le format.

    Args:
        payload: Charge utile JSON du rapport.

    Returns:
        Rapport d'intervention type.

    Raises:
        ValueError: Si l'identifiant d'intervention est absent ou si la
            charge utile n'est pas un objet.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a mapping")
    intervention_id = str(payload.get("intervention_id") or "").strip()
    if not intervention_id:
        raise ValueError("intervention_id is required")

    nature_raw = str(payload.get("nature") or InterventionNature.FEATURE.value).lower()
    try:
        nature = InterventionNature(nature_raw)
    except ValueError:
        nature = InterventionNature.FEATURE

    validation_raw = str(
        payload.get("validation_level") or ValidationLevel.IMPLEMENTED.value
    ).upper()
    try:
        validation_level = ValidationLevel(validation_raw)
    except ValueError:
        validation_level = ValidationLevel.IMPLEMENTED

    project_id = payload.get("project_id")
    return InterventionReport(
        intervention_id=intervention_id,
        created_at=str(payload.get("created_at") or ""),
        project_id=(str(project_id) if project_id else None),
        mission=str(payload.get("mission") or ""),
        phase=str(payload.get("phase") or ""),
        agent=str(payload.get("agent") or ""),
        session_id=str(payload.get("session_id") or ""),
        session_title=str(payload.get("session_title") or ""),
        nature=nature,
        status=str(payload.get("status") or "RECORDED"),
        validation_level=validation_level,
        context=str(payload.get("context") or ""),
        initial_problem=str(payload.get("initial_problem") or ""),
        initial_state=str(payload.get("initial_state") or ""),
        pre_existing_anomalies=_as_str_list(payload.get("pre_existing_anomalies")),
        constraints=_as_str_list(payload.get("constraints")),
        work_description=str(payload.get("work_description") or ""),
        features=_as_str_list(payload.get("features")),
        components=_as_str_list(payload.get("components")),
        files_created=_as_str_list(payload.get("files_created")),
        files_modified=_as_str_list(payload.get("files_modified")),
        files_deleted=_as_str_list(payload.get("files_deleted")),
        schema_or_config_changes=_as_str_list(payload.get("schema_or_config_changes")),
        change_reasons=_as_str_list(payload.get("change_reasons")),
        corrections=_build_corrections(payload.get("corrections")),
        anomalies=_build_anomalies(payload.get("anomalies")),
        security_findings=_build_security_findings(payload.get("security_findings")),
        technical_debt=_build_debts(payload.get("technical_debt")),
        tests=_build_tests(payload.get("tests")),
        tests_not_run=_as_str_list(payload.get("tests_not_run")),
        validation_limits=_as_str_list(payload.get("validation_limits")),
        decisions=_build_decisions(payload.get("decisions")),
        remaining_work=_as_str_list(payload.get("remaining_work")),
        deferred_actions=_as_str_list(payload.get("deferred_actions")),
        next_steps=_as_str_list(payload.get("next_steps")),
        persistent_risks=_as_str_list(payload.get("persistent_risks")),
    )


# ---------------------------------------------------------------------------
# Service de tracabilite
# ---------------------------------------------------------------------------

# Correspondance niveau de validation -> statut d'enregistrement EM.
# Les statuts cibles appartiennent aux ensembles autorises par le registre
# documentaire (`core/engineering_memory/registry.py`) : un statut hors
# ensemble serait refuse a la validation, avant meme l'ecriture.
_VALIDATION_TO_STATUS: Dict[str, str] = {
    ValidationLevel.IMPLEMENTED.value: "IMPLEMENTED",
    ValidationLevel.TESTED.value: "VERIFIED",
    ValidationLevel.RUNTIME_VALIDATED.value: "VERIFIED",
    ValidationLevel.E2E_VALIDATED.value: "VERIFIED",
    ValidationLevel.PARTIAL.value: "IMPLEMENTED",
    ValidationLevel.BLOCKED.value: "FAILED",
    ValidationLevel.NOT_VERIFIED.value: "RECORDED",
}

# Etat d'anomalie -> statut d'evenement d'ingenierie (document immuable).
_ANOMALY_STATE_TO_EVENT_STATUS: Dict[str, str] = {
    AnomalyState.OPEN.value: "RECORDED",
    AnomalyState.INVESTIGATING.value: "RECORDED",
    AnomalyState.FIXED.value: "VERIFIED",
    AnomalyState.DEFERRED.value: "RECORDED",
    AnomalyState.BLOCKED.value: "FAILED",
}

# Rubriques obligatoires d'un rapport d'intervention : leur presence prouve
# que la section a ete traitee, meme si son contenu est vide (aucune
# correction, aucune anomalie). Une section absente signifie « non
# documente », ce qui est different de « documente : vide ».
REQUIRED_SECTIONS: tuple[str, ...] = (
    "intervention_id",
    "created_at",
    "nature",
    "status",
    "validation_level",
    "context",
    "work_description",
    "corrections",
    "anomalies",
    "security_findings",
    "technical_debt",
    "tests",
    "tests_not_run",
    "validation_limits",
    "decisions",
    "remaining_work",
    "deferred_actions",
    "next_steps",
    "persistent_risks",
)

# Natures qui n'attendent aucune modification de fichier : le controle de
# documentation des modifications ne peut pas exiger un fichier pour une
# simple investigation ou un audit.
_NATURES_WITHOUT_FILE_CHANGE: frozenset[str] = frozenset(
    {
        InterventionNature.INVESTIGATION.value,
        InterventionNature.AUDIT.value,
        InterventionNature.DOCUMENTATION.value,
        InterventionNature.TESTING.value,
    }
)


def _default_fallback_dir() -> Path:
    """Répertoire de trace de secours, hors du corpus documentaire.

    Le secours doit survivre à l'indisponibilité du vault : il est donc
    placé **hors** de `daena/`, dans l'espace de configuration de l'agent.

    Returns:
        Chemin du répertoire de secours.
    """
    raw = os.environ.get("ETHAN_TRACEABILITY_FALLBACK_DIR")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".ethan" / "traceability-fallback"


class TraceabilityService:
    """Service Core de tracabilite des interventions d'ingenierie.

    S'appuie sur les services DAENA existants :
    * `EngineeringMemoryService` pour la persistance documentaire (vault) ;
    * `ProjectAnchorService` (P2.8.2) pour le rattachement projet, s'il est
      disponible.

    Aucun nouveau moteur de stockage n'est cree.

    Args:
        engineering_memory: Service Engineering Memory (vault documentaire).
        anchor_service: Service d'ancrage projet, optionnel.
        fallback_dir: Repertoire de trace de secours (hors corpus).
    """

    def __init__(
        self,
        engineering_memory: Any,
        anchor_service: Any | None = None,
        *,
        fallback_dir: Path | None = None,
    ) -> None:
        self._em = engineering_memory
        self._anchors = anchor_service
        self._fallback_dir = Path(fallback_dir) if fallback_dir else _default_fallback_dir()

    # -- Ecriture ------------------------------------------------------

    async def record_intervention(self, report: InterventionReport) -> Dict[str, Any]:
        """Persiste le rapport d'intervention dans DAENA.

        Le document est **immuable** : un identifiant deja utilise avec un
        contenu different n'est jamais ecrase. La divergence est signalee et
        conservee comme evenement correle, pour que l'historique reste
        complet.

        Args:
            report: Rapport a persister.

        Returns:
            Dictionnaire decrivant l'operation effectuee.
        """
        structure = report.to_structure()
        notes = report.render_markdown()

        evidence: List[str] = []
        for test in report.tests:
            if test.command:
                evidence.append(test.command)
        evidence.extend(report.files_modified)
        evidence.extend(report.files_created)

        record = MemoryRecord(
            id=report.intervention_id,
            record_type=RecordType.ENGINEERING_EVENT,
            title=(
                f"{report.nature.value} - "
                f"{report.mission or report.phase or report.intervention_id}"
            ),
            status=_VALIDATION_TO_STATUS.get(report.validation_level.value, "RECORDED"),
            source_of_fact=report.agent or "unknown-agent",
            provenance_level=SourceOfFactLevel.OBSERVED,
            components=list(report.components),
            created_at=report.created_at,
            updated_at=report.created_at,
            evidence_refs=list(dict.fromkeys(evidence)),
            authors=[report.agent] if report.agent else [],
            origin=RecordOrigin.DECLARED,
            confidence=ConfidenceLevel.MEDIUM,
            notes=notes,
            tags=[
                "traceability",
                f"nature:{report.nature.value}",
                f"validation:{report.validation_level.value}",
            ],
            correlation_id=report.project_id,
            task_id=report.mission or None,
            metadata={
                **structure,
                "traceability_schema": "1.0.0",
                "kind": "intervention",
                "anomaly_ids": [a.anomaly_id for a in report.anomalies],
                "security_finding_ids": [f.finding_id for f in report.security_findings],
                "technical_debt_ids": [d.debt_id for d in report.technical_debt],
                "decision_count": len(report.decisions),
            },
        )

        outcome = await self._write(record)
        if outcome.get("conflict"):
            # L'historique est preserve : le conflit devient un evenement correle.
            await self._append_event(
                correlation_id=report.intervention_id,
                title=f"Divergence detectee sur {report.intervention_id}",
                notes=(
                    "Un enregistrement portant le meme identifiant existe avec un "
                    "contenu different. Le document d'origine n'a pas ete ecrase."
                ),
                actor=report.agent,
            )
            return outcome

        if report.project_id and self._anchors is not None:
            outcome["anchored"] = await self._attach(
                record.id,
                report.project_id,
                actor=report.agent or "traceability",
                kind="intervention",
            )
        return outcome

    async def record_anomaly(
        self,
        anomaly_id: str,
        description: str,
        *,
        component: str = "",
        severity: str = "MEDIUM",
        impact: str = "",
        cause: str = "",
        project_id: str | None = None,
        actor: str = "",
        reference: str = "",
    ) -> Dict[str, Any]:
        """Enregistre une anomalie decouverte (document INCIDENT).

        Le document d'anomalie est **immuable** : son etat n'est pas reecrit,
        il evolue par evenements correles (voir `transition_anomaly`).

        Args:
            anomaly_id: Identifiant stable de l'anomalie.
            description: Description de l'anomalie.
            component: Composant concerne.
            severity: Gravite (LOW / MEDIUM / HIGH / CRITICAL).
            impact: Impact potentiel.
            cause: Cause connue ou hypothese.
            project_id: Projet concerne, si connu.
            actor: Auteur de la decouverte.
            reference: Reference vers l'intervention associee.

        Returns:
            Decriptif de l'operation effectuee.
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = MemoryRecord(
            id=anomaly_id,
            record_type=RecordType.INCIDENT,
            title=description[:120],
            status=AnomalyState.OPEN.value,
            source_of_fact=actor or "unknown-agent",
            provenance_level=SourceOfFactLevel.OBSERVED,
            components=[component] if component else [],
            created_at=now,
            updated_at=now,
            evidence_refs=[reference] if reference else [],
            authors=[actor] if actor else [],
            origin=RecordOrigin.DECLARED,
            confidence=ConfidenceLevel.MEDIUM,
            notes=(
                f"## Anomalie {anomaly_id}\n\n"
                f"- Description : {description}\n"
                f"- Composant : {component or '—'}\n"
                f"- Gravite : {severity}\n"
                f"- Impact : {impact or '—'}\n"
                f"- Cause : {cause or 'hypothèse non confirmee'}\n"
                f"- Etat : {AnomalyState.OPEN.value}\n"
                f"- Reference : {reference or '—'}\n"
            ),
            tags=["traceability", "anomaly", f"severity:{severity}"],
            correlation_id=project_id,
            metadata={
                "traceability_schema": "1.0.0",
                "kind": "anomaly",
                "anomaly_id": anomaly_id,
                "description": description,
                "component": component,
                "severity": severity,
                "impact": impact,
                "cause": cause,
                "state": AnomalyState.OPEN.value,
                "reference": reference,
            },
        )
        outcome = await self._write(record)
        if project_id and self._anchors is not None and not outcome.get("conflict"):
            outcome["anchored"] = await self._attach(
                record.id,
                project_id,
                actor=actor or "traceability",
                kind="anomaly",
            )
        return outcome

    async def transition_anomaly(
        self,
        anomaly_id: str,
        state: AnomalyState,
        *,
        note: str = "",
        actor: str = "",
        reference: str = "",
    ) -> Dict[str, Any]:
        """Enregistre un changement d'etat d'anomalie **sans ecraser** le document.

        L'historique est porte par un evenement correle (`correlation_id` pointant
        sur l'anomalie) : le document d'origine reste intact et lisible, et la
        chronologie complete reste reconstituable.

        Args:
            anomaly_id: Identifiant de l'anomalie.
            state: Nouvel etat.
            note: Commentaire de la transition.
            actor: Auteur de la transition.
            reference: Intervention a l'origine de la transition.

        Returns:
            Decriptif de l'evenement enregistre.
        """
        state_value = state.value if isinstance(state, AnomalyState) else str(state)
        event_id = f"{anomaly_id}-ST-{state_value}-{len(self._related_events(anomaly_id)) + 1:03d}"
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = MemoryRecord(
            id=event_id,
            record_type=RecordType.ENGINEERING_EVENT,
            title=f"Transition anomalie {anomaly_id} -> {state_value}",
            status=_ANOMALY_STATE_TO_EVENT_STATUS.get(state_value, "RECORDED"),
            source_of_fact=actor or "unknown-agent",
            provenance_level=SourceOfFactLevel.OBSERVED,
            components=[],
            created_at=now,
            updated_at=now,
            evidence_refs=[reference] if reference else [],
            authors=[actor] if actor else [],
            origin=RecordOrigin.DECLARED,
            confidence=ConfidenceLevel.MEDIUM,
            notes=(
                f"## Transition {anomaly_id}\n\n"
                f"- Nouvel etat : {state_value}\n"
                f"- Note : {note or '—'}\n"
                f"- Auteur : {actor or '—'}\n"
                f"- Intervention : {reference or '—'}\n"
            ),
            tags=["traceability", "anomaly-transition", f"state:{state_value}"],
            correlation_id=anomaly_id,
            task_id=reference or None,
            metadata={
                "traceability_schema": "1.0.0",
                "kind": "anomaly-transition",
                "anomaly_id": anomaly_id,
                "state": state_value,
                "note": note,
                "reference": reference,
            },
        )
        return await self._write(record)

    async def record_debt(
        self,
        debt_id: str,
        description: str,
        *,
        origin: str = "",
        justification: str = "",
        risk: str = "",
        priority: str = "MEDIUM",
        components: Sequence[str] = (),
        recommended_action: str = "",
        dependencies: Sequence[str] = (),
        project_id: str | None = None,
        actor: str = "",
        reference: str = "",
    ) -> Dict[str, Any]:
        """Enregistre une dette technique (document TECHNICAL_DEBT).

        Args:
            debt_id: Identifiant stable de la dette.
            description: Description de la dette.
            origin: Origine de la dette.
            justification: Justification de son maintien.
            risk: Risque associe.
            priority: Priorite.
            components: Composants concernes.
            recommended_action: Action recommandee.
            dependencies: Dependances eventuelles.
            project_id: Projet concerne, si connu.
            actor: Auteur.
            reference: Intervention a l'origine.

        Returns:
            Decriptif de l'operation effectuee.
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = MemoryRecord(
            id=debt_id,
            record_type=RecordType.TECHNICAL_DEBT,
            title=description[:120],
            status="IDENTIFIED",
            source_of_fact=actor or "unknown-agent",
            provenance_level=SourceOfFactLevel.OBSERVED,
            components=list(components),
            created_at=now,
            updated_at=now,
            evidence_refs=[reference] if reference else [],
            authors=[actor] if actor else [],
            origin=RecordOrigin.DECLARED,
            confidence=ConfidenceLevel.MEDIUM,
            notes=(
                f"## Dette technique {debt_id}\n\n"
                f"- Description : {description}\n"
                f"- Origine : {origin or '—'}\n"
                f"- Justification du maintien : {justification or '—'}\n"
                f"- Risque : {risk or '—'}\n"
                f"- Priorite : {priority}\n"
                f"- Composants : {', '.join(components) or '—'}\n"
                f"- Action recommandee : {recommended_action or '—'}\n"
                f"- Dependances : {', '.join(dependencies) or '—'}\n"
                f"- Etat : IDENTIFIED\n"
                f"- Reference : {reference or '—'}\n"
            ),
            tags=["traceability", "technical-debt", f"priority:{priority}"],
            correlation_id=project_id,
            metadata={
                "traceability_schema": "1.0.0",
                "kind": "technical-debt",
                "debt_id": debt_id,
                "description": description,
                "origin": origin,
                "justification": justification,
                "risk": risk,
                "priority": priority,
                "components": list(components),
                "recommended_action": recommended_action,
                "dependencies": list(dependencies),
                "state": "IDENTIFIED",
                "reference": reference,
            },
        )
        outcome = await self._write(record)
        if project_id and self._anchors is not None and not outcome.get("conflict"):
            outcome["anchored"] = await self._attach(
                record.id,
                project_id,
                actor=actor or "traceability",
                kind="technical-debt",
            )
        return outcome

    # -- Controle de fin d'intervention -------------------------------

    def complete(self, intervention_id: str) -> Dict[str, Any]:
        """Verifie qu'une intervention est correctement documentee.

        Controle les huit conditions exigees :
        rapport cree, modifications documentees, corrections recensees,
        anomalies enregistrees, dettes conservees, tests documentes, travaux
        restants identifies, rapport reellement persistant et consultable.

        Le resultat indique explicitement ce qui manque. Un echec n'est jamais
        presente comme une documentation reussie.

        Args:
            intervention_id: Identifiant de l'intervention.

        Returns:
            Rapport de controle.
        """
        checks: List[Dict[str, Any]] = []
        record = None
        try:
            record = self._em.get(intervention_id)
        except Exception as exc:  # pragma: no cover - lecture defensive
            checks.append({"check": "report_readable", "ok": False, "detail": str(exc)})

        if record is None:
            checks.append(
                {
                    "check": "report_exists",
                    "ok": False,
                    "detail": f"aucun enregistrement pour {intervention_id}",
                }
            )
            return {
                "intervention_id": intervention_id,
                "complete": False,
                "persisted": False,
                "checks": checks,
                "missing": ["report_exists"],
                "unresolved_anomalies": [],
            }

        structure = dict(record.metadata or {})
        persisted = False
        repository_path = getattr(record, "repository_path", None)
        if repository_path is not None:
            try:
                persisted = Path(repository_path).is_file()
            except OSError:
                persisted = False
        checks.append(
            {
                "check": "report_persisted",
                "ok": persisted,
                "detail": str(repository_path or ""),
            }
        )

        missing: List[str] = []
        for key in REQUIRED_SECTIONS:
            if key not in structure:
                missing.append(key)
        checks.append(
            {
                "check": "required_sections",
                "ok": not missing,
                "detail": ("sections manquantes : " + ", ".join(missing)) if missing else "complet",
            }
        )

        nature = str(structure.get("nature") or "")
        touched = (
            list(structure.get("files_modified") or [])
            + list(structure.get("files_created") or [])
            + list(structure.get("files_deleted") or [])
        )
        if touched:
            modifications_ok = True
            modifications_detail = f"{len(touched)} fichier(s) documente(s)"
        elif (
            nature in _NATURES_WITHOUT_FILE_CHANGE
            and str(structure.get("work_description") or "").strip()
        ):
            modifications_ok = True
            modifications_detail = "intervention sans modification de fichier attendue"
        else:
            modifications_ok = False
            modifications_detail = "aucune modification documentee"
        checks.append(
            {
                "check": "modifications_documented",
                "ok": modifications_ok,
                "detail": modifications_detail,
            }
        )

        for key, label in (
            ("corrections", "corrections_recensees"),
            ("anomalies", "anomalies_enregistrees"),
            ("technical_debt", "dettes_conservees"),
            ("tests", "tests_documented"),
            ("decisions", "decisions_recensees"),
            ("remaining_work", "travaux_restants_identifies"),
        ):
            listed = structure.get(key)
            if listed is None:
                checks.append({"check": label, "ok": False, "detail": "section absente"})
                continue
            count = len(listed) if isinstance(listed, (list, dict)) else 1
            checks.append({"check": label, "ok": True, "detail": f"{count} element(s)"})

        anomalies = structure.get("anomalies") or []
        unresolved = [
            str(item.get("anomaly_id"))
            for item in anomalies
            if isinstance(item, dict)
            and str(item.get("state", "")).upper()
            in {AnomalyState.OPEN.value, AnomalyState.BLOCKED.value}
        ]

        complete = all(check.get("ok") for check in checks)
        return {
            "intervention_id": intervention_id,
            "complete": complete,
            "persisted": persisted,
            "checks": checks,
            "missing": missing,
            "unresolved_anomalies": unresolved,
            "path": str(repository_path or ""),
        }

    # -- Lecture -------------------------------------------------------

    def list_interventions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Liste les rapports d'intervention enregistres.

        Args:
            limit: Nombre maximum d'elements.

        Returns:
            Liste de dictionnaires decrivant chaque intervention.
        """
        results = self._em.search(record_type=RecordType.ENGINEERING_EVENT.value)
        traced = [
            {
                "id": record.id,
                "title": record.title,
                "status": record.status,
                "created_at": record.created_at,
                "project_id": record.correlation_id,
                "mission": record.task_id,
                "validation_level": (record.metadata or {}).get("validation_level"),
                "agent": (record.metadata or {}).get("agent"),
                "session_id": (record.metadata or {}).get("session_id"),
                "path": str(getattr(record, "repository_path", "") or ""),
            }
            for record in results
            if (record.metadata or {}).get("traceability_schema")
            and (record.metadata or {}).get("kind") == "intervention"
        ]
        traced.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return traced[:limit]

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        """Retourne un enregistrement par identifiant, ou None."""
        return self._em.get(record_id)

    def related_events(self, record_id: str) -> List[MemoryRecord]:
        """Retourne les evenements correles a un enregistrement.

        L'historique d'une anomalie ou d'un rapport est constitue de ces
        evenements : le document d'origine n'est jamais reecrit.

        Args:
            record_id: Identifiant du document de reference.

        Returns:
            Liste des evenements correles, par ordre chronologique.
        """
        return self._related_events(record_id)

    # -- Internes ------------------------------------------------------

    async def _attach(
        self,
        target_id: str,
        project_id: str,
        *,
        actor: str,
        kind: str,
    ) -> bool:
        """Rattache un enregistrement a un projet, sans faire echouer l'ecriture.

        L'echec d'ancrage n'annule pas la documentation : il est signale et
        l'enregistrement reste consultable.

        Args:
            target_id: Identifiant de l'enregistrement.
            project_id: Identifiant du projet.
            actor: Auteur du rattachement.
            kind: Nature du rattache (intervention / anomaly / technical-debt).

        Returns:
            True si le rattachement a abouti.
        """
        if self._anchors is None:
            return False
        try:
            await self._anchors.attach(
                "memory_record",
                target_id,
                project_id,
                actor=actor,
                metadata={"origin": "traceability", "kind": kind},
            )
            return True
        except Exception as exc:
            logger.warning("Ancrage projet impossible pour %s : %s", target_id, exc)
            return False

    async def _write(self, record: MemoryRecord) -> Dict[str, Any]:
        """Ecrit un enregistrement via l'Engineering Memory.

        En cas d'echec de persistance, une **trace de secours** est ecrite
        hors du corpus documentaire : le contenu n'est pas perdu, et l'echec
        est signale explicitement (jamais presente comme une documentation
        reussie).

        Args:
            record: Enregistrement a ecrire.

        Returns:
            Decriptif de l'operation : ecrit, idempotent, en conflit, en
            echec ou en secours.
        """
        try:
            stored = self._em.record(record)
        except Exception as exc:
            if type(exc).__name__ == "DuplicateRecordError":
                return {
                    "status": "conflict",
                    "conflict": True,
                    "persisted": False,
                    "id": record.id,
                    "detail": (
                        "Un enregistrement avec le meme identifiant et un contenu "
                        "different existe. Il n'a pas ete ecrase."
                    ),
                }
            logger.error("Echec d'enregistrement du rapport %s : %s", record.id, exc)
            fallback = self._write_fallback(record, str(exc))
            return {
                "status": "failed",
                "conflict": False,
                "persisted": False,
                "id": record.id,
                "error": str(exc),
                "fallback_path": fallback,
                "detail": (
                    "L'enregistrement dans DAENA a echoue. Une trace de secours a "
                    "ete ecrite ; l'intervention n'est PAS documentee dans DAENA."
                ),
            }
        return {
            "status": "recorded",
            "conflict": False,
            "persisted": True,
            "id": stored.id,
            "path": str(getattr(stored, "repository_path", "") or ""),
        }

    async def _append_event(
        self,
        *,
        correlation_id: str,
        title: str,
        notes: str,
        actor: str = "",
    ) -> Dict[str, Any]:
        """Ajoute un evenement correle sans modifier le document d'origine."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        event_id = f"{correlation_id}-EVT-{now.replace(':', '').replace('-', '')}"
        record = MemoryRecord(
            id=event_id,
            record_type=RecordType.ENGINEERING_EVENT,
            title=title,
            status="RECORDED",
            source_of_fact=actor or "traceability",
            provenance_level=SourceOfFactLevel.OBSERVED,
            components=[],
            created_at=now,
            updated_at=now,
            evidence_refs=[],
            authors=[actor] if actor else [],
            origin=RecordOrigin.DECLARED,
            confidence=ConfidenceLevel.MEDIUM,
            notes=notes,
            tags=["traceability", "event"],
            correlation_id=correlation_id,
            metadata={
                "traceability_schema": "1.0.0",
                "kind": "correlated-event",
            },
        )
        return await self._write(record)

    def _related_events(self, record_id: str) -> List[MemoryRecord]:
        """Liste brute des enregistrements correles a un identifiant."""
        try:
            records = self._em.search()
        except Exception:
            return []
        related = [
            record
            for record in records
            if record.id != record_id
            and (record.correlation_id == record_id or record.task_id == record_id)
            and (record.metadata or {}).get("kind") != "anomaly"
        ]
        related.sort(key=lambda item: item.created_at or "")
        return related

    def _write_fallback(self, record: MemoryRecord, error: str) -> str:
        """Ecrit une trace de secours hors du corpus documentaire.

        La trace reprend le meme format que le document DAENA (frontmatter
        YAML + corps Markdown) afin de pouvoir etre rejouee ulterieurement
        dans le corpus sans traitement particulier.

        Une reprise avec le meme contenu ne cree pas de doublon : la
        signature du contenu est comparee, et le fichier existant est
        conserve. Un contenu different est conserve dans une variante
        numerotee — aucune trace n'est perdue.

        Args:
            record: Enregistrement non persiste.
            error: Message d'erreur de persistance.

        Returns:
            Chemin du fichier de secours ecrit.
        """
        try:
            self._fallback_dir.mkdir(parents=True, exist_ok=True)
            payload = record.to_dict()
            signature = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)

            target = self._fallback_dir / f"{record.id}.md"
            if target.exists():
                existing_signature = self._fallback_signature(target)
                if existing_signature is not None and existing_signature == signature:
                    return str(target)
                index = 2
                while (self._fallback_dir / f"{record.id}-{index}.md").exists():
                    index += 1
                target = self._fallback_dir / f"{record.id}-{index}.md"

            import yaml

            payload["traceability_fallback"] = {
                "error": redact(error),
                "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            frontmatter = yaml.safe_dump(
                payload, sort_keys=False, allow_unicode=True, default_flow_style=False
            )
            if not frontmatter.endswith("\n"):
                frontmatter += "\n"
            content = f"---\n{frontmatter}---\n\n{record.text_body()}"

            target.write_text(content, encoding="utf-8")
            sidecar = target.with_suffix(".json")
            sidecar.write_text(
                json.dumps(
                    {
                        "id": record.id,
                        "record_type": str(record.record_type),
                        "title": record.title,
                        "error": redact(error),
                        "signature": signature,
                        "path": str(target),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return str(target)
        except Exception as exc:  # pragma: no cover - secours best-effort
            logger.error("Trace de secours impossible pour %s : %s", record.id, exc)
            return ""

    @staticmethod
    def _fallback_signature(path: Path) -> str | None:
        """Recalcule la signature de contenu d'une trace de secours.

        Le frontmatter est delimite ligne par ligne : un document contenant
        '---' dans son corps (tableau Markdown) ne doit pas tronquer la
        lecture.

        Args:
            path: Fichier de secours.

        Returns:
            Signature du contenu, ou None si le fichier est illisible.
        """
        import yaml

        try:
            text = path.read_text(encoding="utf-8")
            lines = text.split("\n")
            if not lines or lines[0].strip() != "---":
                return None
            for index in range(1, len(lines)):
                if lines[index].strip() == "---":
                    data = yaml.safe_load("\n".join(lines[1:index]))
                    if not isinstance(data, dict):
                        return None
                    data.pop("traceability_fallback", None)
                    return json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
            return None
        except Exception:
            return None


__all__ = [
    "AnomalyEntry",
    "AnomalyState",
    "CorrectionEntry",
    "DecisionEntry",
    "InterventionNature",
    "InterventionReport",
    "REQUIRED_SECTIONS",
    "SecurityFindingEntry",
    "TechnicalDebtEntry",
    "TestResultEntry",
    "TraceabilityService",
    "ValidationLevel",
    "build_intervention_id",
    "redact",
    "redact_structure",
    "report_from_payload",
]

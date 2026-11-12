"""DAĒNĀ P2.8.3 — Traçabilité des interventions : tests ciblés.

Environnement isolé : corpus DAĒNĀ **répliqué** dans un répertoire
temporaire (même arborescence que `daena/`), store Core en mémoire. Le
corpus réel n'est jamais touché.

La persistance est **réelle** : les documents sont écrits sur disque avec le
mécanisme de l'Engineering Memory (frontmatter YAML + corps Markdown), puis
relus par une nouvelle instance de service — c'est le test de redémarrage.

Couverture :
   1. Création d'un rapport d'intervention
   2. Enregistrement d'une correction
   3. Enregistrement d'une anomalie non résolue
   4. Enregistrement d'une faille de sécurité
   5. Enregistrement d'une dette technique
   6. Enregistrement des résultats de tests
   7. Association à un projet et à une phase
   8. Historique de plusieurs interventions
   9. Absence d'écrasement des rapports précédents
  10. Persistance après redémarrage
  11. Gestion des erreurs de persistance
  12. Reprise sans doublons
  13. Respect des permissions HROT (couche API : interfaces/api/tests)
  14. Absence de fuite de secrets
  15. Non-régression des fonctionnalités DAĒNĀ existantes
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from core.engineering_memory.models import MemoryRecord, RecordOrigin, RecordType
from core.engineering_memory.persistence import ObsidianPersistence
from core.engineering_memory.registry import EngineeringMemoryRegistry
from core.engineering_memory.service import EngineeringMemoryService
from core.engineering_memory.traceability import (
    AnomalyState,
    TraceabilityService,
    ValidationLevel,
    redact,
    redact_structure,
    report_from_payload,
)
from core.projects.anchors import ANCHOR_DOMAIN, ProjectAnchorService
from core.state.record_store import CoreRecordStore

# Arborescence du corpus DAENA : les destinations doivent exister, sinon
# l'Engineering Memory écrit dans un repertoire qui n'a pas sa place dans
# le corpus reel.
DAENA_DIRECTORIES = (
    "Archives/Events",
    "Archives/Rapports-Agents",
    "Knowledge/Composants",
    "Knowledge/Decisions",
    "Knowledge/Incidents",
    "Knowledge/Tests-et-Preuves",
    "Operational-Memory",
    "_meta",
)


def _run(coro):
    """Exécute une coroutine dans une boucle événementielle dédiée."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture()
def corpus(tmp_path: Path) -> Path:
    """Corpus DAENA isolé, reproduisant l'arborescence réelle."""
    root = tmp_path / "daena"
    for directory in DAENA_DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture()
def service(corpus: Path) -> TraceabilityService:
    """Service de traçabilité adossé à un vrai Engineering Memory."""
    em = EngineeringMemoryService(root=corpus)
    return TraceabilityService(em, fallback_dir=corpus.parent / "fallback")


def _payload(**overrides):
    """Charge utile de rapport minimale mais complète.

    L'identifiant est **déterministe** : deux appels produisent le même
    identifiant, ce qui permet de tester le conflit d'identifiant et
    l'idempotence.
    """
    payload = {
        "intervention_id": "EVT-20261112T000000000000-OPENCODE",
        "project_id": "p-alpha",
        "mission": "P2.8.3",
        "phase": "P2.8",
        "agent": "opencode",
        "session_id": "ses_test",
        "nature": "feature",
        "validation_level": "TESTED",
        "context": "Contexte technique de la mission",
        "initial_problem": "Besoin initial",
        "initial_state": "Etat observe avant intervention",
        "constraints": ["Preserver le corpus"],
        "work_description": "Implementation du service de tracabilite",
        "components": ["core.engineering_memory"],
        "files_created": ["core/engineering_memory/traceability.py"],
        "files_modified": ["core/engineering_memory/models.py"],
        "change_reasons": ["Reutiliser les mecanismes existants"],
        "tests": [
            {
                "name": "test_traceability",
                "command": "pytest tests/core/test_traceability.py -q",
                "passed": 12,
                "failed": 0,
                "result": "OK",
            }
        ],
        "remaining_work": ["Documenter l'operation dans DAENA"],
    }
    payload.update(overrides)
    return payload


# ── 1. Création d'un rapport ───────────────────────────────────────────


def test_creation_du_rapport_est_persiste(service: TraceabilityService, corpus: Path):
    """Un rapport cree est ecrit dans le corpus et relisible."""
    report = report_from_payload(_payload())
    outcome = _run(service.record_intervention(report))

    assert outcome["status"] == "recorded"
    assert outcome["persisted"] is True
    assert outcome["conflict"] is False

    target = Path(outcome["path"])
    assert target.is_file()
    assert target.parent == corpus / "Archives" / "Events"
    assert "## A. Identification" in target.read_text(encoding="utf-8")
    assert "## J. Travaux restants" in target.read_text(encoding="utf-8")


def test_le_rapport_contient_les_dix_rubriques(service: TraceabilityService):
    """Les rubriques A a J sont presentes dans le document rendu."""
    report = report_from_payload(_payload())
    markdown = report.render_markdown()
    for section in (
        "## A. Identification",
        "## B. État initial",
        "## C. Travaux réalisés",
        "## D. Corrections effectuées",
        "## E. Observations et anomalies",
        "## F. Sécurité et failles",
        "## G. Dette technique",
        "## H. Tests et validations",
        "## I. Décisions architecturales",
        "## J. Travaux restants",
    ):
        assert section in markdown, section


def test_la_structure_interrogeable_est_conservee(service: TraceabilityService):
    """La charge utile structurée est conservee dans l'enregistrement."""
    report = report_from_payload(_payload())
    outcome = _run(service.record_intervention(report))
    stored = service.get(report.intervention_id)

    assert stored is not None
    assert stored.metadata is not None
    assert stored.metadata["kind"] == "intervention"
    assert stored.metadata["mission"] == "P2.8.3"
    assert stored.metadata["traceability_schema"] == "1.0.0"
    assert outcome["path"]


# ── 2. Corrections ─────────────────────────────────────────────────────


def test_enregistrement_dune_correction(service: TraceabilityService):
    """Une correction est recensee dans le rapport."""
    payload = _payload(
        corrections=[
            {
                "problem": "Le frontmatter etait illisible",
                "root_cause": "Decoupage du frontmatter sur la chaine '---'",
                "solution": "Recherche du delimiteur ligne par ligne",
                "components": ["core/engineering_memory/persistence.py"],
                "verification_tests": ["pytest tests/core/test_engineering_memory.py"],
                "observed_result": "88 tests passants",
            }
        ]
    )
    report = report_from_payload(payload)
    _run(service.record_intervention(report))

    stored = service.get(report.intervention_id)
    assert stored is not None
    corrections = stored.metadata["corrections"]
    assert len(corrections) == 1
    assert corrections[0]["problem"] == "Le frontmatter etait illisible"
    assert corrections[0]["root_cause"]
    assert corrections[0]["observed_result"] == "88 tests passants"


# ── 3. Anomalie non resolue ────────────────────────────────────────────


def test_anomalie_non_resolue_est_enregistree_avec_son_etat(
    service: TraceabilityService, corpus: Path
):
    """Une anomalie non resolue reste OPEN et n'est jamais masquee."""
    outcome = _run(
        service.record_anomaly(
            "INC-2026-001-TEST-OUVERTE",
            "Anomalie non resolue detectee pendant le travail",
            component="core.engineering_memory",
            severity="HIGH",
            impact="Le rapport pourrait etre incomplet",
            cause="hypothese non confirmee",
            project_id="p-alpha",
            actor="opencode",
            reference="EVT-TEST",
        )
    )

    assert outcome["status"] == "recorded"
    assert outcome["persisted"] is True
    document = Path(outcome["path"])
    assert document.parent == corpus / "Knowledge" / "Incidents"
    content = document.read_text(encoding="utf-8")
    assert "Etat : OPEN" in content

    stored = service.get("INC-2026-001-TEST-OUVERTE")
    assert stored is not None
    assert stored.metadata["state"] == AnomalyState.OPEN.value


def test_transition_danomalie_preserve_lhistorique_sans_ecraser(
    service: TraceabilityService, corpus: Path
):
    """Un changement d'etat est un evenement correle : l'original reste intact."""
    _run(service.record_anomaly("INC-2026-001-TEST-HIST", "Anomalie avec historique"))
    outcome = _run(
        service.transition_anomaly(
            "INC-2026-001-TEST-HIST",
            AnomalyState.FIXED,
            note="Corrigee dans l'intervention",
            actor="opencode",
            reference="EVT-TEST",
        )
    )

    assert outcome["status"] == "recorded"
    original = service.get("INC-2026-001-TEST-HIST")
    assert original is not None
    assert original.metadata["state"] == AnomalyState.OPEN.value  # non reecrit

    events = service.related_events("INC-2026-001-TEST-HIST")
    assert len(events) == 1
    assert events[0].metadata["state"] == AnomalyState.FIXED.value
    assert events[0].metadata["note"] == "Corrigee dans l'intervention"

    # Les deux evenements (creation + transition) restent consultables.
    incident_files = list((corpus / "Knowledge" / "Incidents").glob("INC-2026-001-TEST-HIST*.md"))
    event_files = list((corpus / "Archives" / "Events").glob("INC-2026-001-TEST-HIST*.md"))
    assert len(incident_files) == 1
    assert len(event_files) == 1


# ── 4. Faille de securite ─────────────────────────────────────────────


def test_faille_de_securite_est_enregistree_avec_son_risque(
    service: TraceabilityService, corpus: Path
):
    """Une faille est consignee dans la rubrique securite du rapport."""
    payload = _payload(
        security_findings=[
            {
                "finding_id": "SEC-2026-001-TEST",
                "nature": "Secret dans le journal d'audit",
                "component": "core/auth",
                "risk_level": "CRITICAL",
                "impact": "Divulgation d'identifiants",
                "corrective_measures": "Redaction systematique avant persistance",
                "state": "MITIGATED",
                "security_tests": ["pytest tests/core/test_engineering_memory_security.py"],
            }
        ]
    )
    report = report_from_payload(payload)
    _run(service.record_intervention(report))

    stored = service.get(report.intervention_id)
    findings = stored.metadata["security_findings"]
    assert len(findings) == 1
    assert findings[0]["risk_level"] == "CRITICAL"
    assert findings[0]["state"] == "MITIGATED"


# ── 5. Dette technique ─────────────────────────────────────────────────


def test_dette_technique_est_conservee(service: TraceabilityService, corpus: Path):
    """Une dette est conservee comme document dedie, non comme anomalie."""
    outcome = _run(
        service.record_debt(
            "DEBT-2026-001-TEST",
            "Le store partage n'est pas branche sur le registre",
            origin="P2.8.1",
            justification="Migratee en P2.8.6",
            risk="Perte de donnees au redemarrage",
            priority="HIGH",
            components=["core/resources/registry.py"],
            recommended_action="Brancher le ResourceRegistry sur CoreRecordStore",
            dependencies=["P2.8.6"],
            project_id="p-alpha",
            actor="opencode",
            reference="EVT-TEST",
        )
    )

    assert outcome["status"] == "recorded"
    document = Path(outcome["path"])
    assert document.parent == corpus / "Operational-Memory"
    assert "Priorite : HIGH" in document.read_text(encoding="utf-8")

    stored = service.get("DEBT-2026-001-TEST")
    assert stored.record_type == RecordType.TECHNICAL_DEBT
    assert stored.metadata["priority"] == "HIGH"


# ── 6. Resultats de tests ──────────────────────────────────────────────


def test_resultats_de_tests_sont_documentes(service: TraceabilityService):
    """Les resultats de tests figurent dans la rubrique H."""
    report = report_from_payload(_payload())
    _run(service.record_intervention(report))

    stored = service.get(report.intervention_id)
    tests = stored.metadata["tests"]
    assert len(tests) == 1
    assert tests[0]["passed"] == 12
    assert tests[0]["failed"] == 0
    assert tests[0]["command"].startswith("pytest")


def test_le_niveau_de_validation_est_porte_par_le_statut(
    service: TraceabilityService,
):
    """Le niveau de validation determine le statut de l'enregistrement."""
    report = report_from_payload(_payload(validation_level="E2E_VALIDATED"))
    _run(service.record_intervention(report))

    stored = service.get(report.intervention_id)
    assert stored.metadata["validation_level"] == ValidationLevel.E2E_VALIDATED.value
    assert stored.status == "VERIFIED"


# ── 7. Association projet et phase ────────────────────────────────────


def test_association_a_un_projet_et_a_une_phase(corpus: Path):
    """Le rapport est rattache au projet par les Project Anchors (P2.8.2)."""
    store = CoreRecordStore()
    _run(
        store.save(
            "projects",
            "p-alpha",
            {
                "id": "p-alpha",
                "name": "Alpha",
                "description": "",
                "instructions": "",
                "user_id": "tester",
                "metadata": {},
                "is_active": True,
                "created_at": "2026-11-12T00:00:00Z",
                "updated_at": "2026-11-12T00:00:00Z",
            },
        )
    )
    anchors = ProjectAnchorService(store=store)
    em = EngineeringMemoryService(root=corpus)
    service = TraceabilityService(em, anchor_service=anchors)

    report = report_from_payload(_payload(project_id="p-alpha", mission="P2.8.3", phase="P2.8"))
    outcome = _run(service.record_intervention(report))

    assert outcome["status"] == "recorded"
    assert outcome.get("anchored") is True

    stored = service.get(report.intervention_id)
    assert stored.correlation_id == "p-alpha"
    assert stored.task_id == "P2.8.3"

    anchor = _run(store.list(ANCHOR_DOMAIN))
    assert any(item.get("target_id") == report.intervention_id for item in anchor)


def test_une_information_non_rattachee_reste_globale(service: TraceabilityService):
    """Sans projet declare, le rapport reste global : rien n'est deduit."""
    report = report_from_payload(_payload(project_id=None))
    outcome = _run(service.record_intervention(report))

    assert outcome["status"] == "recorded"
    stored = service.get(report.intervention_id)
    assert stored.correlation_id is None
    assert outcome.get("anchored") is None


# ── 8. Historique de plusieurs interventions ───────────────────────────


def test_historique_de_plusieurs_interventions(service: TraceabilityService, corpus: Path):
    """Les interventions successives sont conservees et listees."""
    ids = []
    for index in range(3):
        report = report_from_payload(_payload(mission=f"P2.8.{index}"))
        outcome = _run(service.record_intervention(report))
        assert outcome["status"] == "recorded"
        ids.append(report.intervention_id)

    listed = service.list_interventions()
    assert {item["id"] for item in listed} == set(ids)

    documents = list((corpus / "Archives" / "Events").glob("EVT-*.md"))
    assert len(documents) == 3


# ── 9. Absence d'ecrasement ───────────────────────────────────────────


def test_un_rapport_existant_nest_jamais_ecrase(service: TraceabilityService, corpus: Path):
    """Un identifiant reutilise avec un contenu different ne peut pas ecraser."""
    report = report_from_payload(_payload())
    first = _run(service.record_intervention(report))
    original_text = Path(first["path"]).read_text(encoding="utf-8")

    divergent = report_from_payload(_payload(work_description="Contenu divergent"))
    second = _run(service.record_intervention(divergent))

    assert second["status"] == "conflict"
    assert second["conflict"] is True
    assert second["persisted"] is False

    # Le document d'origine est intact, au caractere pres.
    assert Path(first["path"]).read_text(encoding="utf-8") == original_text

    # La divergence est tracee comme evenement correle : rien n'est perdu.
    events = service.related_events(report.intervention_id)
    assert any("Divergence" in (event.title or "") for event in events)


# ── 10. Persistance apres redemarrage ─────────────────────────────────


def test_persistance_apres_redemarrage(corpus: Path):
    """Une nouvelle instance relit le rapport ecrit par la precedente."""
    em = EngineeringMemoryService(root=corpus)
    first_service = TraceabilityService(em)
    report = report_from_payload(_payload())
    _run(first_service.record_intervention(report))

    # Redemarrage simule : nouveau service, nouveau registre, meme corpus.
    restarted = TraceabilityService(EngineeringMemoryService(root=corpus))

    stored = restarted.get(report.intervention_id)
    assert stored is not None
    assert stored.metadata["mission"] == "P2.8.3"
    assert Path(stored.repository_path).is_file()
    assert restarted.complete(report.intervention_id)["persisted"] is True


def test_le_controle_de_fin_valuationne_les_huit_conditions(service: TraceabilityService):
    """Le controle de fin verifie les huit conditions exigees."""
    report = report_from_payload(_payload())
    _run(service.record_intervention(report))

    result = service.complete(report.intervention_id)
    assert result["complete"] is True
    assert result["persisted"] is True
    checks = {check["check"] for check in result["checks"]}
    assert checks >= {
        "report_persisted",
        "required_sections",
        "modifications_documented",
        "corrections_recensees",
        "anomalies_enregistrees",
        "dettes_conservees",
        "tests_documented",
        "travaux_restants_identifies",
    }


def test_un_rapport_absent_nest_pas_declare_complet(service: TraceabilityService):
    """Un rapport inexistant n'est jamais presente comme documente."""
    result = service.complete("EVT-20261112T000000000000-ABSENT")
    assert result["complete"] is False
    assert result["persisted"] is False
    assert "report_exists" in result["missing"]


# ── 11. Gestion des erreurs de persistance ────────────────────────────


def test_echec_de_persistance_signale_explicitement_et_conserve_une_trace(
    tmp_path: Path,
):
    """Un echec d'ecriture est signale et une trace de secours est conservee."""
    # Une racine invalide (un fichier) rend toute ecriture impossible,
    # independamment des permissions du processus de test.
    broken_root = tmp_path / "racine-invalide"
    broken_root.write_text("ceci n'est pas un repertoire", encoding="utf-8")

    em = EngineeringMemoryService(root=broken_root)
    fallback_dir = tmp_path / "fallback"
    service = TraceabilityService(em, fallback_dir=fallback_dir)

    report = report_from_payload(_payload())
    outcome = _run(service.record_intervention(report))

    assert outcome["status"] == "failed"
    assert outcome["persisted"] is False
    assert outcome["error"]
    assert "PAS documentee" in outcome["detail"]

    fallback = Path(outcome["fallback_path"])
    assert fallback.is_file()
    assert fallback.parent == fallback_dir
    content = fallback.read_text(encoding="utf-8")
    assert report.intervention_id in content
    assert "## A. Identification" in content

    # La trace de secours est rejouable : elle porte le meme frontmatter.
    sidecar = fallback.with_suffix(".json")
    assert sidecar.is_file()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["id"] == report.intervention_id


def test_reprise_sans_doublon_apres_echec(tmp_path: Path):
    """Une reprise avec le meme contenu ne cree pas de second fichier."""
    broken_root = tmp_path / "racine-invalide"
    broken_root.write_text("ceci n'est pas un repertoire", encoding="utf-8")
    fallback_dir = tmp_path / "fallback"

    service = TraceabilityService(
        EngineeringMemoryService(root=broken_root), fallback_dir=fallback_dir
    )
    report = report_from_payload(_payload())

    first = _run(service.record_intervention(report))
    second = _run(service.record_intervention(report))

    assert first["status"] == "failed"
    assert second["status"] == "failed"
    assert first["fallback_path"] == second["fallback_path"]
    assert len(list(fallback_dir.glob("*.md"))) == 1


# ── 12. Reprise sans doublons ─────────────────────────────────────────


def test_reenregistrement_identique_ne_cree_pas_de_doublon(
    service: TraceabilityService, corpus: Path
):
    """Le meme rapport enregistre deux fois reste un seul document."""
    report = report_from_payload(_payload())
    first = _run(service.record_intervention(report))
    second = _run(service.record_intervention(report))

    assert first["status"] == "recorded"
    assert second["status"] == "recorded"
    assert second["conflict"] is False
    assert first["path"] == second["path"]
    assert len(list((corpus / "Archives" / "Events").glob("EVT-*.md"))) == 1


# ── 14. Absence de fuite de secrets ────────────────────────────────────


def test_aucun_secret_nest_persiste(service: TraceabilityService):
    """Un secret present dans le rapport est masque avant persistance."""
    secret = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    payload = _payload(
        work_description=f"Connexion avec le token {secret} pour le deploiement",
        context="Cle de service ethan_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 utilisee",
    )
    report = report_from_payload(payload)
    outcome = _run(service.record_intervention(report))

    assert outcome["status"] == "recorded"
    content = Path(outcome["path"]).read_text(encoding="utf-8")
    assert secret not in content
    assert "ethan_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" not in content
    assert "REDACTE" in content


def test_la_redaction_couvre_les_formes_courantes():
    """Les formes de secret usuelles sont masquees."""
    assert "ghp_" not in redact("token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345")
    assert "sk-ant-" not in redact("cle sk-ant-ABCDEFGHIJKLMNOPQRSTUV")
    assert "BEGIN" not in redact("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")
    assert "hunter2hunter2" not in redact("password=hunter2hunter2")
    assert "mypassword" not in redact("mot de passe : mypassword")
    assert redact_structure({"a": ["ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"]})["a"][0].startswith(
        "[REDACTE"
    )


def test_un_secret_dans_le_contenu_est_refuse_par_la_politique(corpus: Path):
    """La politique EM refuse un enregistrement contenant un secret brut."""
    em = EngineeringMemoryService(root=corpus)
    record = MemoryRecord(
        id="EVT-20261112T000000000000-SECRET",
        record_type=RecordType.ENGINEERING_EVENT,
        title="ESSAI",
        status="RECORDED",
        source_of_fact="tester",
        provenance_level="observed",
        components=[],
        created_at="2026-11-12T00:00:00Z",
        updated_at="2026-11-12T00:00:00Z",
        evidence_refs=[],
        authors=["tester"],
        origin=RecordOrigin.DECLARED,
        confidence="medium",
        notes="api_key=AKIAIOSFODNN7EXAMPLE",
        tags=[],
    )
    with pytest.raises(Exception):
        em.record(record)


# ── 15. Non-regression DAENA ───────────────────────────────────────────


def test_non_regression_des_enregistrements_standards(corpus: Path):
    """Les usages precedents de l'Engineering Memory restent valides."""
    em = EngineeringMemoryService(root=corpus)
    record = MemoryRecord(
        id="EVT-20261112T000000000000-LEGACY",
        record_type=RecordType.ENGINEERING_EVENT,
        title="Evenement classique",
        status="RECORDED",
        source_of_fact="tester",
        provenance_level="observed",
        components=["core.api"],
        created_at="2026-11-12T00:00:00Z",
        updated_at="2026-11-12T00:00:00Z",
        evidence_refs=[],
        authors=["tester"],
        origin=RecordOrigin.DECLARED,
        confidence="high",
        notes="note classique",
        tags=["backend.started"],
    )
    stored = em.record(record)
    assert stored.id == record.id

    assert em.get("EVT-20261112T000000000000-LEGACY") is not None
    assert em.search(record_type="engineering_event")
    assert em.component_history("core.api")

    # La destination canonique n'a pas change.
    destination = em.destination_status(RecordType.ENGINEERING_EVENT)
    assert destination["relative_directory"] == "Archives/Events"


def test_non_regression_du_routage_documentaire():
    """Le registre documentaire conserve ses destinations."""
    registry = EngineeringMemoryRegistry()
    assert registry.relative_path_for(
        RecordType.ENGINEERING_EVENT, "EVT-1", "Titre"
    ) == Path("Archives/Events/EVT-1-titre.md")
    assert registry.relative_path_for(
        RecordType.INCIDENT, "INC-1", "Titre"
    ) == Path("Knowledge/Incidents/INC-1-titre.md")
    assert registry.relative_path_for(
        RecordType.TECHNICAL_DEBT, "DEBT-1", "Titre"
    ) == Path("Operational-Memory/DEBT-1-titre.md")


def test_non_regression_de_la_detection_de_doublon(corpus: Path):
    """Le mecanisme de doublon de l'Engineering Memory reste actif."""
    persistence = ObsidianPersistence(corpus, EngineeringMemoryRegistry())

    def _record(notes: str) -> MemoryRecord:
        return MemoryRecord(
            id="EVT-20261112T000000000000-DUP",
            record_type=RecordType.ENGINEERING_EVENT,
            title="Doublon",
            status="RECORDED",
            source_of_fact="tester",
            provenance_level="observed",
            components=[],
            created_at="2026-11-12T00:00:00Z",
            updated_at="2026-11-12T00:00:00Z",
            evidence_refs=[],
            authors=["tester"],
            origin=RecordOrigin.DECLARED,
            confidence="medium",
            notes=notes,
            tags=[],
        )

    persistence.write(_record("contenu A"))
    with pytest.raises(Exception):
        persistence.write(_record("contenu B"))


def test_non_regression_de_la_lecture_des_documents_a_tableau(corpus: Path):
    """Un document dont le corps contient '---' reste relisible."""
    em = EngineeringMemoryService(root=corpus)
    record = MemoryRecord(
        id="EVT-20261112T000000000000-TABLEAU",
        record_type=RecordType.ENGINEERING_EVENT,
        title="Rapport avec tableau",
        status="RECORDED",
        source_of_fact="tester",
        provenance_level="observed",
        components=[],
        created_at="2026-11-12T00:00:00Z",
        updated_at="2026-11-12T00:00:00Z",
        evidence_refs=[],
        authors=["tester"],
        origin=RecordOrigin.DECLARED,
        confidence="medium",
        notes="| ID | Valeur |\n|---|---|\n| A | B |",
        tags=[],
    )
    em.record(record)
    reloaded = em.get("EVT-20261112T000000000000-TABLEAU")
    assert reloaded is not None
    assert "|--" in reloaded.notes


def test_non_regression_du_vault(corpus: Path):
    """Le vault reste explorable et la recherche fonctionne."""
    from core.engineering_memory.vault import VaultService

    vault = VaultService(root=corpus)
    tree = vault.tree()
    assert tree
    hits = vault.search("Archives")
    assert isinstance(hits, list)

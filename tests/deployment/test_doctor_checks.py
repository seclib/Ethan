"""Tests des invariants de ``scripts/cmd-doctor.sh`` (plan Boot, phase 3).

Régression couverte : après le rebuild (``core/`` + ``sdk/`` + ``plugins/``),
plusieurs checks du doctor pointaient encore vers le monde pré-rebuild —
modules ``core.providers.*`` / ``core.registry`` disparus, dossier ``runtime/``
inexistant — ou s'arrêtaient à un test partiel (``redis-cli`` absent du host).
Résultat sur un système sain : « 66 PASS, 6 WARNING » de faux positifs.

Contrat vérifié ici :
1. chaque import Python référencé par le script est résolvable ;
2. aucun check ne référence les chemins obsolètes du pré-rebuild ;
3. le check ``runtime`` est neutralisé quand ``runtime/`` est absent ;
4. le check ``PYTHONPATH`` dépend d'un import réellement en échec ;
5. (live, skippé sans stack) ``./ethan doctor`` sur un système sain affiche
   ``0 FAIL`` et aucun des faux positifs corrigés.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "cmd-doctor.sh"
STATUS_SCRIPT = ROOT / "scripts" / "cmd-status.sh"

# Imports Python embarqués dans les heredocs (`python3 -c "..."`).
_IMPORT_RE = re.compile(
    r"^\s*from\s+([A-Za-z_][\w.]*)\s+import|^\s*import\s+([A-Za-z_][\w.]*)",
    re.MULTILINE,
)

# Faux positifs corrigés : chacun correspondait à un check défaillant
# (module disparu, dossier inexistant, test partiel) sur un système sain.
_FAUX_POSITIFS_HISTORIQUES = (
    "PYTHONPATH non défini (peut empêcher les imports)",
    "NODE_ENV non défini (défaut: development)",
    "Import runtime échoué (optionnel)",
    "Redis : port ouvert mais redis-cli non installé (test limité)",
    "Core : impossible de vérifier les providers",
    "Core : impossible de vérifier le registre de plugins",
)


def _imports_python_du_script() -> set[str]:
    """Modules du projet importés par les fragments Python du doctor."""
    modules: set[str] = set()
    for match in _IMPORT_RE.finditer(SCRIPT.read_text(encoding="utf-8")):
        module = match.group(1) or match.group(2)
        if module.split(".")[0] in {"core", "sdk", "plugins"}:
            modules.add(module)
    return modules


class TestImportsDuDoctor:
    """Chaque module référencé par le script doit exister réellement."""

    def test_imports_du_projet_resolvables(self):
        modules = sorted(_imports_python_du_script())
        assert modules, "aucun import projet détecté — la regex est cassée ?"
        for module in modules:
            try:
                importlib.import_module(module)
            except ImportError as exc:  # pragma: no cover - échec = régression
                pytest.fail(
                    f"cmd-doctor.sh référence {module!r}, non importable : {exc}"
                )

    def test_aucun_import_pre_rebuild(self):
        content = SCRIPT.read_text(encoding="utf-8")
        for pattern in (
            "from core.providers",
            "from core.registry",
            "import core.providers",
            "import core.registry",
        ):
            assert pattern not in content, (
                f"« {pattern} » n'existe plus depuis le rebuild — "
                "le doctor doit cibler core.llm.* / core.plugins.*"
            )


class TestChecksCorriges:
    """Les gardes qui empêchent le retour des faux positifs."""

    def test_check_runtime_neutralise_sans_dossier(self):
        if (ROOT / "runtime").is_dir():
            pytest.skip("runtime/ présent : le check actif est légitime")
        content = SCRIPT.read_text(encoding="utf-8")
        assert '[ ! -d "${ETHAN_ROOT}/runtime" ]' in content, (
            "sans dossier runtime/, le check doit être neutralisé "
            "(le fix `pip install -e runtime` serait inapplicable)"
        )

    def test_check_pythonpath_verifie_l_effet_reel(self):
        content = SCRIPT.read_text(encoding="utf-8")
        assert "import core, sdk, plugins" in content, (
            "le warning PYTHONPATH doit dépendre d'un import réellement en échec"
        )

    def test_redis_fallback_conteneur_present(self):
        # Uniformisé entre `ethan doctor` et `ethan status` : redis-cli absent
        # du host → test réel via le conteneur au lieu d'un test de port.
        for script in (SCRIPT, STATUS_SCRIPT):
            content = script.read_text(encoding="utf-8")
            assert "docker exec ethan-redis redis-cli" in content, (
                f"{script.name} doit tester Redis via le conteneur "
                "quand redis-cli est absent du host"
            )


# ── Intégration : vraie stack (ignoré si non démarrée) ────────────────────


def _docker_stack_ready() -> bool:
    """True si le conteneur Compose ``nats`` tourne (stack ETHAN démarrée)."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "nats", "--format", "json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return '"State":"running"' in result.stdout


requires_docker_stack = pytest.mark.skipif(
    not _docker_stack_ready(),
    reason="Stack Docker ETHAN non démarrée (docker compose ps nats vide)",
)


class TestLiveStack:
    """Le vrai doctor face à la vraie stack : plus aucun faux positif."""

    @requires_docker_stack
    def test_doctor_sans_faux_positif_sur_systeme_sain(self):
        env = os.environ.copy()
        # Force l'interpréteur du venv projet : c'est lui qui rend les
        # imports core/sdk/plugins résolvables (comme en usage réel).
        env["PATH"] = f"{ROOT / '.venv' / 'bin'}:{env['PATH']}"
        result = subprocess.run(
            [str(ROOT / "ethan"), "doctor"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0, output
        # Résumé 0 FAIL : « Tout est opérationnel » (0 warning) ou
        # « Aucun échec critique » (warnings tolérés) — jamais « Problèmes ».
        assert "Problèmes détectés" not in output, output
        assert "Tout est opérationnel" in output or "Aucun échec critique" in output, (
            output
        )
        for faux_positif in _FAUX_POSITIFS_HISTORIQUES:
            assert faux_positif not in output, (
                f"faux positif réapparu dans `ethan doctor` : {faux_positif}"
            )

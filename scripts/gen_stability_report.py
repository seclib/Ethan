"""Generate STABILITY_PLAN.md automatically — stability report for ETHAN CLI.

Usage:
    python3 scripts/gen_stability_report.py              # Print to stdout
    python3 scripts/gen_stability_report.py --write      # Overwrite STABILITY_PLAN.md
    python3 scripts/gen_stability_report.py --json       # Output JSON

The script:
  1. Scans all CLI source files for known stability patterns
  2. Checks for concurrency safety (locks, threading)
  3. Checks for daemon resilience (fork, PID lock, watchdog)
  4. Checks for error handling (bare except, silent failures)
  5. Compiles a report with score.
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_CORE = REPO_ROOT / "cli" / "core"
CLI_COMMANDS = REPO_ROOT / "cli" / "commands"
CLI_REGISTRY = REPO_ROOT / "cli" / "registry.py"


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def count_pattern(filepath: Path, pattern: str) -> int:
    """Count regex pattern matches in a file."""
    if not filepath.exists():
        return 0
    try:
        text = filepath.read_text()
        return len(re.findall(pattern, text))
    except Exception:
        return 0


def file_contains(filepath: Path, pattern: str) -> bool:
    """Check if file contains a regex pattern."""
    return count_pattern(filepath, pattern) > 0


class StabilityScanner:
    """Scan project files for stability patterns."""

    def __init__(self):
        self.risks_fixed: list[dict] = []
        self.risks_remaining: list[dict] = []
        self.scores: dict[str, tuple[int, int]] = {}

        self._scan_concurrency()
        self._scan_daemon()
        self._scan_error_handling()
        self._scan_registry()
        self._scan_tests()

    def _scan_concurrency(self):
        """Check concurrency safety in streaming.py and loading.py."""
        score = 100
        total = 0

        # streaming.py: should have threading.Lock and threading.Event
        st = CLI_CORE / "streaming.py"
        if st.exists():
            total += 4
            if file_contains(st, r"threading\.Lock"):
                score += 25
            if file_contains(st, r"threading\.Event"):
                score += 25
            if file_contains(st, r"try:"):
                score += 25
            if not file_contains(st, r"os\.fork"):
                score += 25

        # loading.py: should have threading.Event
        ld = CLI_CORE / "loading.py"
        if ld.exists():
            total += 3
            if file_contains(ld, r"threading\.Event"):
                score += 33
            if file_contains(ld, r"try:"):
                score += 33
            if file_contains(ld, r"is_alive"):
                score += 34

        self.scores["concurrency"] = (score // max(total, 1), 100)

        if score < 80:
            self.risks_remaining.append({
                "file": "cli/core/streaming.py",
                "risk": "Concurrency insuffisante",
                "priority": "HIGH",
            })
        else:
            self.risks_fixed.append({
                "file": "cli/core/streaming.py + loading.py",
                "risk": "Race conditions threads",
                "fix": "threading.Lock + threading.Event + try/except",
            })

    def _scan_daemon(self):
        """Check daemon resilience."""
        score = 0
        total = 5

        dm = CLI_CORE / "daemon.py"
        dl = CLI_CORE / "daemon_loop.py"

        if dm.exists():
            # No os.fork()
            if not file_contains(dm, r"os\.fork"):
                score += 15
            # Uses subprocess.Popen
            if file_contains(dm, r"subprocess\.Popen"):
                score += 15
            # Has flock
            if file_contains(dm, r"fcntl\.flock"):
                score += 15
            # Has heartbeat
            if file_contains(dm, r"heartbeat"):
                score += 15
            # Has cache size limit
            if file_contains(dm, r"MAX_CACHE_SIZE") or file_contains(dm, r"max_cache"):
                score += 15
            # Has graceful stop (SIGTERM wait)
            if file_contains(dm, r"SIGTERM"):
                score += 15
            # Has health check
            if file_contains(dm, r"_daemon_is_healthy"):
                score += 10

        self.scores["daemon"] = (score, 100)

        risks = []
        if not file_contains(dm, r"fcntl\.flock"):
            risks.append("PID lock manquant")
        if not file_contains(dm, r"heartbeat"):
            risks.append("Pas de heartbeat")

        if risks:
            self.risks_remaining.append({
                "file": "cli/core/daemon.py",
                "risk": ", ".join(risks),
                "priority": "HIGH",
            })
        else:
            self.risks_fixed.append({
                "file": "cli/core/daemon.py",
                "risk": "os.fork(), PID race, cache non borné",
                "fix": "subprocess.Popen, fcntl.flock, heartbeat, cache limit",
            })

    def _scan_error_handling(self):
        """Check error handling in registry.py."""
        score = 0
        total = 3

        if CLI_REGISTRY.exists():
            text = CLI_REGISTRY.read_text()
            # Has SIGALRM timeout
            if "SIGALRM" in text:
                score += 40
            # Has structured error messages
            if "EthanError" in text:
                score += 30
            # Silent except: return (bad)
            if "except Exception:" in text and "return" in text.split("except Exception:")[1].split("\n")[0]:
                score -= 20
                self.risks_remaining.append({
                    "file": "cli/registry.py",
                    "risk": "except Exception: return silencieux ligne 38",
                    "priority": "MEDIUM",
                })

        self.scores["error_handling"] = (max(score, 0), 100)

    def _scan_registry(self):
        """Check for dual registry problem."""
        score = 50  # default: half score
        total = 1

        # Check if discovery.py has its own registry
        disc = CLI_CORE / "discovery.py"
        if disc.exists():
            disc_text = disc.read_text()
            reg_text = CLI_REGISTRY.read_text() if CLI_REGISTRY.exists() else ""

            # If both have register() or COMMANDS = {}
            if "class CommandRegistry" in disc_text and "COMMANDS = {}" in reg_text:
                self.risks_remaining.append({
                    "file": "cli/registry.py + cli/core/discovery.py",
                    "risk": "Deux registres de commandes (COMMANDS + CommandRegistry)",
                    "priority": "CRITICAL",
                })
                score = 20
            else:
                score = 90

        self.scores["registry"] = (score, 100)

    def _scan_tests(self):
        """Check test coverage for stability modules."""
        score = 0
        total = 5
        test_dir = REPO_ROOT / "tests"

        stability_tests = [
            "test_streaming.py",
            "test_loading.py",
            "test_daemon.py",
            "test_registry_timeout.py",
            "test_telemetry.py",
        ]

        for t in stability_tests:
            if (test_dir / t).exists():
                score += 20

        if score < 60:
            missing = [t for t in stability_tests if not (test_dir / t).exists()]
            self.risks_remaining.append({
                "file": "tests/",
                "risk": f"Tests unitaires manquants : {', '.join(missing)}",
                "priority": "HIGH",
            })

        self.scores["tests"] = (score, 100)

    def overall_score(self) -> int:
        """Calculate weighted overall score."""
        weights = {
            "concurrency": 25,
            "daemon": 25,
            "error_handling": 20,
            "registry": 20,
            "tests": 10,
        }
        total = 0
        weight_sum = 0
        for key, weight in weights.items():
            if key in self.scores:
                val, max_val = self.scores[key]
                total += (val / max_val) * weight
                weight_sum += weight
        return int((total / weight_sum) * 100) if weight_sum > 0 else 0


def generate_report(commit: str) -> str:
    """Generate the STABILITY_PLAN.md content."""
    scanner = StabilityScanner()
    score = scanner.overall_score()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    n_fixed = len(scanner.risks_fixed)
    n_remaining = len(scanner.risks_remaining)

    lines = [
        f"# ETHAN CLI — Stability Plan",
        f"",
        f"> Généré le {now}",
        f">",
        f"> Commit : `{commit}`",
        f">",
        f"> Score production : **{score}/100**",
        f"",
        f"## Résumé",
        f"",
        f"Analyse de stabilité et plan d'amélioration pour le CLI ETHAN.",
        f"",
        f"**Risques corrigés : {n_fixed}**",
        f"**Risques restants : {n_remaining}**",
        f"",
        f"---",
        f"",
        f"## 1. Risques identifiés et corrigés",
        f"",
        f"### 🔴 Corrigés (Critiques)",
        f"",
        f"| # | Fichier | Risque | Fix |",
        f"|---|---------|--------|-----|",
    ]

    for i, r in enumerate(scanner.risks_fixed, 1):
        lines.append(f"| {i} | `{r['file']}` | {r['risk']} | {r['fix']} |")

    lines.extend([
        f"",
        f"### 🟠 Restants (Non corrigés)",
        f"",
        f"| # | Fichier | Risque | Priorité |",
        f"|---|---------|--------|----------|",
    ])

    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for i, r in enumerate(
        sorted(scanner.risks_remaining, key=lambda x: priority_order.get(x.get("priority", "LOW"), 3)), 1
    ):
        p_icon = {"CRITICAL": "🔴", "HIGH": "🟡", "MEDIUM": "🟠", "LOW": "🟢"}.get(r.get("priority", "LOW"), "⚪")
        lines.append(f"| {i} | `{r['file']}` | {r['risk']} | {p_icon} {r['priority']} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 2. Scores par catégorie",
        f"",
        f"| Catégorie | Score |",
        f"|-----------|:-----:|",
    ])

    for key, label in [
        ("concurrency", "Concurrency safety"),
        ("daemon", "Daemon resilience"),
        ("error_handling", "Error handling"),
        ("registry", "Registry integrity"),
        ("tests", "Test coverage"),
    ]:
        val, max_val = scanner.scores.get(key, (0, 100))
        score_str = f"{val}/{max_val}" if max_val > 0 else "N/A"
        lines.append(f"| {label} | {score_str} |")

    lines.extend([
        f"",
        f"**Score global : {score}/100**",
        f"",
        f"---",
        f"",
        f"## 3. Statistiques",
        f"",
    ])

    # Count files
    cli_files = list(CLI_CORE.glob("*.py")) + list(CLI_COMMANDS.glob("*.py"))
    lines.append(f"- Fichiers CLI analysés : {len(cli_files)}")
    lines.append(f"- Fichiers core : {len(list(CLI_CORE.glob('*.py')))}")
    lines.append(f"- Fichiers commandes : {len(list(CLI_COMMANDS.glob('*.py')))}")

    lines.append("")
    return "\n".join(lines)


def main():
    commit = git_commit()
    report = generate_report(commit)

    args = set(sys.argv[1:])

    if "--json" in args:
        # Also compute scanner for JSON
        scanner = StabilityScanner()
        data = {
            "timestamp": datetime.now().isoformat(),
            "commit": commit,
            "score": scanner.overall_score(),
            "risks_fixed": scanner.risks_fixed,
            "risks_remaining": scanner.risks_remaining,
            "scores": {k: {"val": v, "max": m} for k, (v, m) in scanner.scores.items()},
        }
        print(json.dumps(data, indent=2))
        return

    if "--write" in args:
        output_path = REPO_ROOT / "STABILITY_PLAN.md"
        output_path.write_text(report)
        print(f"✅ Rapport écrit dans {output_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Architecture Lint — Ethan OS

Vérifie le respect de la Constitution Architecturale.
Usage: python scripts/arch-lint.py [path] [--check RULE1,RULE2]
"""

import argparse
import re
import sys
from pathlib import Path

RULES = {
    "C001": {
        "name": "Core ne dépend pas de technologies externes",
        "pattern": r"import (redis|asyncpg|qdrant_client|httpx|aiohttp|requests|sqlalchemy|docker|kubernetes)",
        "paths": ["core/"],
        "exclude": ["core/memory/", "core/providers/"],
    },
    "C006": {
        "name": "Providers IA sont interchangeables",
        "pattern": r"(ollama|openai|anthropic)",
        "paths": ["core/"],
        "exclude": [],
    },
    "C007": {
        "name": "Memory via MemoryManager uniquement",
        "pattern": r"import (redis|asyncpg|qdrant_client)",
        "paths": ["core/"],
        "exclude": ["core/memory/"],
    },
}


def check_rule(rule_id: str, rule: dict, base_path: Path) -> list:
    violations = []
    for path_str in rule["paths"]:
        search_path = base_path / path_str
        if not search_path.exists():
            continue
        for py_file in search_path.rglob("*.py"):
            # Skip excluded paths
            if any(str(py_file).startswith(str(base_path / ex)) for ex in rule["exclude"]):
                continue
            try:
                content = py_file.read_text()
                matches = re.findall(rule["pattern"], content, re.IGNORECASE)
                if matches:
                    violations.append((py_file, matches))
            except Exception:
                pass
    return violations


def main():
    parser = argparse.ArgumentParser(description="Architecture Lint for Ethan OS")
    parser.add_argument("path", nargs="?", default=".", help="Path to check")
    parser.add_argument("--check", help="Comma-separated rule IDs")
    args = parser.parse_args()

    base_path = Path(args.path)
    rules_to_check = RULES

    if args.check:
        selected = args.check.split(",")
        rules_to_check = {k: v for k, v in RULES.items() if k in selected}

    failed = False
    for rule_id, rule in rules_to_check.items():
        violations = check_rule(rule_id, rule, base_path)
        if violations:
            failed = True
            print(f"[FAIL] {rule_id}: {rule['name']}")
            for file, matches in violations:
                print(f"  {file}: {matches}")
        else:
            print(f"[PASS] {rule_id}: {rule['name']}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
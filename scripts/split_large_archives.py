#!/usr/bin/env python3
"""Découpage des fichiers Markdown volumineux par frontière de message."""

import re
import shutil
from pathlib import Path

MAX_SIZE_MB = 5
MAX_SIZE = MAX_SIZE_MB * 1024 * 1024

ODSIDIAN_ROOT = Path.home() / "AI" / "Ethan" / "Odsidian"


def split_large_file(file_path: Path) -> list[Path]:
    """Découpe un fichier Markdown volumineux par frontière de message."""
    size = file_path.stat().st_size
    if size < MAX_SIZE:
        return [file_path]

    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Extraire le frontmatter
    frontmatter = ""
    body_start = 0
    if lines and lines[0] == "---":
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i] == "---":
                end_idx = i
                break
        if end_idx is not None:
            frontmatter = "\n".join(lines[:end_idx + 1]) + "\n"
            body_start = end_idx + 1

    body = "\n".join(lines[body_start:])

    # Découper par "### Tour" (frontière de message)
    # Pattern: ### Tour N — Role
    parts = re.split(r"(?=^### Tour \d+)", body, flags=re.MULTILINE)

    if len(parts) <= 1:
        # Pas de frontière de tour trouvée, ne pas découper
        return [file_path]

    # Grouper les parties pour ne pas créer trop de petits fichiers
    # Viser ~2 MB par fichier
    target_size = 2 * 1024 * 1024
    groups = []
    current_group = []
    current_size = 0

    for part in parts:
        part_size = len(part.encode("utf-8"))
        if current_size + part_size > target_size and current_group:
            groups.append(current_group)
            current_group = [part]
            current_size = part_size
        else:
            current_group.append(part)
            current_size += part_size

    if current_group:
        groups.append(current_group)

    if len(groups) <= 1:
        return [file_path]

    # Créer les fichiers de sortie
    stem = file_path.stem
    parent = file_path.parent
    output_files = []

    # Sauvegarder l'original
    backup_path = file_path.with_suffix(".md.bak")
    shutil.copy2(file_path, backup_path)

    for i, group in enumerate(groups, 1):
        part_content = frontmatter + "\n".join(group)
        # Ajouter une référence à la partie
        part_content = part_content.replace(
            "---\n",
            f"---\npart: {i}/{len(groups)}\noriginal: {file_path.name}\n",
            1,
        )

        part_path = parent / f"{stem}-part-{i:02d}.md"
        part_path.write_text(part_content, encoding="utf-8")
        output_files.append(part_path)

    # Supprimer l'original (remplacé par les parties)
    file_path.unlink()

    return output_files


def main():
    # Trouver les fichiers > MAX_SIZE
    large_files = []
    for md_file in ODSIDIAN_ROOT.rglob("*.md"):
        if md_file.stat().st_size > MAX_SIZE:
            large_files.append(md_file)

    print(f"Fichiers volumineux trouvés : {len(large_files)}")

    for f in sorted(large_files, key=lambda x: -x.stat().st_size):
        print(f"  {f.relative_to(ODSIDIAN_ROOT)} ({f.stat().st_size / 1024 / 1024:.1f} MB)")
        parts = split_large_file(f)
        if len(parts) > 1:
            print(f"    → Découpé en {len(parts)} parties")
        else:
            print(f"    → Non découpé (pas de frontière trouvée)")


if __name__ == "__main__":
    main()

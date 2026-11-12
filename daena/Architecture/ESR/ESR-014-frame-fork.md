# ESR-014 — Préparation du fork Frame

- Objectif : documenter la création locale du fork Frame sans implementation.
- Priorité : moyenne
- Fichiers et références :
  - Frame : `examples/frame`
  - Upstream : `https://github.com/heygen-com/hyperframes`
  - Commit : `8b1f88b3c`
  - Documentation fork : `examples/frame/docs/FRAME_FORK.md`
  - Pattern de confinement : `core/plugins/odin.py`, `examples/odin/compose.yaml`
- Remotes Frame :
  - `origin` et `upstream` pointent temporairement vers l'upstream officiel en fetch
  - push désactivé volontairement
- Vérification :
  - `git status --short` = clean
  - `git fsck --full` sans erreur
  - commit `8b1f88b3c`
- Limites :
  - Bun non installé dans cet environnement
  - tests HyperFrames dépendant de FFmpeg/Chromium non exécutés

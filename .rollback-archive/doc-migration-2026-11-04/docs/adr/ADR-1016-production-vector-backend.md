# ADR-1016 — Configuration vectorielle production

- Statut : Proposed
- Contexte : memory par défaut, backends externes optionnels.
- Décision : prod doit explicitement choisir `vector_backend` et config réversible.
- Risques : ops, persistance externe, réseau.
- Tests : smoke / config tests futurs.

## Optional Capability Correction
- No external backend required by default.
- Memory vector backend is native and remains available.
- Optional services must remain separately managed and explicitly opt-in.
- Capability states apply: Supported, Not installed, Installed/Stopped, Running, Ready, Error.

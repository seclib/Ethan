# 05 — Menus and Installation Diagnostic

## Plugins (confirmé)

- Routes backend présentes.
- `PluginRegistry` est l’implémentation réelle.
- Installation par id ou custom.
- Permissions `Permission.PLUGINS`.
- Gateway guard `ActionType.PLUGIN_INSTALL` sur `/plugins/install`.
- Certaines routes (`enable`, etc.) n’ont pas toutes de gateway_guard visible dans l’extrait inspecté.

## Capabilities / Tools (observé)

- Router capabilities très dense.
- Tools représentés sous `/tools`, `/tools/pipelines`, `/tools/servers`.
- Serveurs outils exige `Permission.ADMIN` pour création.
- Possibilité d’états frontend non synchronisés avec states réels.

## Knowledge (partiel)

- Routes présentes.
- Implémentation détaillée non audité ici par durée.

## Skills (observé)

- Routes présentes, installation lab, permission EXECUTE.
- Import/sync skills présent.

## Causes probables d’échec plugin/capacity

1. permission `PLUGINS` manquante côté utilisateur/rôle.
2. registry non initialisé (`503` possible).
3. contract mismatch await frontend/backend.
4. HROT denial via gateway guard.
5. multiples systèmes d’état (`application registry` vs composants vs docker).

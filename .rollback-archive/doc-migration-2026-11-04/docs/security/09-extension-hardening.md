# 09 — Durcissement des extensions (skills, plugins, outils)

> Statut : **implémenté** — les quatre contournements identifiés lors de
> l'audit « extensions non fiables par défaut » sont fermés et verrouillés par
> `tests/security/test_extension_security.py` (38 tests).

Principe appliqué (AGENTS.md) : un skill, un plugin ou un serveur d'outils est
un composant **non fiable par défaut**. La politique est appliquée par le Core
(validation puis exécution), jamais par une interface, et jamais par confiance
dans l'appelant.

## 1. Validateur de plugins — imports pointés

`import os.path` lie le module racine `os` : il doit être refusé comme
`import os`. La liste `FORBIDDEN_IMPORTS` était comparée au nom complet
(`os.path` n'y figure pas) → l'import passait et `os.system(...)` devenait
appelable dans le plugin.

Correction : la comparaison porte sur le premier segment du nom
(`alias.name.split(".")[0]`), pour `ast.Import` **et** `ast.ImportFrom`.
Tests : `TestPluginValidatorDottedImports` — refus de `os.path` et
`subprocess.foo`, acceptation de `json.decoder` (pas de faux positif).

## 2. Loader de plugins — provenance et résolution de version

Deux défauts de la chaîne de chargement :

| Défaut | Effet | Correction |
|---|---|---|
| `_verify_signature` jamais appelée | un `manifest.json` altéré après signature était chargé sans contrôle | appel dans `load()` : signature présente = doit correspondre au SHA-256 de `manifest.json` ; absente = plugin non signé (chemin développement) ; invalide = rejet + log |
| `_resolve_version` comparait des chaînes | `"1.9.0" > "1.10.0"` est vrai lexicographiquement → une version **antérieure** pouvait remplacer la version chargée | comparaison sémantique (`PluginVersion.parse`), repli lexical uniquement si la version n'est pas semver |

Tests : `TestPluginLoaderIntegrity` (signature valide / invalide / manifest
altéré) et `TestPluginLoaderSemver`.

## 3. Plugin terminal — continuation de ligne

La liste des motifs dangereux (`&&`, `||`, `;`, `|`, backticks, `$(`, `${`,
`&`, `>`, `<`) omettait `\n` et `\r`. Or la commande validée est exécutée par
`asyncio.create_subprocess_shell` : un retour à la ligne y est un séparateur de
commandes. `"ls -la\nrm -rf /"` passait donc la whitelist (`shlex.split` ne
retient que `ls`) puis exécutait la seconde commande.

Correction : `\n` et `\r` ajoutés à la liste. Tests :
`TestTerminalCommandValidation` (enchaînement, redirection, substitution,
substitution arrière, continuation).

## 4. Skill Lab — `pip install` sur entrée non fiable

`_run_in_docker` interpolait les `requirements` reçus de l'API dans une ligne
`sh -c "pip install {deps} && python /tmp/skill.py"`. `"requests; curl …"` (ou
`&&`, backticks, redirection) sortait de la commande pip et s'exécutait dans le
conteneur : la validation des paquets était contournable et le conteneur
exécutait une commande non contrôlée avant même le code du skill.

Correction en couches indépendantes :

1. `_validate_requirements` (fail-closed) — chaque entrée doit être un
   requirement PEP 508 simplifié : nom, extras `[..]`, contrainte de version.
   Aucun espace ni métacaractère shell n'est accepté.
2. `_build_docker_command` — les requirements sont transmis en **arguments
   positionnels** du shell (`sh -c 'pip install --no-input "$@" && python …'`
   `ethan-lab <req>…`) : même si la validation amont était contournée, la
   donnée ne peut pas devenir du code. Sans dépendances, aucun shell n'est
   invoqué.
3. `_safe_container_name` — le nom du conteneur est assaini (le nom du skill
   est fourni par l'appelant) avant d'être passé à `docker run --name`.

Tests : `TestSkillLabRequirements`, `TestSkillLabContainerName`.

## 5. Fichiers

- `core/plugins/validator.py` — premier segment des imports
- `plugins/loader.py` — signature branchée, versions semver
- `plugins/terminal/main.py` — `\n` / `\r` refusés
- `core/skills/lab.py` — validation + argv + nom de conteneur
- `tests/security/test_extension_security.py` — 38 tests

## 6. Invariants vérifiés

- **Défense en profondeur** : validation (couche 1) et construction de commande
  (couche 2) sont indépendantes ; contourner l'une ne suffit pas.
- **Fail-closed** : une entrée non conforme est refusée, jamais nettoyée
  silencieusement puis exécutée.
- **Pas de maintenance de charges** : la liste terminal est structurelle
  (métacaractères), pas une liste de commandes dangereuses à compléter.
- **Provenance** : un plugin signé puis modifié ne se charge plus ; l'absence
  de signature reste un chemin « développement » explicite (loggé).

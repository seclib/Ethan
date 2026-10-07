# Revue de production du CLI ETHAN

Date : 5 octobre 2026. Revue du checkout courant sous Debian 13 et Python
3.13.5. L'arbre de travail avait de nombreuses modifications non commités;
les résultats décrivent cet état. Cette revue n'a pas modifié les commandes
du CLI.

## Suivi — 6 octobre 2026 (correctifs P1 appliqués)

| Statut | Résultat |
|---|---|
| **PASS — P1** | Version = métadonnées installées (`Ethan`, hatch-vcs) : `ethan --version` affiche `0.0.1.dev137+…`, `interfaces/cli/pyproject.toml` marqué NON-DISTRIBUABLE. |
| **PASS — P1** | `--no-color` respecté par l'aide (`ctx.color`, zéro ANSI en pipe). |
| **PASS — P1** | `auth create-admin/list/reset-password` refusés par défaut (exit 4 + hint, refus `change-me-in-prod`) ; `--i-understand-direct-db` explicite en attendant le bootstrap Core. |
| **PASS — P2** | `ruff check interfaces/cli` : 0 diagnostic (194 → 0). |
| **PASS — P2** | `version -o json` renseigne `core` via `GET /version` (timeout 2 s, `null` hors-ligne, jamais bloquant). |

Restent ouverts (P2) : relecture token legacy `interfaces/cli/config.py`,
typecheck non configuré, wheel 57,5 Mo (distribution Core+CLI assumée),
plafond Python du sous-paquet, upgrade inter-versions et stack Core réelle.

## Synthèse — état au 6 octobre 2026 (revérifié)

| Statut | Résultat |
|---|---|
| **PASS** | Packaging : paquet racine `Ethan` seul (hatch-vcs, `ethan=interfaces.cli.main:main`) ; `interfaces/cli/pyproject.toml` marqué NON-DISTRIBUABLE. |
| **PASS** | Version : `ethan --version` = métadonnées installées (`0.0.1.dev137+…`, repli `1.0.0` hors install) ; `version -o json` renseigne `core` via `GET /version` (timeout 2 s, `null` hors-ligne). |
| **PASS** | UX : `--no-color` respecté par l'aide (zéro ANSI vérifié) ; exit codes contrat §5 ; `-o json` 1-doc ; `auth list` sans flag → exit 4 + hint stderr. |
| **PASS** | Tests/lint : `tests/cli + test_cli_plugin_cmd` **531 passed** ; `ruff format` 76 fichiers ; `ruff check` **0 diagnostic**. |
| **WARN — P2** | Relecture token legacy `interfaces/cli/config.py` (permissions inconnues) conservée après `credentials.json`. |
| **WARN — P2** | Typecheck non configuré ; wheel 57,5 Mo (distribution Core+CLI assumée) ; plafond Python sous-paquet ; upgrade inter-versions et stack Core réelle non rejoués ici. |

Les 3 FAIL P1 du 05/10 (version, `--no-color`, DB directe) et 2 WARN P2
(ruff, `core: null`) sont clos. Reste le trio DB derrière garde-fou explicite
en attendant le bootstrap admin Core (dette architecturale assumée, plus un
contournement silencieux).

## Matrice de vérification

| Catégorie | Résultat | Exécution / couverture |
|---|---|---|
| Unit | **PASS** | `pytest -q tests/cli tests/test_cli_plugin_cmd.py` — 531 passed. |
| Integration | **PASS partiel** | Les tests CLI utilisent des clients/API simulés; ils couvrent dispatch, configuration, authentification, erreurs HTTP, sorties et commandes. Aucune stack ETHAN réelle n'était démarrée. |
| CLI smoke | **PASS partiel** | Wheel installé dans un virtualenv neuf, invocation depuis `/tmp`: `ethan --version`, `ethan --help`, commande inconnue, option de sortie invalide, API refusant la connexion et JSON d'erreur. L'API indisponible renvoie exit 5. |
| API | **WARN** | Le Core local distant, l'authentification réelle et les écarts de version n'ont pas été testés contre un serveur. Le Core URL configurable est couvert par les tests simulés. |
| Security | **WARN** | Revue statique des tokens, permissions, journalisation et arguments. `credentials.json` est créé/corrigé en `0600`, `--token` avertit sur son exposition, et des tests CLI passent. Les commandes d'administration DB restent une exception architecturale et de sécurité. Pas d'audit dynamique complet des flux ou fichiers temporaires. |
| Packaging | **FAIL partiel** | Build wheel racine **PASS** (`ethan-0.0.1.dev137+unknown.g4a7e8e026.d20261005`, 57,5 MB), installation sans dépendances dans un virtualenv vierge et smoke `--version` **PASS**. Build wheel `interfaces/cli` **FAIL**: setuptools détecte plusieurs paquets de premier niveau (`ui`, `core`, `plugins`, `commands`). |

## Détails prioritaires

### P1 — Construire une seule distribution officielle et aligner ses versions

Deux métadonnées déclarent l'entrée `ethan` : la racine utilise Hatch/VCS et
la cible `interfaces.cli.main:main`, tandis que `interfaces/cli/pyproject.toml`
déclare `ethan-cli` version `1.0.0` avec setuptools. Ce dernier build échoue
sur la découverte automatique des paquets. Le wheel racine se construit, mais
sa version VCS générée ne correspond pas à `interfaces/cli/_version.py` qui
est codé en dur à `1.0.0`. Il faut désigner une source de vérité de packaging
et de version avant release.

### P1 — Corriger les sorties couleur

`interfaces/cli/main.py::_show_help` emploie directement les constantes ANSI
de `core/colors.py`. Il ignore le `color` calculé dans `CLIContext`, ce qui
fait apparaître les séquences de contrôle dans les logs et sorties redirigées
et rend `--no-color` inopérant sur l'aide.

### P1 — Garder l'administration des utilisateurs derrière le Core

`interfaces/cli/commands/auth.py` conserve trois chemins d'administration
qui se connectent directement à PostgreSQL. `_get_db_url()` inclut une valeur
de mot de passe par défaut `change-me-in-prod`. Cela contourne la frontière
API et doit être retiré ou migré vers une capacité Core avant une release de
production.

### P2 — Version et compatibilité Core

L'API expose `GET /version` dans `interfaces/api/routers/state.py`, mais le
CLI ne le consulte pas. La commande `version` remplit `core` par `null`; le
CLI ne peut donc pas avertir quand le contrat ou le serveur est incompatible.
Les cas Core local, Core distant et version incompatible restent à valider
sur une stack réelle.

### P2 — Séparer les dépendances du CLI

Le wheel racine est fonctionnel, mais embarque les dépendances générales
d'ETHAN. Le wheel n'est pas une publication autonome légère du CLI; une
installation fraîche standard résoudra toute cette liste. Debian 13 refuse
également les installations pip dans le Python système (PEP 668); le guide
recommande un environnement virtuel.

## Commandes et résultats

- `python3 -m interfaces.cli.main --version` depuis le checkout : **PASS**,
  affiche `ETHAN CLI v1.0.0`.
- `python -m pip wheel --no-deps --no-build-isolation --wheel-dir
  /tmp/ethan-cli-audit-root .` : **PASS**.
- `python -m pip wheel --no-deps --no-build-isolation --wheel-dir
  /tmp/ethan-cli-audit-subproject ./interfaces/cli` : **FAIL** (découverte
  setuptools ambiguë).
- `pytest -q tests/cli tests/test_cli_plugin_cmd.py` : **PASS**, 531 tests.
- `ruff format --check interfaces/cli` : **PASS**, 76 fichiers inchangés.
- `ruff check interfaces/cli` : **FAIL**, 194 diagnostics.
- Typecheck : **WARN / non configuré** (aucune cible mypy, pyright ou
  `typecheck` trouvée dans le projet).
- `ethan -o json provider list` contre `127.0.0.1:1` : **PASS** pour le
  contrat d'erreur, exit 5 et JSON uniquement sur stdout.
- Installation répétée du même wheel : pip indique que la même version est
  déjà installée et n'effectue aucune mise à niveau; désinstallation du wheel
  isolé : **PASS**. Une mise à niveau entre deux versions distinctes n'a pas
  pu être vérifiée avec un seul artefact de build.
- Sortie couleur : **FAIL**, l'aide fraîchement installée émet de l'ANSI
  dans un pipe.
- Tests complets Core, build Docker et package d'une release publiée : non
  exécutés dans cette revue CLI.

## Documentation

Le guide historique `docs/user-guide/cli.md` décrivait `jarvis` et des
commandes d'un ancien CLI. Il a été remplacé par un guide qui reflète le CLI
actuel et ses limites connues. Le README du CLI indique désormais le paquet
racine comme voie d'installation depuis un virtualenv et identifie
l'installateur historique comme tel.

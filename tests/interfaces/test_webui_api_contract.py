"""Contrat WebUI -> API : chaque chemin appele par le WebUI existe-t-il ?

Precedent motive (refonte UX, 30/09/2026) : le Shell ETHAN etait casse en
silence parce qu'il interrogeait `POST /message` alors que l'API sert
`POST /v1/message` — et l'echec se deguisait en « API unreachable ». Meme
famille de panne, meme kilometrage vers le Shell : la WebUI Could have called
a route that does not exist and nothing would have said so.

Ces tests lisent le code source de l'interface et la surface reellement
declaree par l'application, puis exigent la correspondance. Aucun serveur, aucun
NATS, aucun state : l'import de `app` ne declenche PAS son lifespan.

Trois conventions du WebUI sont figees ici :
  1. le proxy `src/app/api/[...path]/route.ts` retire `/api` et RIEN d'autre
     (pas de `/v1` automatique) — le chemin JS est donc le chemin backend ;
  2. `apiFetch` accepte un chemin litteral ou un template ; les `${...}` sont
     des fragments de query-string ou des branches, pas des segments ;
  3. les segments `${id}` valent un parametre de chemin, compare generique.

Regle AGENTS.md : ce test ne fait QUE de la lecture. Aucune logique metier,
aucune decision de design — les doubles listes (Knowledge/Library,
Tools/MCP) sont signalees comme un CONSTAT, pas tranchees ici.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from tests.contract_kit import declared_routes

WEBUI = Path(__file__).resolve().parents[2] / "interfaces" / "webui"
API_MODULES = WEBUI / "src" / "lib" / "api"
PROXY = WEBUI / "src" / "app" / "api" / "[...path]" / "route.ts"

# `apiFetch(`/models/${id}`)` | `apiFetch<Array<Record<string, unknown>>>('/x')`
# | `fetch('/api/health/detailed')` (legacy). Le template est capture SEUL :
# un backtick peut contenir des quotes.
CALL_RE = re.compile(
    r"""(?:apiFetch(?:<[^(]*?>)?|fetch)\(\s*(?:`([^`]*)`|'([^']*)'|"([^"]*)")"""
)


def _interpolate_to_segments(path: str) -> str:
    """`/folders/${id}` -> `/folders/{x}`. On retire les query-strings.

    Les `${...}` sont consommés bloc par bloc : le premier `}` ferme le bloc
    (une interpolation peut contenir un `?` : `${refresh ? "?refresh=true" : ""}`).
    """
    out: list[str] = []
    i = 0
    while i < len(path):
        if path.startswith("${", i):
            end = path.find("}", i)
            if end == -1:  # bloc non ferme : on garde le reste tel quel
                out.append(path[i:])
                break
            if out and out[-1] != "/":
                out.append("/")
            out.append("{x}")
            i = end + 1
        else:
            out.append(path[i])
            i += 1
    return "".join(out).split("?")[0].rstrip("/") or "/"


def _called_paths() -> dict[str, set[str]]:
    """Chemin backend -> modules WebUI qui l'appellent. Lecture seule."""
    called: dict[str, set[str]] = defaultdict(set)
    for module in sorted(API_MODULES.glob("*.ts")):
        for match in CALL_RE.finditer(module.read_text(encoding="utf-8", errors="replace")):
            raw = match.group(1) or match.group(2) or match.group(3)
            if not raw or not raw.startswith("/"):
                continue
            if raw.startswith("/api/"):  # le proxy retire ce prefixe
                raw = raw[4:]
            called[_interpolate_to_segments(raw)].add(module.stem)
    return called


class TestProxyContract:
    def test_le_proxy_ne_rajoute_aucun_prefixe(self):
        """`/api` est le SEUL prefixe retiré : le chemin JS = chemin backend.

        C'est la convention qui rend `/models` -> `GET /models`. Si le proxy
        ajoutait `/v1`, tous les chemins du WebUI seraient faux sans que rien
        ne le signale.
        """
        source = PROXY.read_text(encoding="utf-8")
        assert 'pathname.replace(/^\\/api/, "")' in source, (
            "le proxy doit retirer exactement `/api` — vérifier tout appel "
            "WebUI avant de modifier cette règle"
        )


class TestCheminsAppeles:
    def test_chaque_prefixe_appele_existe_sur_l_api(self):
        """Aucun appel WebUI ne doit cibler une route inexistante.

        On compare le PREFIXE litteral (avant le premier `${}`) : exiger la
        forme exacte produirait des faux positifs sur les query-strings et sur
        les interpolations de segments (`/folders/tree${query}` -> `/tree`).
        """
        declared = {re.sub(r"\{[^}]+\}", "{x}", path) for _, path in declared_routes()}
        orphans = {}
        for path, modules in _called_paths().items():
            literal = path.split("{x}")[0].rstrip("/")
            if literal.startswith("/api"):  # prefixe retire par le proxy
                literal = literal[4:].rstrip("/")
            if not literal:
                # Appel 100 % dynamique (`/api${path}`) : rien de verifiable
                # statiquement — les appels litteraux du meme module le sont.
                continue
            if not any(declared_path == literal or declared_path.startswith(literal + "/") for declared_path in declared):
                orphans[path] = modules
        assert not orphans, (
            "chemins appeles par le WebUI mais absents de l'API (corriger "
            f"l'interface, pas l'API) : {orphans}"
        )

    def test_le_webui_appelle_bien_l_api(self):
        """Garde-fou de l'audit : un module sans appel est une page morte.

        Detecte une page qui perdrait son branchement data (erreur de refactor
        silencieuse : l'UI s'affiche, plus jamais rien).
        """
        inert = {m.stem for m in API_MODULES.glob("*.ts")} - {
            m for modules in _called_paths().values() for m in modules
        }
        assert inert <= {"client"}, f"modules sans aucun appel API : {sorted(inert)}"


class TestDoublesConstates:
    """Constat, PAS une regle : documente les surfaces qui se recouvrent.

    Deux paires partagent des endpoints Core identiques. La decision de les
    fusionner appartient a l'UX (document de cartographie) ; ce test garantit
    seulement que le recouvrement reste visible et non Silent.
    """

    def test_recouvrements_connus_toujours_visibles(self):
        called = _called_paths()
        overlaps = {
            path: sorted(modules)
            for path, modules in called.items()
            if len(modules) > 1 and path != "/files"
        }
        # Invite a revalider la decision UX a chaque evolution de la surface.
        assert overlaps, "aucun recouvrement — la cartographie doit etre revalidee"
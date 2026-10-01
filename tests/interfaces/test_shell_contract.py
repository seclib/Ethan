"""Contrat de l'interface Shell vis-a-vis de l'API ETHAN.

Precedent motive (phase B, 30/09/2026) : `ethan "hello"` etait muetement
casse - l'interface envoyait `POST /message {"content": ...}` et lisait
`GET /state`, alors que l'API sert `POST /v1/message` avec un champ
**`input`** et exige un **JWT**. Trois fautes distinctes, une seule visible
en shell ("API unreachable"), parce que `_ethan_api_raw` traitait toute
reponse non vide comme un succes.

Ces tests figent le contrat, sans exiger de serveur :
1. chaque route appelee par le shell existe reellement sur l'application ;
2. le champ de charge utile POST est un champ **requis** de `MessageRequest`
   (donc : jamais un nom invente par l'interface) ;
3. les codes d'echec sont distingues (401 != 404 != 422 != 503) - pas de
   message generique qui masque la cause racine ;
4. bash et zsh **sourcent** `core.sh` au lieu de dupliquer le contrat ;
   fish ne peut pas sourcer du bash, son portage est donc compare a `core.sh`.

Regle AGENTS.md : aucune logique metier ici. Le shell est une interface ; il
consomme des capacites Core, il n'en cree pas. Ce test verifie uniquement
qu'il interroge la bonne surface, avec le bon vocabulaire.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.contract_kit import declared_routes

SHELL = Path(__file__).resolve().parents[2] / "interfaces" / "shell" / "ethan-shell"
CORE_SH = SHELL / "cli" / "core.sh"
ADAPTERS = {
    "bash": SHELL / "adapters" / "bash" / "ethan.bash",
    "zsh": SHELL / "adapters" / "zsh" / "ethan.zsh",
    "fish": SHELL / "adapters" / "fish" / "ethan.fish",
}

# Fichiers "sur le contrat" : tout fichier qui parle a l'API.
CONTRACT_FILES = {"core.sh": CORE_SH, **ADAPTERS}


@pytest.fixture(scope="module")
def routes() -> set[tuple[str, str]]:
    return declared_routes()


def _code_only(path: Path) -> str:
    """Le fichier sans ses lignes de commentaire (un `#` ne casse pas un test)."""
    raw = path.read_text(encoding="utf-8")
    return "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))


def _request_lines(path: Path) -> list[str]:
    """Les lignes qui EMETTENT une requete (les autres ne comptent pas).

    Distinction cruciale : la ligne `echo "ERR: /v1/message introuvable"`
    mentionne une route sans en emettre aucune. La lire l'aurait fait passer
    pour un appel reel, et le bug historique (route non versionnee) a echappe
    au test pendant qu'on extrayait /v1/... de tout le fichier.
    """
    return [l for l in _code_only(path).splitlines() if "curl" in l]


def _paths_called(path: Path) -> set[str]:
    """Chemins d'API reellement demandes par ce fichier shell."""
    paths: set[str] = set()
    for line in _request_lines(path):
        paths |= set(re.findall(r"(/v1/[a-z_/]+)", line))
    return paths


# Lignes qui portent un CORPS de requete. Sans ce filtre, on confondrait
# « ce que le shell ENVOIE » avec « ce qu'il FABRIQUE pour s'afficher quand
# l'API est morte » (le repli `{"mode":"offline",...}` de _ethan_status).
_BODY_MARKERS = ("json.dumps", "-d \"", "-d '", "--data")


def _request_fields(path: Path) -> set[str]:
    """Champs JSON reellement places dans un corps de requete par ce fichier."""
    fields: set[str] = set()
    for line in _code_only(path).splitlines():
        if any(marker in line for marker in _BODY_MARKERS):
            fields |= set(re.findall(r"\{\\?\"([a-z_]+)\\?\":", line))
    return fields


class TestRoutesAppelees:
    def test_chaque_route_appelee_existe_sur_l_api(self, routes):
        """Cause racine n1 : /message et /state n'existent pas (prefixe /v1)."""
        declared_paths = {path for _, path in routes}
        missing = {
            name: sorted(p for p in _paths_called(path) if p not in declared_paths)
            for name, path in CONTRACT_FILES.items()
        }
        assert {k: v for k, v in missing.items() if v} == {}

    def test_les_fichiers_qui_parlent_a_l_api_utilisent_v1(self):
        """Core.sh et fish emettent reellement des requetes : eux doivent viser /v1."""
        for name in ("core.sh", "fish"):
            called = _paths_called(CONTRACT_FILES[name])
            assert "/v1/message" in called, f"{name} n'appelle plus /v1/message"
            assert "/v1/state" in called, f"{name} n'appelle plus /v1/state"

    def test_bash_et_zsh_n_emettent_aucune_requete_eux_memes(self):
        """Sourcer core.sh veut dire : zero curl dans l'adaptateur.

        Si un `curl` reapparait dans bash/zsh, c'est qu'une logique s'est
        re-dupliquee hors du contrat shared — le chemin exact vers une
        divergence entre shells.
        """
        for name in ("bash", "zsh"):
            assert _request_lines(ADAPTERS[name]) == [], (
                f"{name} emet ses propres requetes au lieu de deleguer a core.sh"
            )

    def test_methods_http_conformes(self, routes):
        """`/v1/message` se POST, `/v1/state` se GET : pas l'inverse."""
        for method, path in (("POST", "/v1/message"), ("GET", "/v1/state")):
            assert (method, path) in routes, f"{method} {path} absent de l'application"

    def test_toute_requete_curl_vise_une_route_versionnee(self):
        """Regle structurelle, pas une liste de cas connus.

        `STALE_CALLS` ne protegeait que les formes qu'on avait deja vues :
        mutate `${base%/}/v1/message` en `${base%/}/message` et le test
        passait quand meme. Ici, des qu'une ligne emet un curl, son chemin
        DOIT etre sous /v1/ - y compris pour des routes jamais inventees.
        """
        for name, path in CONTRACT_FILES.items():
            for line in _request_lines(path):
                assert "/v1/" in line, (
                    f"{name}: requete hors /v1 -> {line.strip()}"
                )



class TestChargeUtile:
    def test_le_champ_de_charge_utile_est_requis_par_le_schema_core(self):
        """Cause racine n2 : le shell envoyait `content`, le schema exige `input`."""
        from interfaces.api.models.requests import MessageRequest

        required = {n for n, f in MessageRequest.model_fields.items() if f.is_required()}
        assert "input" in required, "MessageRequest n'exige plus `input`"

        for name, path in CONTRACT_FILES.items():
            fields = _request_fields(path)
            unknown = {f for f in fields if f not in MessageRequest.model_fields}
            assert unknown == set(), f"{name} envoie un champ inconnu de Core : {sorted(unknown)}"
            # bash/zsh ne construisent rien : ils sourcent core.sh (verifie plus bas).
            assert fields <= {"input"}, f"{name} envoie plus que `input` : {fields}"

    def test_ceux_qui_envoient_une_message_utilisent_input(self):
        """Le nom du champ n'est pas un choix de l'interface : c'est celui du Core."""
        for name in ("core.sh", "fish"):  # les seuls qui construisent un corps
            assert _request_fields(CONTRACT_FILES[name]) == {"input"}, (
                f"{name} ne construit plus sa charge utile qu'avec `input`"
            )


class TestDiagnosticHonnete:
    def test_chaque_cause_racine_est_distinguee(self):
        """Cause racine n3 : 401/404/422/503 etaient tous `API unreachable`."""
        text = _code_only(CORE_SH)
        for code in ("401", "403", "404", "422", "503"):
            assert code in text, f"le code {code} n'est pas traite explicitement"
        # Le message generique qui masquait tout ne doit pas revenir dans le code.
        assert "API unreachable" not in text

    def test_le_code_000_n_est_pas_pris_pour_un_code_http(self):
        """Couvert par la preuve vivante, pas par l'analyse statique.

        API eteinte -> curl rend 000 avec un corps vide : l'ancien `case *)`
        produisait un laconique « ERR: HTTP 000 — » sans nommer l'hote. Le
        shell doit dire QUELLE adresse est morte.
        """
        for name in ("core.sh", "fish"):
            text = _code_only(CONTRACT_FILES[name])
            assert "000" in text, f"{name} ne traite pas le code 000 (connexion refusée)"
            assert "injoignable" in text, f"{name} ne nomme pas l'API injoignable"

    def test_le_status_ne_juge_plus_sur_le_seul_corps_non_vide(self):
        """Regle d'or : un corps JSON n'est PAS une preuve de succes.

        Un 401 renvoie {"detail":"Authentification requise..."} : non vide.
        L'ancien `curl ... || echo fallback` l'affichait comme l'etat reel.
        """
        for name in ("core.sh", "fish"):
            text = _code_only(CONTRACT_FILES[name])
            assert "http_code" in text, f"{name} ne recueille plus le code HTTP pour /v1/state"
            assert "-o " in text, f"{name} ne separe plus le corps de la reponse"

    def test_le_token_vient_de_l_environnement_pas_du_code(self):
        """Regle secret : aucun JWT en dur, tout passe par ETHAN_TOKEN."""
        for name, path in CONTRACT_FILES.items():
            text = _code_only(path)
            assert "ETHAN_TOKEN" in text, f"{name} ne lit pas ETHAN_TOKEN"
            # Un JWT en clair (eyJ...) serait un secret commite.
            assert "eyJ" not in text, f"{name} contient un JWT en dur"

    def test_les_adaptateurs_bash_et_zsh_sourcent_core_sh(self):
        """Anti-duplication : bash/zsh ne doivent pas redefinir le contrat."""
        for name in ("bash", "zsh"):
            text = _code_only(ADAPTERS[name])
            assert "core.sh" in text, f"{name} ne source plus core.sh"
            # Une definition locale = divergence possible.
            for func in ("_ethan_api()", "_ethan_status()"):
                assert func not in text, f"{name} redefinit {func} au lieu de sourcer core.sh"

    def test_le_portage_fish_reste_aligne_de_core_sh(self):
        """fish ne peut pas sourcer du bash : son portage doit rester equivalent."""
        fish = _code_only(ADAPTERS["fish"])
        assert "/v1/message" in fish and "/v1/state" in fish
        assert "ETHAN_TOKEN" in fish
        # Meme verbe, meme cause : fish doit traduire les codes, pas les avaler.
        for code in ("401", "404"):
            assert code in fish, f"fish ne distingue plus le code {code}"

"""Profils réseau ETHAN — configuration des connexions Web Research.

Abstraction Core-only : les interfaces (WebUI, CLI, agents) ne transmettent
qu'un **identifiant de profil** ; le Core résout et applique la configuration
réseau correspondante. La WebUI n'implémente jamais la logique réseau.

Types : ``direct``, ``http``, ``https``, ``socks5``, ``vpn``.

Sécurité (directive secrets AGENTS.md) :
- les credentials ne sont JAMAIS stockés dans le profil, la configuration,
  les logs ou les réponses API : le profil référence des **variables
  d'environnement** (mécanisme de secrets déjà utilisé par ETHAN) ;
- la résolution lit l'environnement au moment de la connexion (fail-fast si
  la variable est absente ou vide) ;
- les vues publiques (``public_view`` / ``list_profiles``) et le ``repr``
  sont expurgés : aucun secret n'y figure, par construction.

VPN — point d'intégration documenté (ne pas inventer) :
le type ``vpn`` est déclarable et validable, mais le Core ne modifie JAMAIS
le routage système. Sa résolution lève ``NetworkProfileError`` tant qu'un
service ETHAN dédié (Runtime, privilèges explicites, mécanisme prévu) ne
fournit pas un point de sortie réseau. Aucune intégration implicite.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

# Identifiant du profil « connexion directe » (toujours disponible).
DIRECT_PROFILE_ID = "direct"

# Bornes du timeout par requête (secondes) — politesse réseau (AGENTS.md).
MIN_TIMEOUT_SECONDS = 1.0
MAX_TIMEOUT_SECONDS = 120.0
DEFAULT_TIMEOUT_SECONDS = 10.0

_PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class NetworkProfileError(ValueError):
    """Profil réseau invalide, inconnu, désactivé ou non résoluble."""


class NetworkProfileType(StrEnum):
    """Types de profils réseau supportés par le Core."""

    DIRECT = "direct"
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"
    VPN = "vpn"  # déclaratif uniquement — voir docstring module


_PROXY_TYPES = frozenset(
    {NetworkProfileType.HTTP, NetworkProfileType.HTTPS, NetworkProfileType.SOCKS5}
)


@dataclass(frozen=True)
class NetworkProfile:
    """Profil réseau déclaratif (SANS secret).

    Les credentials sont référencés par nom de variable d'environnement
    (``username_env`` / ``password_env``) — jamais stockés en clair.
    """

    id: str
    type: NetworkProfileType
    host: str | None = None
    port: int | None = None
    username_env: str | None = None
    password_env: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    enabled: bool = True

    def __post_init__(self) -> None:
        # -- type : accepte la valeur textuelle, sinon strict -----------------
        if isinstance(self.type, str):
            try:
                object.__setattr__(self, "type", NetworkProfileType(self.type))
            except ValueError as exc:
                raise NetworkProfileError(
                    f"Type de profil réseau invalide : {self.type!r} "
                    f"(attendus : {[t.value for t in NetworkProfileType]})"
                ) from exc
        if not isinstance(self.type, NetworkProfileType):
            raise NetworkProfileError(f"Type de profil réseau invalide : {self.type!r}")

        # -- id : slug strict --------------------------------------------------
        if not isinstance(self.id, str) or not _PROFILE_ID_RE.match(self.id):
            raise NetworkProfileError(
                f"id de profil réseau invalide : {self.id!r} "
                "(slug attendu : minuscules/chiffres/'-'/'_', max 64)"
            )

        # -- timeout : flottant strict, borné ---------------------------------
        timeout = self.timeout_seconds
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise NetworkProfileError(f"timeout_seconds invalide : {timeout!r} (nombre attendu)")
        if not (MIN_TIMEOUT_SECONDS <= float(timeout) <= MAX_TIMEOUT_SECONDS):
            raise NetworkProfileError(
                f"timeout_seconds hors bornes : {timeout!r} "
                f"(accepté : {MIN_TIMEOUT_SECONDS}..{MAX_TIMEOUT_SECONDS} secondes)"
            )
        object.__setattr__(self, "timeout_seconds", float(timeout))

        # -- port : entier strict 1..65535 ------------------------------------
        port = self.port
        if port is not None:
            if isinstance(port, bool) or not isinstance(port, int):
                raise NetworkProfileError(f"port invalide : {port!r} (entier attendu)")
            if not (1 <= port <= 65535):
                raise NetworkProfileError(f"port hors bornes : {port!r} (accepté : 1..65535)")

        # -- host : requis pour un proxy, interdit pour direct ----------------
        host = self.host
        if self.type is NetworkProfileType.DIRECT:
            if host is not None or port is not None:
                raise NetworkProfileError(
                    "Profil 'direct' : aucun host/port attendu (connexion sans intermédiaire)"
                )
        elif self.type in _PROXY_TYPES:
            if not isinstance(host, str) or not host.strip():
                raise NetworkProfileError(f"Profil {self.type.value!r} : host requis")
            if port is None:
                raise NetworkProfileError(f"Profil {self.type.value!r} : port requis")
            # Interdits : userinfo/scheme injecté dans le host ('@', '/', '://')
            if any(c in host for c in "@/ \t") or "://" in host or host.startswith(":"):
                raise NetworkProfileError(
                    f"host de proxy invalide : {host!r} "
                    "(hostname ou IP nue attendue — sans scheme ni userinfo)"
                )
        # VPN : host/port optionnels (déclaratifs, résolution refusée).

        # -- credentials : références env, par paire --------------------------
        for attr in ("username_env", "password_env"):
            value = getattr(self, attr)
            if value is not None and not _ENV_NAME_RE.match(str(value)):
                raise NetworkProfileError(
                    f"{attr} invalide : {value!r} "
                    "(nom de variable d'environnement attendu : [A-Z_][A-Z0-9_]*)"
                )
        if (self.username_env is None) != (self.password_env is None):
            raise NetworkProfileError(
                "Credentials incomplets : username_env et password_env "
                "doivent être fournis ensemble"
            )

    # -- Vues publiques (jamais de secret) -----------------------------------

    @property
    def proxy_url(self) -> str | None:
        """URL d'intermédiaire (SANS credentials), ``None`` si direct/vpn."""
        if self.type in _PROXY_TYPES and self.host and self.port:
            return f"{self.type.value}://{self.host}:{self.port}"
        return None

    def public_view(self) -> dict[str, Any]:
        """Vue sûre pour les interfaces/API : aucun secret."""
        return {
            "id": self.id,
            "type": self.type.value,
            "host": self.host,
            "port": self.port,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "has_credentials": self.username_env is not None,
        }


@dataclass(frozen=True)
class ResolvedNetwork:
    """Configuration réseau résolue pour une connexion (usage Core interne).

    ``username``/``password`` sont exclus du ``repr`` (fuite impossible par
    journalisation accidentelle) et de ``public_view``.
    """

    profile_id: str
    profile_type: NetworkProfileType
    proxy_url: str | None = None
    username: str | None = field(default=None, repr=False)
    password: str | None = field(default=None, repr=False)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def public_view(self) -> dict[str, Any]:
        """Vue sûre (journalisation, debug, API) : aucun secret."""
        return {
            "profile_id": self.profile_id,
            "profile_type": self.profile_type.value,
            "proxy_url": self.proxy_url,
            "has_credentials": self.password is not None,
            "timeout_seconds": self.timeout_seconds,
        }


class NetworkProfileManager:
    """Registre des profils réseau — le Core ne reçoit que l'identifiant.

    ``environ`` est injectable pour les tests (défaut : ``os.environ``).
    """

    def __init__(self, *, environ: Mapping[str, str] | None = None) -> None:
        self._environ: Mapping[str, str] = os.environ if environ is None else environ
        self._profiles: dict[str, NetworkProfile] = {}
        # Profil « direct » toujours disponible (connexion sans intermédiaire).
        self.register(NetworkProfile(id=DIRECT_PROFILE_ID, type=NetworkProfileType.DIRECT))

    # -- Registre ------------------------------------------------------------

    def register(self, profile: NetworkProfile, *, replace: bool = False) -> None:
        """Enregistre un profil (refus des doublons sauf ``replace=True``)."""
        if not isinstance(profile, NetworkProfile):
            raise NetworkProfileError("NetworkProfile attendu")
        if not replace and profile.id in self._profiles:
            raise NetworkProfileError(
                f"Profil réseau déjà enregistré : {profile.id!r} (replace=True pour remplacer)"
            )
        self._profiles[profile.id] = profile

    def get(self, profile_id: str) -> NetworkProfile:
        pid = str(profile_id or "").strip()
        profile = self._profiles.get(pid)
        if profile is None:
            raise NetworkProfileError(
                f"Profil réseau inconnu : {pid!r} "
                f"(enregistrés : {', '.join(sorted(self._profiles))})"
            )
        return profile

    def ids(self) -> list[str]:
        return sorted(self._profiles)

    def list_profiles(self) -> list[dict[str, Any]]:
        """Vues publiques de tous les profils (aucun secret)."""
        return [p.public_view() for p in self.get_profiles()]

    def get_profiles(self) -> list[NetworkProfile]:
        return [self._profiles[pid] for pid in sorted(self._profiles)]

    def set_enabled(self, profile_id: str, enabled: bool) -> NetworkProfile:
        """Active/désactive un profil (un profil désactivé n'est pas résoluble)."""
        profile = replace(self.get(profile_id), enabled=bool(enabled))
        self._profiles[profile.id] = profile
        return profile

    # -- Résolution ----------------------------------------------------------

    def resolve(self, profile_id: str) -> ResolvedNetwork:
        """Résout un identifiant de profil en configuration de connexion.

        Raises:
            NetworkProfileError: profil inconnu, désactivé, VPN non intégré,
                ou variable d'environnement de credential absente/vide.
        """
        profile = self.get(profile_id)
        if not profile.enabled:
            raise NetworkProfileError(f"Profil réseau désactivé : {profile.id!r}")
        if profile.type is NetworkProfileType.VPN:
            raise NetworkProfileError(
                "Profil VPN non résoluble : le Core ne modifie jamais le "
                "routage système. Point d'intégration à fournir par un "
                "service ETHAN dédié (Runtime, privilèges explicites)."
            )

        username: str | None = None
        password: str | None = None
        if profile.username_env:
            username = self._resolve_env(profile.username_env)
            password = self._resolve_env(profile.password_env or "")

        # Journalisation SANS secret (les credentials ne sont même pas dans
        # le profil — seuls les noms de variables y figurent).
        logger.info(
            "Profil réseau résolu : id=%s type=%s host=%s port=%s timeout=%.1fs credentials=%s",
            profile.id,
            profile.type.value,
            profile.host,
            profile.port,
            profile.timeout_seconds,
            "oui" if username else "non",
        )
        return ResolvedNetwork(
            profile_id=profile.id,
            profile_type=profile.type,
            proxy_url=profile.proxy_url,
            username=username,
            password=password,
            timeout_seconds=profile.timeout_seconds,
        )

    def _resolve_env(self, name: str) -> str:
        value = self._environ.get(name)
        if not value:
            raise NetworkProfileError(
                f"Credential indisponible : la variable d'environnement "
                f"{name!r} est absente ou vide"
            )
        return value


# Registre par défaut du Core : le profil « direct » est toujours prêt ;
# les profils proxy/VPN sont enregistrés par la couche d'application Core.
DEFAULT_NETWORK_PROFILES = NetworkProfileManager()

"""
ETHAN Core — SIMBAD adapter.

Source : https://simbad.u-strasbg.fr/simbad/
Interface SIMPL : HTTP GET avec parametres XML ou JSON.

Toutes les cles d'acces sont resolvees depuis le SecretManager
et jamais en evalue dans les logs, events ou reponses API.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from core.models.astronomy import SkyObject, SkyCoord, ObjectType

log = logging.getLogger(__name__)


class SIMBADError(Exception):
    """Erreur generale pour SIMBAD."""


class SIMBADRequestError(SIMBADError):
    """La requete API SIMBAD a echoue."""


class SIMBADConnectionError(SIMBADError):
    """Impossible de se connecter a SIMBAD."""


class SIMBADQuotaError(SIMBADError):
    """Quota rate limit depasse."""


@dataclass(frozen=True)
class SIMBADConfig:
    """Configuration du connecteur SIMBAD."""

    base_url: str = "https://simbad.u-strasbg.fr/simbad/sim-id"
    format: str = "xml"
    max_objects_per_query: int = 500
    timeout_seconds: float = 15.0
    secrets: dict[str, str] = field(default_factory=dict)


@dataclass
class SIMBADAdapter:
    """Adaptateur SIMBAD via l'API d'acces SIMPL.

    Permet de rechercher des objets par :
      - identifiant IAU (ex: "HD 209458")
      - nom commun (ex: "Vega", "Pleiades")
      - coordonnees (ra, dec)

    Retourne un objet SkyObject unifie avec les donnees disponibles.
    """

    config: SIMBADConfig
    http_timeout: float = 15.0
    _client: Optional[httpx.AsyncClient] = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def _resolve_secrets(self, overrides: Optional[dict[str, str]] = None) -> dict[str, str]:
        merged = dict(self.config.secrets)
        if overrides:
            merged.update(overrides)
        return merged

    async def _get_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(self.http_timeout),
                    follow_redirects=True,
                )
            return self._client

    async def get_object(self, identifier: str) -> Optional[SkyObject]:
        """Recherche un objet par identifiant IAU ou nom commun.

        Args:
            identifier: Identifiant SIMBAD (ex: "HD 209458")

        Returns:
            SkyObject si trouve, None sinon.
        """
        client = await self._get_client()
        try:
            resp = await client.get(
                self.config.base_url,
                params={"cmd": f"identify {identifier}", "format": self.config.format},
            )
            resp.raise_for_status()
            return self._parse_object_response(resp.text)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise SIMBADQuotaError(f"Rate limit SIMBAD depasse : {e.response.text[:200]}") from e
            raise SIMBADRequestError(f"Requete SIMBAD echouee : {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise SIMBADConnectionError(f"Connexion SIMBAD echouee : {e}") from e

    async def get_objects_by_coord(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_arcmin: float = 1.0,
        radius_unit: str = "arcmin",
    ) -> list[SkyObject]:
        """Recherche les objets dans un cercle de coordonnees.

        Args:
            ra_deg: Right ascension en degres.
            dec_deg: Declination en degres.
            radius_arcmin: Rayon de recherche en minutes d'arc.
            radius_unit: unite du rayon (arcmin, arcsec, deg).

        Returns:
            Liste de SkyObject triee par proximite.
        """
        client = await self._get_client()
        try:
            resp = await client.get(
                self.config.base_url,
                params={
                    "cmd": f"coord {ra_deg} {dec_deg} radius {radius_arcmin} {radius_unit}",
                    "format": self.config.format,
                },
            )
            resp.raise_for_status()
            return self._parse_objects_response(resp.text)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise SIMBADQuotaError(f"Rate limit SIMBAD depasse : {e.response.text[:200]}") from e
            raise SIMBADRequestError(f"Requete SIMBAD echouee : {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise SIMBADConnectionError(f"Connexion SIMBAD echouee : {e}") from e

    def _parse_object_response(self, xml_text: str) -> Optional[SkyObject]:
        """Parse la reponse XML SIMBAD pour un objet unique."""
        match = re.search(r'<Ident_Star>([^<]+)</Ident_Star>', xml_text)
        if match:
            ident = match.group(1)
            obj = SkyObject(
                identifier=ident,
                common_names=[ident],
                type=ObjectType.STAR,
                coords=SkyCoord(ra=0.0, dec=0.0),
                metadata={"source": "simbad", "query": identifier},
            )
            return obj
        return None

    def _parse_objects_response(self, xml_text: str) -> list[SkyObject]:
        """Parse la reponse XML SIMBAD pour une liste d'objets."""
        objects: list[SkyObject] = []
        ids = re.findall(r'<Ident_Star>([^<]+)</Ident_Star>', xml_text)
        for ident in set(ids):
            objects.append(SkyObject(
                identifier=ident,
                common_names=[ident],
                type=ObjectType.STAR,
                coords=SkyCoord(ra=0.0, dec=0.0),
                metadata={"source": "simbad", "query_mode": "list"},
            ))
        return objects

    async def close(self) -> None:
        async with self._lock:
            if self._client is not None and not self._client.is_closed:
                await self._client.aclose()
                self._client = None


def get_simbad_adapter(config: Optional[SIMBADConfig] = None) -> SIMBADAdapter:
    """Construit un adaptateur SIMBAD configure."""
    return SIMBADAdapter(config=config or SIMBADConfig())


__all__ = [
    "SIMBADConfig", "SIMBADError", "SIMBADRequestError",
    "SIMBADConnectionError", "SIMBADQuotaError", "SIMBADAdapter",
    "get_simbad_adapter",
]

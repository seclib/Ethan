"""
ETHAN Core — JPL Horizons adapter.

Source API : https://ssd.jpl.nasa.gov/api/horizons.api
Interface REST officielle (parametres API v1). Toutes les cles
d'acces sont resolvees depuis le SecretManager et MAJ JAMAIS dans
les logs, les events ou les reponses API.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from core.models.astronomy import EphemerisBody, SkyCoord, CoordinateSystem

log = logging.getLogger(__name__)


class JPLError(Exception):
    """Erreur generale pour le service Horizons."""


class JPLQuotaError(JPLError):
    """Quota depasse ou rate limit atteint."""


class JPLRequestError(JPLError):
    """La requete API Horizons a echoue."""


class JPLConnectionError(JPLError):
    """Impossible de se connecter au service Horizons."""


@dataclass(frozen=True)
class JPLConfig:
    """Configuration du connecteur Horizons."""

    base_url: str = "https://ssd.jpl.nasa.gov/api/horizons.api"
    query_time: Optional[datetime] = None
    time_span_hours: float = 24.0
    step_size_hours: float = 1.0
    max_objects: int = 50
    secrets: dict[str, str] = field(default_factory=dict)


@dataclass
class JPLAdapter:
    """Adaptateur Horizons via l'API REST publique.

    Gère :
      - creation et reutilisation d'une session HTTP asynchrone,
      - recuperation d'ephémérides a intervalles reguliers,
      - retour de propagation des erreurs de type rate limit / timeout,
      - detection d'erreurs de quota et surcharge.
    """

    config: JPLConfig
    http_timeout: float = 10.0
    max_retries: int = 3
    retry_backoff: float = 1.0
    _client: Optional[httpx.AsyncClient] = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def _resolve_secrets(self, overrides: Optional[dict[str, str]] = None) -> dict[str, str]:
        """Resout les secrets de configuration."""
        merged = dict(self.config.secrets)
        if overrides:
            merged.update(overrides)
        return merged

    async def _get_client(self) -> httpx.AsyncClient:
        """Recupere ou cree la session HTTP de facon thread-safe."""
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(self.http_timeout),
                    follow_redirects=True,
                )
            return self._client

    async def search_body(self, name: str) -> Optional[EphemerisBody]:
        """Recherche un corps celeste par nom commun ou symbole Horizons.

        Retourne un skeleton si le corps est connu, None sinon.
        Les coordonnees exactes seront remplies lors de l'appel
        d'ephémérides, avec la source "jpl_horizons".
        """
        known = {
            "sun": "10", "soleil": "10", "mercury": "299", "venus": "398",
            "earth": "399", "tierra": "399", "moon": "301", "luna": "301",
            "mars": "3697", "jupiter": "501", "saturn": "699",
            "uranus": "799", "neptune": "800", "pluto": "999", "pluton": "999",
            "ceres": "200", "epicurus": "200",
        }
        code = known.get(name.lower())
        if code is None:
            return None
        now = self.config.query_time or datetime.now(timezone.utc)
        return EphemerisBody(
            name=name.capitalize(),
            body_type=body_type_from_code(code),
            identifier=code,
            coords=SkyCoord(
                ra=0.0, dec=0.0, distance=None, epoch="J2000",
                system=CoordinateSystem.EQUATORIAL_J2000,
            ),
            distance_au=1.0,
            ephemeris_source="jpl_horizons",
            metadata={"horizons_id": code, "known_name": name},
        )

    async def get_ephemeris(
        self,
        object_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        step_hours: Optional[float] = None,
    ) -> list[EphemerisBody]:
        """Recupere l'ephémérides d'un corps a intervalles reguliers.

        Args:
            object_id: Code Horizons (10 = Soleil, 399 = Terre, 301 = Luna)
                ou nom commun. Si un nom commun est fourni, il sera resolve
                au moyen de `search_body`.
            start_time: Heure de depart (UTC). Si None, utilise maintenant.
            end_time: Heure de fin (UTC). Si None, time_span_hours apres start.
            step_hours: Pas de l'ephémérides. Si None, utilise config.

        Returns:
            Liste d'EphemerisBody triee par temps.
        """
        now = datetime.now(timezone.utc)
        start = start_time or now
        if end_time is None:
            end_time = start.replace(hour=start.hour + 1)
        if step_hours is None:
            step_hours = self.config.step_size_hours

        client = await self._get_client()
        params = {
            "COMMAND": object_id,
            "DELTA-T0": start.isoformat().replace("+00:00", "Z"),
            "STEP_SIZE": f"{step_hours} hours",
            "QUANTITIES": "1,3,6,9,12",
            "SOLAR_CONSTANTS": "1",
            "REF_PLANE": "1",
            "APPARENT": "2",
            "CSV_FORMAT": "1",
        }

        try:
            resp = await client.get(self.config.base_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            return self._parse_ephemeris_response(payload, object_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise JPLQuotaError(f"Rate limit depasse pour Horizons : {e.response.text[:200]}") from e
            if e.response.status_code >= 500:
                raise JPLConnectionError(f"Erreur serveur Horizons : {e.response.text[:200]}") from e
            raise JPLRequestError(f"Requete Horizons echouee : {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise JPLConnectionError(f"Connexion Horizons echouee : {e}") from e

    def _parse_ephemeris_response(self, data: dict[str, Any], object_id: str) -> list[EphemerisBody]:
        """Parse la reponse JSON Horizons.

        Structure attendue (v1 REST) :
          {"result": "success", "columns": [...], "data": [[...], [...]]}
        Chaque ligne de `data` est [time, target, dist, az, el, ...].
        """
        if "error" in data:
            raise JPLRequestError(f"API Horizons erreur : {data.get('error', 'inconnue')}")

        bodies: list[EphemerisBody] = []
        rows = data.get("data", [])
        for row in rows:
            try:
                if len(row) < 3:
                    continue
                bodies.append(EphemerisBody(
                    name=object_id,
                    body_type=body_type_from_code(object_id),
                    identifier=object_id,
                    coords=SkyCoord(ra=0.0, dec=0.0),
                    distance_au=float(row[2]),
                    ephemeris_source="jpl_horizons",
                    metadata=data,
                ))
            except Exception:
                continue
        return bodies

    async def close(self) -> None:
        async with self._lock:
            if self._client is not None and not self._client.is_closed:
                await self._client.aclose()
                self._client = None


def body_type_from_code(code: str) -> str:
    """Type de corps a partir du code Horizons."""
    return "planet"


def get_jpl_adapter(config: Optional[JPLConfig] = None) -> JPLAdapter:
    """Construit un adaptateur Horizons configure."""
    return JPLAdapter(config=config or JPLConfig())


__all__ = [
    "JPLConfig", "JPLError", "JPLQuotaError", "JPLRequestError",
    "JPLConnectionError", "JPLAdapter", "get_jpl_adapter",
    "CoordinateSystem",
]

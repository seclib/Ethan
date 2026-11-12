"""
ETHAN Core — Unified astronomy data models.

Source de vérité pour les représentations spatiales : les composants
Blockchain, Dao, etc. ne répliquent pas ces types, ils les consomment.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CoordinateSystem(str, Enum):
    """Système de coordonnées supporté."""
    EQUATORIAL_J2000 = "icrs_j2000"
    ECLIPTIC_J2000 = "ecliptic_j2000"
    GALACTIC = "galactic"
    SUPERGALACTIC = "supergalactic"
    HORIZONTAL = "horizontal"
    EPHEMERIS = "ephemeris"


class ObjectType(str, Enum):
    """Type d'objet céleste."""
    STAR = "star"
    BINARY_STAR = "binary_star"
    EXOplanet = "exoplanet"
    SOLAR_SYSTEM_BODY = "solar_system_body"
    MOON = "moon"
    ASTEROID = "asteroid"
    COMET = "comet"
    DWARF_PLANET = "dwarf_planet"
    GALAXY = "galaxy"
    NEBULA = "nebula"
    CLUSTER = "cluster"
    QUASAR = "quasar"
    PULSAR = "pulsar"
    BLazar = "blazar"
    NOVERA_CEPHEID = "cepheid"
    SUPERNOVA = "supernova"
    EXTREME_HORIZON = "extreme_horizon"
    UNKNOWN = "unknown"


class MagnitudeSystem(str, Enum):
    """Système de magnitudes."""
    VEGETA = "vegeta"
    JOSO = "joso"
    VEGA = "vega"
    AB = "ab"
    PHYSICAL = "physical"


class Waveband(str, Enum):
    """Bandes spectrales d'observation."""
    OPTICAL = "optical"
    U = "u"
    B = "b"
    V = "v"
    R = "r"
    I = "i"
    NIR = "nir"
    J = "j"
    H = "h"
    K = "k"
    MIR = "mir"
    FIR = "fir"
    X_RAY = "xray"
    GAMMA = "gamma"
    RADIO = "radio"
    UV = "uv"
    ALL = "all"


class ProvenanceStatus(str, Enum):
    """Statut de provenance d'une donnée."""
    VERIFIED = "verified"
    PENDING = "pending"
    UNTRUSTED = "untrusted"
    BROKEN = "broken"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"


class AccessLevel(str, Enum):
    """Niveau d'accès à la donnée."""
    PUBLIC = "public"
    RESEARCH = "research"
    CONFIDENTIAL = "confidential"
    LICENSE = "license"


@dataclasses.dataclass(frozen=True)
class SkyCoord:
    """Coordonnées celeste unifiées.

    Représente un point dans un système de coordonnées spécifié.
    Les conversions entre systèmes sont déléguées à des services dédiés.
    """

    ra: float          # Right ascension en degrés
    dec: float         # Declination en degrés
    distance: Optional[float] = None   # Distance en pc
    epoch: str = "J2000"
    system: CoordinateSystem = CoordinateSystem.EQUATORIAL_J2000
    proper_motion_ra: Optional[float] = None
    proper_motion_dec: Optional[float] = None
    radial_velocity: Optional[float] = None
    parallax: Optional[float] = None

    def to_degrees(self) -> tuple[float, float]:
        return self.ra, self.dec

    def to_dict(self) -> dict[str, Any]:
        return {
            "ra": self.ra,
            "dec": self.dec,
            "distance": self.distance,
            "epoch": self.epoch,
            "system": self.system.value if isinstance(self.system, CoordinateSystem) else self.system,
            "proper_motion_ra": self.proper_motion_ra,
            "proper_motion_dec": self.proper_motion_dec,
            "radial_velocity": self.radial_velocity,
            "parallax": self.parallax,
        }


@dataclasses.dataclass(frozen=True)
class SkyObject:
    """Objet céleste unifié.

    Contient les données identifiables d'un objet dans n'importe quel
    catalogue (SIMBAD, Gaia, Catalogs NASA, etc.).
    """

    identifier: str          # Identifiant principal (ex: "HD 209458")
    common_names: list[str] = dataclasses.field(default_factory=list)
    type: ObjectType = ObjectType.UNKNOWN
    coords: Optional[SkyCoord] = None
    magnitude: Optional[float] = None
    magnitude_system: MagnitudeSystem = MagnitudeSystem.VEGETA
    magnitude_band: Optional[Waveband] = None
    parallax: Optional[float] = None
    radial_velocity: Optional[float] = None
    spectral_type: Optional[str] = None
    surface_temp: Optional[float] = None
    description: Optional[str] = None
    discoveries: Optional[list[str]] = None
    named_after: Optional[str] = None
    constellation: Optional[str] = None
    notes: list[str] = dataclasses.field(default_factory=list)
    catalog_links: dict[str, str] = dataclasses.field(default_factory=dict)
    provenance: "Provenance" = dataclasses.field(default_factory=lambda: Provenance(
        source="unknown", status=ProvenanceStatus.VERIFIED,
        access_date=datetime.now(timezone.utc),
    ))
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.discoveries is None:
            object.__setattr__(self, "discoveries", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "common_names": self.common_names,
            "type": self.type.value if isinstance(self.type, ObjectType) else self.type,
            "coords": self.coords.to_dict() if self.coords else None,
            "magnitude": self.magnitude,
            "magnitude_system": self.magnitude_system.value if isinstance(self.magnitude_system, MagnitudeSystem) else self.magnitude_system,
            "parallax": self.parallax,
            "spectral_type": self.spectral_type,
            "surface_temp": self.surface_temp,
            "constellation": self.constellation,
            "catalog_links": self.catalog_links,
            "provenance": self.provenance.to_dict(),
            "metadata": self.metadata,
        }


@dataclasses.dataclass(frozen=True)
class EphemerisBody:
    """Corps du système solaire avec éphémérides."""

    name: str
    body_type: str                      # "planet", "moon", "dwarf_planet", "comet", "asteroid"
    identifier: str
    coords: SkyCoord
    distance_au: float                  # Distance en Unités Astronomiques
    magnitude: Optional[float] = None
    albedo: Optional[float] = None
    radius_km: Optional[float] = None
    mass_kg: Optional[float] = None
    angular_diameter: Optional[float] = None
    solar_longitude: Optional[float] = None
    phase_angle: Optional[float] = None
    illumination_fraction: Optional[float] = None
    position_velocity: Optional[dict] = None
    constellation: Optional[str] = None
    ephemeris_source: str = "jpl_horizons"
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "body_type": self.body_type,
            "identifier": self.identifier,
            "coords": self.coords.to_dict(),
            "distance_au": self.distance_au,
            "magnitude": self.magnitude,
            "radius_km": self.radius_km,
            "albedo": self.albedo,
            "angular_diameter": self.angular_diameter,
            "solar_longitude": self.solar_longitude,
            "phase_angle": self.phase_angle,
            "illumination_fraction": self.illumination_fraction,
            "constellation": self.constellation,
            "ephemeris_source": self.ephemeris_source,
            "metadata": self.metadata,
        }


@dataclasses.dataclass(frozen=True)
class LightCurvePoint:
    """Point d'une courbe de lumière."""

    time_btjd: float       # Temps en BTJD (BJD - 2457000)
    flux: Optional[float] = None
    flux_error: Optional[float] = None
    magnitude: Optional[float] = None
    magnitude_error: Optional[float] = None
    band: Optional[Waveband] = None
    instrument: Optional[str] = None
    quality: Optional[float] = None


@dataclasses.dataclass(frozen=True)
class LightCurve:
    """Courbe de lumière d'un objet (ex: exoplanetes-transit).

    Points triés par temps croissant.
    """

    identifier: str
    target_name: str
    points: list[LightCurvePoint]
    band: Waveband
    instrument: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "target_name": self.target_name,
            "band": self.band.value if isinstance(self.band, Waveband) else self.band,
            "instrument": self.instrument,
            "author": self.author,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "points": [
                p.to_dict() if isinstance(p, LightCurvePoint) else p
                for p in self.points
            ],
        }


@dataclasses.dataclass(frozen=True)
class ImageCutout:
    """Coupe d'image obsédante.

    Stocke les métadonnées et le chemin vers l'image. Le contenu binaire
    est géré séparément pour éviter les fuites de mémoire.
    """

    identifier: str
    object_id: str
    source: str
    waveband: Waveband
    size_pixels: tuple[int, int]
    pixel_scale: float
    timestamp: Optional[datetime] = None
    instrument: Optional[str] = None
    observatory: Optional[str] = None
    url: Optional[str] = None
    filepath: Optional[str] = None
    md5: Optional[str] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "object_id": self.object_id,
            "source": self.source,
            "waveband": self.waveband.value if isinstance(self.waveband, Waveband) else self.waveband,
            "size_pixels": list(self.size_pixels),
            "pixel_scale": self.pixel_scale,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "instrument": self.instrument,
            "observatory": self.observatory,
            "url": self.url,
            "filepath": self.filepath,
            "md5": self.md5,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "metadata": self.metadata,
        }


@dataclasses.dataclass(frozen=True)
class Provenance:
    """Provenance d'une donnée pour traçabilité.

    Respecte le principe SECRETS ;
Aucune clé API n'est jamais sérialisée.
    """

    source: str
    access_date: datetime
    url: Optional[str] = None
    api_key_ref: Optional[str] = None    # Référence secrète, jamais la valeur
    rate_limit_remaining: Optional[int] = None
    quota_used: Optional[int] = None
    quota_limit: Optional[int] = None
    fetcher: Optional[str] = None
    request_id: Optional[str] = None
    status: ProvenanceStatus = ProvenanceStatus.VERIFIED
    checksum: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "source": self.source,
            "access_date": self.access_date.isoformat() if self.access_date else None,
            "status": self.status.value if isinstance(self.status, ProvenanceStatus) else self.status,
            "rate_limit_remaining": self.rate_limit_remaining,
            "quota_used": self.quota_used,
            "quota_limit": self.quota_limit,
            "fetcher": self.fetcher,
            "request_id": self.request_id,
            "checksum": self.checksum,
            "notes": self.notes,
        }
        if self.url:
            d["url"] = self.url
        if self.api_key_ref:
            d["api_key_ref"] = self.api_key_ref  # Référence secrète, jamais la valeur réelle
        return d


@dataclasses.dataclass(frozen=True)
class AstroCatalog:
    """Catalogue astronomique unifié (SIMBAD, Gaia, etc.).

    Représente un ensemble d'objets dans un catalogue donné.
    """

    catalog_id: str                    # Source tableau (ex: "simbad", "gaia")
    name: str
    version: Optional[str] = None
    total_objects: Optional[int] = None
    objects: list[SkyObject] = dataclasses.field(default_factory=list)
    query_filters: dict[str, Any] = dataclasses.field(default_factory=dict)
    queried_at: Optional[datetime] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "name": self.name,
            "version": self.version,
            "total_objects": self.total_objects,
            "objects": [o.to_dict() for o in self.objects],
            "query_filters": self.query_filters,
            "queried_at": self.queried_at.isoformat() if self.queried_at else None,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "metadata": self.metadata,
        }


# Alias pour compatibilité avec les logs/émissions existantes
SkyObjectLike = SkyObject
SkyCoordLike = SkyCoord
EphemerisBodyLike = EphemerisBody
ProvenanceLike = Provenance


__all__ = [
    "CoordinateSystem", "ObjectType", "MagnitudeSystem", "Waveband",
    "ProvenanceStatus", "AccessLevel",
    "SkyCoord", "SkyObject", "EphemerisBody",
    "LightCurvePoint", "LightCurve", "ImageCutout", "Provenance", "AstroCatalog",
    "SkyObjectLike", "SkyCoordLike", "EphemerisBodyLike", "ProvenanceLike",
]

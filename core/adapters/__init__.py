"""
ETHAN Core — Adaptateurs d'integration externe.

Façade unique pour les services tiers :
  - JPL Horizons (ephemerides systeme solaire)
  - SIMBAD (catalogue stellaire/extragalactic)
  - NASA Exoplanet Archive (donnees exoplanetes)
  - ... (a venir)

Les consommateurs (Chat, Skills, Missions) ne connaissent
que l'interface `get_adapter` et ne preparent pas de
connexions HTTP directes.
"""

from __future__ import annotations

from typing import Optional

from core.adapters.jpl_horizons import JPLAdapter, JPLConfig, get_jpl_adapter
from core.adapters.simbad import SIMBADAdapter, SIMBADConfig, get_simbad_adapter

__all__ = [
    "JPLAdapter", "JPLConfig", "get_jpl_adapter",
    "SIMBADAdapter", "SIMBADConfig", "get_simbad_adapter",
]

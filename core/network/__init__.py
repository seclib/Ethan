"""ETHAN Core — Network Profiles (connexions Web Research).

Abstraction Core-only : les interfaces transmettent un identifiant de
profil ; le Core applique la configuration correspondante.
"""

from core.network.profiles import (
    DEFAULT_NETWORK_PROFILES,
    DEFAULT_TIMEOUT_SECONDS,
    DIRECT_PROFILE_ID,
    MAX_TIMEOUT_SECONDS,
    MIN_TIMEOUT_SECONDS,
    NetworkProfile,
    NetworkProfileError,
    NetworkProfileManager,
    NetworkProfileType,
    ResolvedNetwork,
)

__all__ = [
    "DEFAULT_NETWORK_PROFILES",
    "DEFAULT_TIMEOUT_SECONDS",
    "DIRECT_PROFILE_ID",
    "MAX_TIMEOUT_SECONDS",
    "MIN_TIMEOUT_SECONDS",
    "NetworkProfile",
    "NetworkProfileError",
    "NetworkProfileManager",
    "NetworkProfileType",
    "ResolvedNetwork",
]

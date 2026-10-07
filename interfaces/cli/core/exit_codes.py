"""ETHAN CLI — Exit codes, error vocabulary and HTTP mapping.

Source unique de vérité : `docs/specs/CLI_CONTRACT.md` §5 (codes figés) et
§4.3 (vocabulaire fermé des codes d'erreur machine).

Ces codes sont un CONTRAT PUBLIC : toute interface (CLI, WebUI, Desktop,
scripts CI) doit pouvoir les consommer. Ils ne sont donc jamais renumérotés —
seuls des codes non utilisés peuvent être réservés (§5).
"""

from __future__ import annotations

from enum import Enum, IntEnum


class ExitCode(IntEnum):
    """Exit codes stables du CLI ETHAN (contrat §5)."""

    SUCCESS = 0
    OPERATION_FAILED = 1
    USAGE = 2
    AUTH = 3
    FORBIDDEN = 4
    UNAVAILABLE = 5
    NOT_FOUND = 6
    TIMEOUT = 7
    CONFLICT = 8
    INTERNAL = 70
    INTERRUPTED = 130


class ErrorCode(str, Enum):
    """Vocabulaire fermé des codes d'erreur machine (contrat §4.3).

    Ce ne sont PAS des exit codes : ils qualifient l'erreur dans la charge
    utile JSON. La classe hérite de `str` pour permettre une comparaison
    directe avec les valeurs sérialisées du document JSON.
    """

    USAGE = "usage"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    CONFLICT = "conflict"
    OPERATION_FAILED = "operation_failed"
    INTERNAL = "internal"


#: Mapping HTTP Core → exit code (§5). Non listé = OPERATION_FAILED (1),
#: c'est-à-dire « le Core a répondu, l'opération a échoué ».
HTTP_STATUS_EXIT: dict[int, ExitCode] = {
    401: ExitCode.AUTH,
    403: ExitCode.FORBIDDEN,
    404: ExitCode.NOT_FOUND,
    409: ExitCode.CONFLICT,
    502: ExitCode.UNAVAILABLE,
    503: ExitCode.UNAVAILABLE,
    504: ExitCode.UNAVAILABLE,
}

#: Reverse mapping exit code → code d'erreur machine (§4.3).
_EXIT_ERROR_CODE: dict[ExitCode, str] = {
    ExitCode.OPERATION_FAILED: ErrorCode.OPERATION_FAILED,
    ExitCode.USAGE: ErrorCode.USAGE,
    ExitCode.AUTH: ErrorCode.UNAUTHORIZED,
    ExitCode.FORBIDDEN: ErrorCode.FORBIDDEN,
    ExitCode.UNAVAILABLE: ErrorCode.UNAVAILABLE,
    ExitCode.NOT_FOUND: ErrorCode.NOT_FOUND,
    ExitCode.TIMEOUT: ErrorCode.TIMEOUT,
    ExitCode.CONFLICT: ErrorCode.CONFLICT,
    ExitCode.INTERNAL: ErrorCode.INTERNAL,
    ExitCode.INTERRUPTED: ErrorCode.INTERNAL,
}


def exit_code_for_status(status: int) -> ExitCode:
    """Map an HTTP status code to its contract exit code (§5)."""
    return HTTP_STATUS_EXIT.get(status, ExitCode.OPERATION_FAILED)


def error_code_for_exit(exit_code: int) -> str:
    """Machine error code matching an exit code (§4.3)."""
    try:
        return _EXIT_ERROR_CODE[ExitCode(exit_code)]
    except (ValueError, KeyError):
        return ErrorCode.OPERATION_FAILED


def normalize_exit(code: int | ExitCode | None) -> int:
    """Coerce any handler return value into a valid contract exit code.

    Command handlers historically returned loose ints (or None). Anything that
    is not a known contract code collapses to SUCCESS (0) so that a legacy
    handler cannot accidentally leak an arbitrary value into scripts.
    """
    if code is None:
        return int(ExitCode.SUCCESS)
    try:
        return int(ExitCode(int(code)))
    except (TypeError, ValueError):
        return int(ExitCode.SUCCESS)

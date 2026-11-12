"""TerminalService — sessions PTY réelles, une seule source de vérité.

Conception (audit) :
- Le plugin `plugins/terminal` est un exécuteur ONE-SHOT à liste blanche : il
  renvoie stdout/stderr d'une commande et meurt. Ce n'est PAS un terminal.
- `interfaces/api/routers/realtime.py` ne fait que relayer NATS. Ce n'est pas
  un terminal non plus.
- Un terminal interactif exige un PTY (pseudo-terminal) et un flux
  bidirectionnel persistant. D'où ce service : il forke un vrai shell dans un
  PTY et expose stdin/stdout/stderr, Ctrl+C, resize et terminaison.

Sécurité (fail-closed, jamais d'escalade automatique) :
- Refus si le processus tourne en root (`geteuid()==0`) : le terminal ne
  fournit JAMAIS root/sudo par défaut.
- Environnement ASSaini : aucun secret (`ETHAN_TOKEN`, *_PASSWORD, *_KEY…) ne
  traverse dans la session.
- Répertoire de travail borné par `resolve_safe_path` (garde-fou Core déjà
  testé) ; repli sur `/workspace` si le cwd demandé est refusé.
- Aucune commande n'est exécutée par ce service : le shell décide. Les
  permissions ETHAN (RBAC, permission EXECUTE) sont vérifiées par l'API avant
  d'atteindre ce service — le Core n'invente pas d'autorisation.

Le Core reste la source de vérité : l'état (RUNNING/EXITED/…) et le `pid`
sont lus ici, jamais calculés par la WebUI.
"""

from __future__ import annotations

import errno
import fcntl
import logging
import os
import pwd
import select
import signal
import struct
import termios
import time
from pathlib import Path

from core.security.policy import resolve_safe_path
from core.terminal.types import (
    TerminalError,
    TerminalNotFound,
    TerminalSecurityError,
    TerminalSession,
    TerminalState,
    new_session_id,
)

logger = logging.getLogger(__name__)

#: Racine par défaut du terminal (cohérente avec le garde-fou Core).
DEFAULT_ROOT = "/workspace"

#: Taille du tampon de lecture PTY (octets). Suffisant pour la progression
#: d'une installation ; les gros volumes sont fragmentés par la couche WS.
READ_SIZE = 4096

#: Variables d'environnement jamais transmises à une session terminal.
#: Le terminal ne fournit pas d'accès arbitraire aux secrets (règle AGENTS.md).
SECRET_ENV_MARKERS = (
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "SECRET",
    "API_KEY",
    "APIKEY",
    "PRIVATE_KEY",
    "CREDENTIAL",
    "SESSION_SECRET",
    "JWT",
)


def _is_secret_env(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in SECRET_ENV_MARKERS)


def build_clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Environnement minimal et sans secret pour le shell enfant.

    On repart d'une base contenant seulement PATH/HOME/LANG/TERM, puis on
    ajoute les variables explicitement demandées par l'API. Aucun secret du
    processus parent ne fuite.
    """
    env: dict[str, str] = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "TERM", "SHELL", "USER"):
        value = os.environ.get(key)
        if value is not None and not _is_secret_env(key):
            env[key] = value
    env.setdefault("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
    env.setdefault("TERM", "xterm-256color")
    # Un terminal doit lire/écrire des couleurs : TERM + un size par défaut.
    env["ETHAN_TERMINAL"] = "1"
    for key, value in (extra or {}).items():
        env[key] = str(value)
    return env


def current_user() -> str:
    """Utilisateur effectif du service (jamais root — cf. `assert_not_root`)."""
    try:
        return pwd.getpwuid(os.geteuid()).pw_name
    except KeyError:  # pragma: no cover — UID sans entrée passwd (rare)
        return str(os.geteuid())


def hostname() -> str:
    try:
        return os.uname().nodename
    except Exception:  # noqa: BLE001 — un nom d'hôte n'est jamais critique
        return "localhost"


def assert_not_root() -> None:
    """Fail-closed : un terminal root est interdit par défaut.

    ETHAN ne fournit ni root, ni sudo, ni accès Docker illimité. Si le service
    tourne en root (conteneur mal configuré), on REFUSE d'ouvrir une session
    plutôt que d'exposer un shell root.
    """
    if os.geteuid() == 0:
        raise TerminalSecurityError(
            "refused: terminal sessions must not run as root",
            reason="geteuid()==0",
        )


def resolve_cwd(requested: str | None, root: str = DEFAULT_ROOT) -> str:
    """Résout le répertoire de travail dans la racine autorisée (fail-closed)."""
    base = Path(root)
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:  # noqa: BLE001 — racine non inscriptible : on replie
        base = Path(os.getcwd())
    candidate = requested or "."
    try:
        return resolve_safe_path(str(base / candidate), [str(base)])
    except Exception:  # noqa: BLE001 — chemin refusé : repli sur la racine
        logger.info("terminal: cwd %s hors périmètre, repli sur %s", candidate, base)
        return str(base)


def default_shell() -> str:
    """Shell de session : $SHELL si valide, sinon /bin/sh (jamais root -i)."""
    shell = os.environ.get("SHELL") or ""
    if shell and os.path.isfile(shell) and os.access(shell, os.X_OK):
        return shell
    return "/bin/sh"


class TerminalService:
    """Sessions PTY réelles : création, I/O, resize, signaux, nettoyage.

    Le service est un registre en mémoire : les sessions vivent dans le
    processus qui les a créées. Une session disparue après redémarrage de
    l'API n'est pas un bug — le processus PTY est mort avec elle, et le
    registre repart vide (aucune fuite : cf. `purge_dead` / `shutdown_all`).
    """

    def __init__(self, *, root: str = DEFAULT_ROOT, shell: str | None = None):
        self._root = root
        self._shell = shell or default_shell()
        self._sessions: dict[str, TerminalSession] = {}
        self._children: dict[str, int] = {}  # session_id -> pid

    # ── Création ─────────────────────────────────────────────────────────────

    def create(
        self,
        *,
        user: str,
        cwd: str | None = None,
        cols: int = 80,
        rows: int = 24,
    ) -> TerminalSession:
        """Ouvre une session PTY réelle.

        Fail-closed : refuse root. Le shell enfant est son propre chef de
        groupe de processus (`os.forkpty`), ce qui permet SIGINT/SIGTERM au
        groupe sans toucher au serveur.
        """
        assert_not_root()

        working_dir = resolve_cwd(cwd, self._root)
        cols = max(1, min(int(cols), 500))
        rows = max(1, min(int(rows), 500))

        env = build_clean_env({"HOME": working_dir, "PWD": working_dir, "USER": user})

        pid, fd = os.forkpty()
        if pid == 0:
            # ── Enfant — ne jamais revenir en Python ──────────────────────
            try:
                os.chdir(working_dir)
                os.execve(self._shell, [os.path.basename(self._shell)], env)
            except Exception:  # noqa: BLE001 — l'enfant ne peut pas "raise"
                os._exit(127)

        # ── Parent : configure la fenêtre du PTY ───────────────────────────
        self._set_winsize(fd, rows, cols)
        session = TerminalSession(
            id=new_session_id(),
            user=user,
            cwd=working_dir,
            pid=pid,
            cols=cols,
            rows=rows,
            hostname=hostname(),
            fd=fd,
        )
        self._sessions[session.id] = session
        self._children[session.id] = pid
        # Audit lifecycle : {id, user} uniquement — jamais de contenu PTY ni de
        # secret. Le contenu interactif n'est pas journalisable par design.
        logger.info(
            "terminal.session.created id=%s user=%s pid=%d cwd=%s",
            session.id,
            user,
            pid,
            working_dir,
        )
        return session

    # ── Accès ────────────────────────────────────────────────────────────────

    def get(self, session_id: str) -> TerminalSession:
        """Session par id, ou `TerminalNotFound` (l'interface peut re-ficher)."""
        session = self._sessions.get(session_id)
        if session is None:
            raise TerminalNotFound(f"unknown terminal session: {session_id}")
        return session

    def list_sessions(self) -> list[TerminalSession]:
        """Toutes les sessions, les mortes purgées au passage."""
        self.purge_dead()
        return list(self._sessions.values())

    # ── I/O ──────────────────────────────────────────────────────────────────

    def write(self, session_id: str, data: str) -> None:
        """stdin : écrit les octets saisis dans le PTY.

        Un Ctrl+C (`\x03`) transite par la ligne discipline du PTY, qui le
        convertit en SIGINT pour le groupe de processus — exactement comme
        dans un terminal réel, sans cas particulier côté serveur.
        """
        session = self.get(session_id)
        if session.state != TerminalState.RUNNING or session.fd is None:
            raise TerminalError(f"session {session_id} is not running", code="TERMINAL-CLOSED")
        payload = data.encode("utf-8", errors="replace")
        try:
            os.write(session.fd, payload)
        except OSError as exc:
            if exc.errno in (errno.EIO, errno.EBADF):
                # Le PTY se ferme quand l'enfant meurt : on marque la session.
                self._mark_exited(session)
                return
            raise
        session.touch()

    def read(self, session_id: str, size: int = READ_SIZE, timeout: float = 0.2) -> bytes:
        """stdout/stderr : lit les octets disponibles (non bloquant).

        Un PTY fusionne stdout et stderr dans un seul flux, comme un vrai
        terminal. Le read est non bloquant et borné : il ne retient jamais la
        boucle WebSocket.
        """
        session = self.get(session_id)
        if session.fd is None:
            return b""
        try:
            ready, _, _ = select.select([session.fd], [], [], timeout)
        except (OSError, ValueError):
            return b""
        if not ready:
            return b""
        try:
            chunk = os.read(session.fd, size)
        except OSError as exc:
            if exc.errno in (errno.EIO, errno.EBADF):
                # EIO sur un PTY = l'enfant a quitté.
                self._mark_exited(session)
                return b""
            raise
        if not chunk:
            self._mark_exited(session)
            return b""
        session.touch()
        return chunk

    # ── Contrôle ─────────────────────────────────────────────────────────────

    def resize(self, session_id: str, *, cols: int, rows: int) -> None:
        """Redimensionne le PTY (ioctl TIOCSWINSZ) — la fenêtre du terminal."""
        session = self.get(session_id)
        cols = max(1, min(int(cols), 500))
        rows = max(1, min(int(rows), 500))
        session.cols, session.rows = cols, rows
        if session.fd is not None:
            self._set_winsize(session.fd, rows, cols)
        session.touch()

    def interrupt(self, session_id: str) -> None:
        """Ctrl+C explicite : SIGINT au groupe de processus de la session."""
        self._signal(session_id, signal.SIGINT)
        # Audit lifecycle : un Stop explicite reste traçable sans contenu PTY.
        logger.info("terminal.session.interrupted id=%s", session_id)

    def terminate(self, session_id: str) -> TerminalSession:
        """Ferme une session : SIGTERM puis SIGKILL si le shell résiste."""
        session = self.get(session_id)
        if session.state == TerminalState.RUNNING:
            self._signal(session_id, signal.SIGTERM)
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                if self._reap(session_id, blocking=False) is not None:
                    break
                time.sleep(0.05)
            else:
                # SIGKILL ne peut pas être ignoré : on RÉCOLTE en bloquant,
                # sinon la méthode rendrait la main avec un enfant encore
                # vivant (SIGKILL est asynchrone côté noyau).
                self._signal(session_id, signal.SIGKILL, ignore_missing=True)
                self._reap(session_id, blocking=True)
        return self.close(session_id)

    def close(self, session_id: str) -> TerminalSession:
        """Nettoyage : ferme le FD, retire du registre, marque CLOSED."""
        session = self._sessions.get(session_id)
        if session is None:
            raise TerminalNotFound(f"unknown terminal session: {session_id}")
        if session.fd is not None:
            try:
                os.close(session.fd)
            except OSError:
                pass
            session.fd = None
        session.state = TerminalState.CLOSED
        self._children.pop(session_id, None)
        self._sessions.pop(session_id, None)
        # Audit lifecycle symétrique à la création : {id, user} uniquement.
        logger.info("terminal.session.closed id=%s user=%s", session.id, session.user)
        return session

    # ── Cycle de vie / fuite de processus ────────────────────────────────────

    def reap(self, session_id: str, *, blocking: bool = True) -> int | None:
        """Récolte le code de sortie de l'enfant (waitpid WNOHANG par défaut)."""
        return self._reap(session_id, blocking=blocking)

    def _reap(self, session_id: str, *, blocking: bool) -> int | None:
        pid = self._children.get(session_id)
        if pid is None:
            return None
        flags = 0 if blocking else os.WNOHANG
        try:
            waited, status = os.waitpid(pid, flags)
        except ChildProcessError:
            # Déjà récolté : on perd la trace, la session devient EXITED.
            self._children.pop(session_id, None)
            session = self._sessions.get(session_id)
            if session is not None:
                if session.exit_code is None:
                    session.exit_code = 0
                session.state = TerminalState.EXITED
                return session.exit_code
            return None
        except OSError:
            return None
        if waited == 0:  # non bloquant : l'enfant court encore
            return None
        self._children.pop(session_id, None)
        exit_code = os.waitstatus_to_exitcode(status)
        session = self._sessions.get(session_id)
        if session is not None:
            session.exit_code = exit_code
            session.state = TerminalState.EXITED
        return exit_code

    def _mark_exited(self, session: TerminalSession) -> None:
        """Marque EXITED quand le PTY signale la fin (EIO / lecture vide)."""
        if session.state != TerminalState.RUNNING:
            return
        session.state = TerminalState.EXITED
        if session.fd is not None:
            try:
                os.close(session.fd)
            except OSError:
                pass
            session.fd = None
        # Récolte le statut si l'enfant est déjà terminé.
        self._reap(session.id, blocking=False)
        self._children.pop(session.id, None)

    def purge_dead(self) -> list[str]:
        """Retire les sessions dont l'enfant a quitté (aucune fuite)."""
        for session_id, pid in list(self._children.items()):
            session = self._sessions.get(session_id)
            if session is None:
                self._children.pop(session_id, None)
                continue
            try:
                waited, _ = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                self._children.pop(session_id, None)
                session.state = TerminalState.EXITED
                continue
            except OSError:
                continue
            if waited == pid:  # l'enfant est mort
                self._children.pop(session_id, None)
                if session.fd is not None:
                    try:
                        os.close(session.fd)
                    except OSError:
                        pass
                    session.fd = None
                session.state = TerminalState.EXITED

        # Une session EXITED n'a plus de FD : elle ne sert plus à rien et son
        # enfant a été récolté — on la retire pour ne pas fuiter de l'état.
        for session_id, session in list(self._sessions.items()):
            if session.state == TerminalState.EXITED and session.fd is None:
                self._sessions.pop(session_id, None)
        return list(self._sessions)

    def shutdown_all(self) -> None:
        """Arrêt du service : tue toutes les sessions (aucun orphelin)."""
        for session_id in list(self._sessions):
            try:
                self.terminate(session_id)
            except TerminalError:
                continue

    # ── Interne ──────────────────────────────────────────────────────────────

    def _set_winsize(self, fd: int, rows: int, cols: int) -> None:
        """Applique la taille de fenêtre au PTY (fcntl.ioctl TIOCSWINSZ)."""
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        except (OSError, ValueError):
            # Un PTY qui refuse la taille reste utilisable : on l'ignore.
            logger.debug("terminal: TIOCSWINSZ refusé")

    def _signal(self, session_id: str, sig: int, *, ignore_missing: bool = False) -> None:
        """Envoie un signal au groupe de processus de la session."""
        session = self.get(session_id)
        try:
            os.killpg(os.getpgid(session.pid), sig)
        except (ProcessLookupError, PermissionError):
            if not ignore_missing:
                self._mark_exited(session)
        except OSError as exc:
            if not ignore_missing:
                raise TerminalError(
                    f"cannot signal session {session_id}: {exc}",
                    code="TERMINAL-SIGNAL",
                ) from exc


__all__ = [
    "DEFAULT_ROOT",
    "READ_SIZE",
    "SECRET_ENV_MARKERS",
    "TerminalService",
    "assert_not_root",
    "build_clean_env",
    "current_user",
    "default_shell",
    "hostname",
    "resolve_cwd",
]

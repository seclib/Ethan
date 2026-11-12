"""TUI plein écran ETHAN.

Architecture : boucle principale unique sur le thread principal, avec un
thread secondaire pour le flux SSE. Aucune logique métier ici : le TUI
projette les contrats Core (agents, modèles, outils, conversations, HROT)
et pilote l'interface.

Raccourcis clavier :
  Enter        envoyer le message
  Ctrl-C       annuler le flux / quitter si inactif
  Ctrl-D       quitter (si entrée vide)
  ↑/↓          historique / défilement
  PgUp/PgDn    défilement de la conversation
  Home/End     haut / bas de la conversation
  Tab          complétion des commandes slash
  Esc          fermer le panneau actif
"""

from __future__ import annotations

import queue
import signal
import sys
import threading
from dataclasses import dataclass, field
from io import StringIO
from typing import Callable

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from interfaces.cli.core.client import get_timeout
from interfaces.cli.core.context import get_context, parse_global_options, set_context
from interfaces.cli.tui.core_client import TuiCoreClient, run_stream_worker
from interfaces.cli.tui.models import (
    Agent,
    ApprovalItem,
    ChatSummary,
    ConnectionStatus,
    DoneEvent,
    ErrorEvent,
    PermissionRequestEvent,
    PermissionResolvedEvent,
    JSONValue,
    Keypress,
    KeyKind,
    Message,
    Model,
    PanelKind,
    Provider,
    StreamError,
    StreamEvent,
    Tool,
    ToolCallEvent,
    ToolCallView,
    ToolResultEvent,
    ContentEvent,
    ContentReplaceEvent,
)
from interfaces.cli.tui.terminal import Terminal

# ── Constantes ─────────────────────────────────────────────────────────

LLM_TIMEOUT = 120.0

HELP_LINES: tuple[str, ...] = (
    "Commandes slash :",
    "  /help                aide",
    "  /exit, /quit         quitter",
    "  /new, /reset         nouvelle conversation (Core)",
    "  /clear               vider l'affichage local",
    "  /sessions            liste et reprise des sessions Core",
    "  /session <id>        reprendre une session",
    "  /agents              liste et sélection des agents",
    "  /agent <id|nom>      sélectionner un agent",
    "  /models              liste et sélection des modèles",
    "  /model <id>          sélectionner un modèle",
    "  /providers           liste et sélection des providers",
    "  /provider <id>       sélectionner un provider",
    "  /tools               liste et sélection des outils",
    "  /status              état du Core",
    "  /approve             demandes d'autorisation HROT en attente",
    "  /history             historique local de la conversation",
    "  /retry               recharger agents/modèles/outils",
    "Raccourcis : ↑/↓ historique, PgUp/PgDn défilement, Tab focus sidebar, Ctrl+K palette, e expand tool, Esc ferme.",
)


@dataclass
class SlashCommand:
    name: str
    description: str
    handler: Callable[["TuiApp", list[str]], None]


@dataclass
class TuiState:
    """État mutable du TUI (pas de logique métier, uniquement l'interface)."""

    connection: ConnectionStatus = ConnectionStatus.CONNECTING
    error: str | None = None
    agents: list[Agent] = field(default_factory=list)
    models: list[Model] = field(default_factory=list)
    providers: list[Provider] = field(default_factory=list)
    tools: list[Tool] = field(default_factory=list)
    chats: list[ChatSummary] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    current_chat_id: str | None = None
    selected_agent_id: str | None = None
    selected_provider_id: str | None = None
    selected_model_id: str | None = None
    selected_tool_ids: list[str] = field(default_factory=list)
    input: str = ""
    cursor: int = 0
    history: list[str] = field(default_factory=list)
    history_index: int = -1
    stream_queue: queue.Queue[StreamEvent | StreamError | None] | None = None
    stream_thread: threading.Thread | None = None
    streaming: bool = False
    stream_abort: threading.Event = field(default_factory=threading.Event)
    scroll_offset: int = 0
    sidebar_focus: bool = False
    sidebar_index: int = 0
    pending_permission: PermissionRequestEvent | None = None
    active_panel: PanelKind = PanelKind.NONE
    panel_index: int = 0
    panel_message: str | None = None
    approvals: list[ApprovalItem] = field(default_factory=list)
    last_status: str = ""


class TuiApp:
    """Application TUI principale."""

    def __init__(
        self,
        *,
        client: TuiCoreClient | None = None,
        console: Console | None = None,
        terminal: Terminal | None = None,
        session_id: str | None = None,
        color: bool = True,
    ) -> None:
        self.state = TuiState()
        self._terminal = terminal if terminal is not None else Terminal()
        self._color = color
        self._client = client if client is not None else TuiCoreClient(
            timeout=get_timeout(default=LLM_TIMEOUT),
            abort_event=self.state.stream_abort,
        )
        # Le client partage l'event d'arrêt avec l'état.
        self._client._abort = self.state.stream_abort
        self._console = console if console is not None else Console(
            force_terminal=True, no_color=not color, color_system="truecolor"
        )
        self._session_id = session_id
        self._running = False
        self._slash_commands: dict[str, SlashCommand] = {}
        self._register_slash_commands()
        self._resize_flag = False
        self._last_size: tuple[int, int] = (80, 24)

    # ── Slash commands ─────────────────────────────────────────────────

    def _register_slash_commands(self) -> None:
        commands: list[SlashCommand] = [
            SlashCommand("help", "Aide", self._cmd_help),
            SlashCommand("exit", "Quitter", self._cmd_exit),
            SlashCommand("quit", "Quitter", self._cmd_exit),
            SlashCommand("new", "Nouvelle conversation", self._cmd_new),
            SlashCommand("reset", "Nouvelle conversation", self._cmd_new),
            SlashCommand("clear", "Vider l'affichage", self._cmd_clear),
            SlashCommand("sessions", "Liste des sessions", self._cmd_sessions),
            SlashCommand("session", "Reprendre une session", self._cmd_session),
            SlashCommand("agents", "Liste des agents", self._cmd_agents),
            SlashCommand("agent", "Sélectionner un agent", self._cmd_agent),
            SlashCommand("models", "Liste des modèles", self._cmd_models),
            SlashCommand("model", "Sélectionner un modèle", self._cmd_model),
            SlashCommand("providers", "Liste des providers", self._cmd_providers),
            SlashCommand("provider", "Sélectionner un provider", self._cmd_provider),
            SlashCommand("tools", "Liste des outils", self._cmd_tools),
            SlashCommand("status", "État du Core", self._cmd_status),
            SlashCommand("approve", "Autorisations HROT", self._cmd_approve),
            SlashCommand("history", "Historique", self._cmd_history),
            SlashCommand("retry", "Recharger", self._cmd_retry),
        ]
        for cmd in commands:
            self._slash_commands[cmd.name] = cmd

    # ── Cycle de vie ───────────────────────────────────────────────────

    def run(self) -> int:
        """Lance le TUI. Retourne un code de sortie."""
        if not self._terminal.is_interactive:
            sys.stderr.write("Le TUI ETHAN nécessite un terminal interactif.\n")
            return 2

        self._running = True
        # SIGWINCH
        try:
            signal.signal(signal.SIGWINCH, lambda *_: setattr(self, "_resize_flag", True))
        except (AttributeError, ValueError):
            pass

        raw_ok = self._terminal.enter_raw()
        if not raw_ok:
            sys.stderr.write("Impossible de passer le terminal en mode brut.\n")
            return 2

        try:
            # Écran alternatif
            sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H")
            sys.stdout.flush()
            cols, rows = self._terminal.size()
            if cols <= 0 or rows <= 0:
                cols, rows = 80, 24
            # Rendu de chargement immédiat pour éviter un écran vide pendant
            # les appels Core initiaux.
            try:
                from rich.text import Text as RText
                loading = RText()
                loading.append("  ● ETHAN TUI — chargement…", style="bold cyan")
                loading.append("\\n\\n  Connexion au Core…", style="dim")
                # Pad to full screen
                lines = ["  ● ETHAN TUI — chargement…", "", "  Connexion au Core…"]
                while len(lines) < rows:
                    lines.append("")
                sys.stdout.write("\n".join(lines))
                sys.stdout.flush()
            except Exception:  # noqa: BLE001
                pass
            self._load_initial()
            self._main_loop()
        except KeyboardInterrupt:
            pass
        except Exception as exc:  # noqa: BLE001 — ne jamais sortir silencieusement
            sys.stderr.write(f"\nTUI error: {exc}\n")
            raise
        finally:
            self._cleanup()
        return 0

    def _cleanup(self) -> None:
        self._running = False
        if self.state.streaming:
            self.state.stream_abort.set()
            if self.state.stream_thread is not None and self.state.stream_thread.is_alive():
                self.state.stream_thread.join(timeout=2.0)
        self._terminal.restore()
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()

    def _load_initial(self) -> None:
        self.state.connection = ConnectionStatus.CONNECTING
        self.state.error = None
        try:
            self.state.agents = self._client.list_agents()
            self.state.models = self._client.list_models()
            self.state.providers = self._client.list_providers()
            self.state.tools = self._client.list_tools()
            self.state.chats = self._client.list_chats()
            self.state.connection = ConnectionStatus.CONNECTED
        except Exception as err:  # noqa: BLE001 — le TUI doit survivre
            self.state.connection = ConnectionStatus.ERROR
            self.state.error = str(err)

        # Sélection initiale
        if self._session_id:
            self._resume_chat(self._session_id)
        elif self.state.chats:
            latest = max(self.state.chats, key=lambda c: c.updated_at or c.created_at)
            self._resume_chat(latest.id)

        # Provider/modèle par défaut
        if self.state.selected_provider_id is None:
            for provider in self.state.providers:
                if provider.is_default:
                    self.state.selected_provider_id = provider.id
                    if not self.state.selected_model_id:
                        self.state.selected_model_id = provider.default_model
                    break

    def _main_loop(self) -> None:
        while self._running:
            if self._resize_flag:
                self._resize_flag = False
                self._last_size = self._terminal.size()
            cols, rows = self._last_size if self._last_size != (0, 0) else self._terminal.size()
            if cols < 100:
                self.state.sidebar_focus = False
            if cols <= 0 or rows <= 0:
                cols, rows = 80, 24
            self._last_size = (cols, rows)

            # Drain la file de flux
            self._drain_stream_queue()

            # Rendu
            frame = self._render(cols, rows)
            self._paint(frame)

            # Lecture clavier
            kp = self._terminal.read_keypress(0.05)
            if kp is not None:
                self._handle_keypress(kp)

    def _drain_stream_queue(self) -> None:
        if self.state.stream_queue is None:
            return
        while True:
            try:
                item = self.state.stream_queue.get_nowait()
            except queue.Empty:
                break
            if item is None:
                # Fin de flux
                self.state.streaming = False
                self.state.stream_queue = None
                self.state.stream_thread = None
                # Marquer le dernier message assistant comme terminé
                for msg in reversed(self.state.messages):
                    if msg.role == "assistant" and msg.status == "pending":
                        msg.status = "done"
                        msg.touch()
                        break
                break
            if isinstance(item, StreamError):
                self.state.streaming = False
                self.state.error = item.message
                self.state.connection = (
                    ConnectionStatus.ERROR if item.exit_code == 5 else self.state.connection
                )
                # Marquer le message assistant comme erreur
                for msg in reversed(self.state.messages):
                    if msg.role == "assistant" and msg.status == "pending":
                        msg.status = "error"
                        msg.touch()
                        break
                # Ajouter un message système
                self.state.messages.append(Message(role="system", content=f"Erreur : {item.message}", status="error"))
                self.state.messages[-1].touch()
                continue
            self._apply_event(item)

    # ── Gestion clavier ────────────────────────────────────────────────

    _SIDEBAR_SECTIONS = ("SESSION", "AGENT", "MODEL", "PROVIDER", "TOOLS", "HROT")
    _SIDEBAR_COMMANDS = {
        "SESSION": "/sessions",
        "AGENT": "/agents",
        "MODEL": "/models",
        "PROVIDER": "/providers",
        "TOOLS": "/tools",
        "HROT": "/approve",
    }

    def _sidebar_available(self, cols: int) -> bool:
        return cols >= 100

    def _handle_keypress(self, kp: Keypress) -> None:
        # Demande d'autorisation HROT en cours : a=autoriser, r=refuser.
        if self.state.pending_permission is not None:
            if kp.kind == KeyKind.CHARACTER and kp.text in ("a", "A", "o", "O", "y", "Y"):
                self._resolve_pending_permission(True)
                return
            if kp.kind == KeyKind.CHARACTER and kp.text in ("r", "R", "n", "N"):
                self._resolve_pending_permission(False)
                return
            if kp.kind == KeyKind.ENTER:
                self._resolve_pending_permission(True)
                return
            if kp.kind == KeyKind.ESCAPE:
                self._resolve_pending_permission(False)
                return
            return

        # Focus barre latérale (uniquement si largeur suffisante).
        if self.state.sidebar_focus:
            if kp.kind == KeyKind.ESCAPE or (kp.kind == KeyKind.CHARACTER and kp.text in ("q", "Q")):
                self.state.sidebar_focus = False
                return
            if kp.kind == KeyKind.TAB and not (kp.kind == KeyKind.CHARACTER):
                pass
            if kp.kind == KeyKind.UP:
                if self.state.sidebar_index > 0:
                    self.state.sidebar_index -= 1
                return
            if kp.kind == KeyKind.DOWN:
                if self.state.sidebar_index < len(self._SIDEBAR_SECTIONS) - 1:
                    self.state.sidebar_index += 1
                return
            if kp.kind == KeyKind.ENTER:
                cmd = self._SIDEBAR_COMMANDS[self._SIDEBAR_SECTIONS[self.state.sidebar_index]]
                self._execute_slash(cmd)
                self.state.sidebar_focus = False
                return
            if kp.kind == KeyKind.TAB:
                # Shift+Tab approximé : Tab seul sort du focus sidebar.
                self.state.sidebar_focus = False
                return
            # Ignorer les autres touches en mode focus sidebar.
            return

        # Ctrl+K : palette de commandes.
        if kp.kind == KeyKind.CTRL_K:
            self.state.active_panel = PanelKind.PALETTE
            self.state.panel_index = 0
            self.state.panel_message = None
            return

        # 'e' : développer/réduire le dernier appel d'outil.
        if kp.kind == KeyKind.CHARACTER and kp.text in ("e", "E") and not self.state.input and self.state.active_panel == PanelKind.NONE:
            for msg in reversed(self.state.messages):
                if msg.role == "assistant" and msg.tool_calls:
                    tc = msg.tool_calls[-1]
                    tc.expanded = not tc.expanded
                    msg.touch()
                    break
            return

        # Tab donne le focus à la sidebar si disponible.
        if kp.kind == KeyKind.TAB:
            # On ne déclenche le focus sidebar que si l'entrée est vide,
            # pour ne pas casser l'autocomplétion.
            if not self.state.input and self._sidebar_available(self._terminal.size()[0]):
                self.state.sidebar_focus = True
                self.state.sidebar_index = 0
                return
            self._autocomplete()
            return

        # Panneau actif : navigation locale
        if self.state.active_panel != PanelKind.NONE:
            self._handle_panel_key(kp)
            return

        if kp.kind == KeyKind.CTRL_C:
            if self.state.streaming:
                self.state.stream_abort.set()
                self._client.abort_stream()
            else:
                self._running = False
            return
        if kp.kind == KeyKind.CTRL_D:
            if not self.state.input:
                self._running = False
            return
        if kp.kind == KeyKind.CTRL_L:
            self._cmd_clear([])
            return
        if kp.kind == KeyKind.NEWLINE:
            # Insert newline at cursor
            self.state.input = (
                self.state.input[: self.state.cursor] + "\\n" + self.state.input[self.state.cursor:]
            )
            self.state.cursor += 1
            return

        if kp.kind == KeyKind.ENTER:
            self._submit()
            return
        if kp.kind == KeyKind.BACKSPACE:
            if self.state.cursor > 0:
                self.state.input = self.state.input[: self.state.cursor - 1] + self.state.input[self.state.cursor:]
                self.state.cursor -= 1
            return
        if kp.kind == KeyKind.DELETE:
            if self.state.cursor < len(self.state.input):
                self.state.input = self.state.input[: self.state.cursor] + self.state.input[self.state.cursor + 1:]
            return
        if kp.kind == KeyKind.LEFT:
            if self.state.cursor > 0:
                self.state.cursor -= 1
            return
        if kp.kind == KeyKind.RIGHT:
            if self.state.cursor < len(self.state.input):
                self.state.cursor += 1
            return
        if kp.kind == KeyKind.HOME or kp.kind == KeyKind.CTRL_A:
            # Start of current line
            line_start = self.state.input.rfind("\\n", 0, self.state.cursor) + 1
            self.state.cursor = line_start
            return
        if kp.kind == KeyKind.END or kp.kind == KeyKind.CTRL_E:
            # End of current line
            line_end = self.state.input.find("\\n", self.state.cursor)
            if line_end < 0:
                line_end = len(self.state.input)
            self.state.cursor = line_end
            return
        if kp.kind == KeyKind.CTRL_U:
            self.state.input = self.state.input[self.state.cursor:]
            self.state.cursor = 0
            return
        if kp.kind == KeyKind.CTRL_K:
            self.state.input = self.state.input[: self.state.cursor]
            return
        if kp.kind == KeyKind.CTRL_W:
            # Supprime le mot précédent
            left = self.state.input[: self.state.cursor]
            right = self.state.input[self.state.cursor:]
            i = len(left)
            while i > 0 and left[i - 1].isspace():
                i -= 1
            while i > 0 and not left[i - 1].isspace():
                i -= 1
            self.state.input = left[:i] + right
            self.state.cursor = i
            return
        if kp.kind == KeyKind.UP:
            # Multi-line: move cursor up if not on first line
            if "\\n" in self.state.input:
                before = self.state.input[: self.state.cursor]
                lines_before = before.split("\\n")
                if len(lines_before) > 1:
                    # Move to previous line, same column
                    col = len(lines_before[-1])
                    prev_line = lines_before[-2]
                    new_col = min(col, len(prev_line))
                    # Calculate new cursor position
                    new_cursor = self.state.cursor - len(lines_before[-1]) - 1 - (len(prev_line) - new_col)
                    if new_cursor >= 0:
                        self.state.cursor = new_cursor
                    return
            # History navigation
            if self.state.history and self.state.history_index < len(self.state.history) - 1:
                self.state.history_index += 1
                self.state.input = self.state.history[-(self.state.history_index + 1)]
                self.state.cursor = len(self.state.input)
            else:
                self.state.scroll_offset += 1
            return
        if kp.kind == KeyKind.DOWN:
            if "\\n" in self.state.input:
                before = self.state.input[: self.state.cursor]
                after = self.state.input[self.state.cursor:]
                lines_before = before.split("\\n")
                lines_after = after.split("\\n")
                if len(lines_after) > 1:
                    # Move to next line, same column
                    col = len(lines_before[-1])
                    next_line = lines_after[1] if len(lines_after) > 1 else ""
                    new_col = min(col, len(next_line))
                    new_cursor = self.state.cursor + len(lines_before[-1].split("\\n")[-1]) + 1 + new_col
                    # Simpler: move to next line start + new_col
                    current_line_start = self.state.input.rfind("\\n", 0, self.state.cursor) + 1
                    col_in_line = self.state.cursor - current_line_start
                    next_line_start = self.state.input.find("\\n", self.state.cursor)
                    if next_line_start >= 0:
                        next_line_start += 1
                        next_line_end = self.state.input.find("\\n", next_line_start)
                        if next_line_end < 0:
                            next_line_end = len(self.state.input)
                        next_line_len = next_line_end - next_line_start
                        new_col = min(col_in_line, next_line_len)
                        self.state.cursor = next_line_start + new_col
                    return
            if self.state.history_index > 0:
                self.state.history_index -= 1
                self.state.input = self.state.history[-(self.state.history_index + 1)] if self.state.history_index >= 0 else ""
                self.state.cursor = len(self.state.input)
            elif self.state.history_index == 0:
                self.state.history_index = -1
                self.state.input = ""
                self.state.cursor = 0
            else:
                if self.state.scroll_offset > 0:
                    self.state.scroll_offset -= 1
            return
        if kp.kind == KeyKind.PAGE_UP:
            self.state.scroll_offset += 5
            return
        if kp.kind == KeyKind.PAGE_DOWN:
            if self.state.scroll_offset > 0:
                self.state.scroll_offset = max(0, self.state.scroll_offset - 5)
            return
        if kp.kind == KeyKind.TAB:
            self._autocomplete()
            return
        if kp.kind == KeyKind.CHARACTER:
            self.state.input = (
                self.state.input[: self.state.cursor] + kp.text + self.state.input[self.state.cursor:]
            )
            self.state.cursor += len(kp.text)
            return

    def _handle_panel_key(self, kp: Keypress) -> None:
        panel = self.state.active_panel
        if kp.kind == KeyKind.ESCAPE or (kp.kind == KeyKind.CHARACTER and kp.text in ("q", "Q")):
            self.state.active_panel = PanelKind.NONE
            self.state.panel_message = None
            return
        if panel in (PanelKind.SESSIONS, PanelKind.AGENTS, PanelKind.MODELS, PanelKind.PROVIDERS, PanelKind.TOOLS):
            items = self._panel_items()
            if kp.kind == KeyKind.UP:
                if items and self.state.panel_index > 0:
                    self.state.panel_index -= 1
            elif kp.kind == KeyKind.DOWN:
                if items and self.state.panel_index < len(items) - 1:
                    self.state.panel_index += 1
            elif kp.kind == KeyKind.ENTER:
                self._panel_activate()
            return
        if panel == PanelKind.PALETTE:
            cmds = list(self._slash_commands.keys())
            if kp.kind == KeyKind.UP and self.state.panel_index > 0:
                self.state.panel_index -= 1
            elif kp.kind == KeyKind.DOWN and self.state.panel_index < len(cmds) - 1:
                self.state.panel_index += 1
            elif kp.kind == KeyKind.ENTER:
                if self.state.panel_index < len(cmds):
                    name = cmds[self.state.panel_index]
                    self.state.active_panel = PanelKind.NONE
                    self._execute_slash("/" + name)
            return
        if panel == PanelKind.APPROVALS:
            items = self.state.approvals
            if kp.kind == KeyKind.UP and self.state.panel_index > 0:
                self.state.panel_index -= 1
            elif kp.kind == KeyKind.DOWN and self.state.panel_index < len(items) - 1:
                self.state.panel_index += 1
            elif kp.kind == KeyKind.CHARACTER and kp.text in ("a", "A"):
                self._approve_selected(True)
            elif kp.kind == KeyKind.CHARACTER and kp.text in ("r", "R"):
                self._approve_selected(False)
            return

    def _panel_items(self) -> list[object]:
        if self.state.active_panel == PanelKind.SESSIONS:
            return self.state.chats
        if self.state.active_panel == PanelKind.AGENTS:
            return self.state.agents
        if self.state.active_panel == PanelKind.MODELS:
            return self.state.models
        if self.state.active_panel == PanelKind.PROVIDERS:
            return self.state.providers
        if self.state.active_panel == PanelKind.TOOLS:
            return self.state.tools
        return []

    def _panel_activate(self) -> None:
        items = self._panel_items()
        if not items or self.state.panel_index >= len(items):
            return
        item = items[self.state.panel_index]
        if self.state.active_panel == PanelKind.SESSIONS:
            if isinstance(item, ChatSummary):
                self._resume_chat(item.id)
                self.state.active_panel = PanelKind.NONE
        elif self.state.active_panel == PanelKind.AGENTS:
            if isinstance(item, Agent):
                self.state.selected_agent_id = item.id
                self.state.selected_provider_id = item.provider or self.state.selected_provider_id
                if item.model:
                    self.state.selected_model_id = item.model
                self.state.active_panel = PanelKind.NONE
        elif self.state.active_panel == PanelKind.MODELS:
            if isinstance(item, Model):
                self.state.selected_model_id = item.id
                # Met à jour le provider si trouvé
                for provider in self.state.providers:
                    if item.id in provider.models or item.provider == provider.id:
                        self.state.selected_provider_id = provider.id
                        break
                if not self.state.selected_provider_id:
                    self.state.selected_provider_id = item.provider
                self.state.active_panel = PanelKind.NONE
        elif self.state.active_panel == PanelKind.PROVIDERS:
            if isinstance(item, Provider):
                self.state.selected_provider_id = item.id
                self.state.selected_agent_id = None
                self.state.active_panel = PanelKind.NONE
        elif self.state.active_panel == PanelKind.TOOLS:
            if isinstance(item, Tool):
                if item.id in self.state.selected_tool_ids:
                    self.state.selected_tool_ids.remove(item.id)
                else:
                    self.state.selected_tool_ids.append(item.id)
                # Pas de fermeture : permet la sélection multiple

    # ── Soumission ─────────────────────────────────────────────────────

    def _submit(self) -> None:
        text = self.state.input.strip()
        self.state.input = ""
        self.state.cursor = 0
        self.state.history_index = -1
        if not text:
            return

        # Slash command
        if text.startswith("/"):
            if len(self.state.history) == 0 or self.state.history[-1] != text:
                self.state.history.append(text)
            self._execute_slash(text)
            return

        # Historique
        if len(self.state.history) == 0 or self.state.history[-1] != text:
            self.state.history.append(text)

        # Pas de Core : erreur
        if self.state.connection == ConnectionStatus.ERROR and not self._client.is_available():
            self.state.messages.append(Message(role="system", content="Core indisponible. /retry pour recharger.", status="error"))
            self.state.messages[-1].touch()
            return

        # Message utilisateur
        user_msg = Message(role="user", content=text, status="done")
        self.state.messages.append(user_msg)
        user_msg.touch()

        # Message assistant en attente
        assistant_msg = Message(role="assistant", content="", status="pending")
        self.state.messages.append(assistant_msg)
        assistant_msg.touch()

        # Payload
        payload: dict[str, JSONValue] = {"message": text}
        if self.state.current_chat_id:
            payload["chat_id"] = self.state.current_chat_id
        if self.state.selected_agent_id:
            payload["agent_id"] = self.state.selected_agent_id
        if self.state.selected_provider_id:
            payload["provider_id"] = self.state.selected_provider_id
        if self.state.selected_model_id:
            payload["model"] = self.state.selected_model_id
        if self.state.selected_tool_ids and not self.state.selected_agent_id:
            payload["tool_ids"] = list(self.state.selected_tool_ids)

        self.state.stream_abort.clear()
        self._client.reset_abort()
        q: queue.Queue[StreamEvent | StreamError | None] = queue.Queue()
        self.state.stream_queue = q
        self.state.streaming = True
        thread = threading.Thread(
            target=run_stream_worker,
            args=(self._client, payload, q),
            daemon=True,
        )
        self.state.stream_thread = thread
        thread.start()

    def _apply_event(self, event: StreamEvent) -> None:
        # Trouver le dernier message assistant pending
        assistant_msg: Message | None = None
        for msg in reversed(self.state.messages):
            if msg.role == "assistant" and msg.status == "pending":
                assistant_msg = msg
                break

        if isinstance(event, ContentEvent):
            if assistant_msg is not None:
                assistant_msg.content += event.content
                assistant_msg.touch()
            if event.chat_id and not self.state.current_chat_id:
                self.state.current_chat_id = event.chat_id
                # Mettre à jour le dernier message
                if assistant_msg is not None:
                    assistant_msg.chat_id = event.chat_id
            return
        if isinstance(event, ContentReplaceEvent):
            if assistant_msg is not None:
                assistant_msg.content = event.content
                assistant_msg.touch()
            if event.chat_id:
                self.state.current_chat_id = event.chat_id
                if assistant_msg is not None:
                    assistant_msg.chat_id = event.chat_id
            return
        if isinstance(event, ToolCallEvent):
            if assistant_msg is not None:
                import json as _json
                import time as _time

                try:
                    params_str = _json.dumps(event.params, ensure_ascii=False)
                except Exception:  # noqa: BLE001
                    params_str = str(event.params)
                assistant_msg.tool_calls.append(
                    ToolCallView(name=event.tool, params=params_str, status="pending", started_at=_time.time())
                )
                assistant_msg.touch()
            return
        if isinstance(event, ToolResultEvent):
            if assistant_msg is not None:
                import time as _time
                for tc in reversed(assistant_msg.tool_calls):
                    if tc.name == event.tool and tc.status == "pending":
                        tc.status = event.status
                        tc.output = event.output
                        tc.ended_at = _time.time()
                        break
                assistant_msg.touch()
            return
        if isinstance(event, PermissionRequestEvent):
            self.state.pending_permission = event
            return
        if isinstance(event, PermissionResolvedEvent):
            self.state.pending_permission = None
            return
        if isinstance(event, DoneEvent):
            if event.chat_id:
                self.state.current_chat_id = event.chat_id
            if assistant_msg is not None:
                assistant_msg.status = "done"
                assistant_msg.message_id = event.message_id
                assistant_msg.chat_id = event.chat_id or assistant_msg.chat_id
                assistant_msg.touch()
            # Rafraîchir la liste des chats
            try:
                self.state.chats = self._client.list_chats()
            except Exception:  # noqa: BLE001
                pass
            return
        if isinstance(event, ErrorEvent):
            if assistant_msg is not None:
                assistant_msg.status = "error"
                assistant_msg.touch()
            self.state.messages.append(Message(role="system", content=f"Erreur : {event.error}", status="error"))
            self.state.messages[-1].touch()
            return

    # ── Slash commands ─────────────────────────────────────────────────

    def _execute_slash(self, text: str) -> None:
        parts = text[1:].split()
        name = parts[0].lower() if parts else ""
        args = parts[1:]
        cmd = self._slash_commands.get(name)
        if cmd is None:
            self.state.messages.append(Message(role="system", content=f"Commande inconnue : /{name}. /help pour la liste.", status="error"))
            self.state.messages[-1].touch()
            return
        try:
            cmd.handler(args)
        except Exception as err:  # noqa: BLE001
            self.state.messages.append(Message(role="system", content=f"Erreur /{name} : {err}", status="error"))
            self.state.messages[-1].touch()

    def _cmd_help(self, args: list[str]) -> None:
        self.state.active_panel = PanelKind.HELP
        self.state.panel_index = 0
        self.state.panel_message = None

    def _cmd_exit(self, args: list[str]) -> None:
        self._running = False

    def _cmd_new(self, args: list[str]) -> None:
        self.state.current_chat_id = None
        self.state.messages = []
        self.state.messages.append(Message(role="system", content="Nouvelle conversation (Core).", status="done"))
        self.state.messages[-1].touch()

    def _cmd_clear(self, args: list[str]) -> None:
        self.state.messages = []
        self.state.scroll_offset = 0

    def _cmd_sessions(self, args: list[str]) -> None:
        try:
            self.state.chats = self._client.list_chats()
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.SESSIONS
        self.state.panel_index = 0

    def _cmd_session(self, args: list[str]) -> None:
        if not args:
            self.state.messages.append(Message(role="system", content="Usage : /session <id>", status="error"))
            self.state.messages[-1].touch()
            return
        self._resume_chat(args[0])

    def _resume_chat(self, chat_id: str) -> None:
        try:
            msgs = self._client.get_chat_messages(chat_id)
        except Exception as err:  # noqa: BLE001
            self.state.messages.append(Message(role="system", content=f"Impossible de reprendre {chat_id} : {err}", status="error"))
            self.state.messages[-1].touch()
            return
        self.state.current_chat_id = chat_id
        self.state.messages = []
        for cm in msgs:
            role = cm.role if cm.role in ("user", "assistant", "system") else "assistant"
            m = Message(role=role, content=cm.content, status=cm.status or "done", chat_id=chat_id, message_id=cm.id, metadata={})
            self.state.messages.append(m)
            m.touch()
        if not self.state.messages:
            self.state.messages.append(Message(role="system", content=f"Session {chat_id[:8]}… chargée.", status="done"))
            self.state.messages[-1].touch()
        self.state.scroll_offset = 0

    def _cmd_agents(self, args: list[str]) -> None:
        try:
            self.state.agents = self._client.list_agents()
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.AGENTS
        self.state.panel_index = 0

    def _cmd_agent(self, args: list[str]) -> None:
        if not args:
            self.state.messages.append(Message(role="system", content="Usage : /agent <id|nom>", status="error"))
            self.state.messages[-1].touch()
            return
        query = args[0].lower()
        target: Agent | None = None
        for agent in self.state.agents:
            if agent.id == args[0] or agent.id.lower().startswith(query) or agent.name.lower() == query:
                target = agent
                break
        if target is None:
            # Recharger au cas où
            try:
                self.state.agents = self._client.list_agents()
            except Exception:  # noqa: BLE001
                pass
            for agent in self.state.agents:
                if agent.id == args[0] or agent.name.lower() == query:
                    target = agent
                    break
        if target is None:
            self.state.messages.append(Message(role="system", content=f"Agent introuvable : {args[0]}", status="error"))
            self.state.messages[-1].touch()
            return
        self.state.selected_agent_id = target.id
        if target.provider:
            self.state.selected_provider_id = target.provider
        if target.model:
            self.state.selected_model_id = target.model
        self.state.messages.append(Message(role="system", content=f"Agent sélectionné : {target.name} ({target.id[:8]}…)", status="done"))
        self.state.messages[-1].touch()

    def _cmd_models(self, args: list[str]) -> None:
        try:
            self.state.models = self._client.list_models()
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.MODELS
        self.state.panel_index = 0

    def _cmd_model(self, args: list[str]) -> None:
        if not args:
            self.state.messages.append(Message(role="system", content="Usage : /model <id>", status="error"))
            self.state.messages[-1].touch()
            return
        model_id = args[0]
        model = None
        for m in self.state.models:
            if m.id == model_id:
                model = m
                break
        if model is None:
            try:
                self.state.models = self._client.list_models()
            except Exception:  # noqa: BLE001
                pass
            for m in self.state.models:
                if m.id == model_id:
                    model = m
                    break
        if model is None:
            self.state.messages.append(Message(role="system", content=f"Modèle introuvable : {model_id}", status="error"))
            self.state.messages[-1].touch()
            return
        self.state.selected_model_id = model.id
        if model.provider:
            self.state.selected_provider_id = model.provider
        self.state.messages.append(Message(role="system", content=f"Modèle sélectionné : {model.id}", status="done"))
        self.state.messages[-1].touch()

    def _cmd_providers(self, args: list[str]) -> None:
        try:
            self.state.providers = self._client.list_providers()
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.PROVIDERS
        self.state.panel_index = 0

    def _cmd_provider(self, args: list[str]) -> None:
        if not args:
            self.state.messages.append(Message(role="system", content="Usage : /provider <id>", status="error"))
            self.state.messages[-1].touch()
            return
        provider_id = args[0]
        provider = None
        for p in self.state.providers:
            if p.id == provider_id:
                provider = p
                break
        if provider is None:
            try:
                self.state.providers = self._client.list_providers()
            except Exception:  # noqa: BLE001
                pass
            for p in self.state.providers:
                if p.id == provider_id:
                    provider = p
                    break
        if provider is None:
            self.state.messages.append(Message(role="system", content=f"Provider introuvable : {provider_id}", status="error"))
            self.state.messages[-1].touch()
            return
        self.state.selected_provider_id = provider.id
        self.state.selected_agent_id = None
        self.state.messages.append(Message(role="system", content=f"Provider sélectionné : {provider.id}", status="done"))
        self.state.messages[-1].touch()

    def _cmd_tools(self, args: list[str]) -> None:
        try:
            self.state.tools = self._client.list_tools()
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.TOOLS
        self.state.panel_index = 0

    def _cmd_status(self, args: list[str]) -> None:
        try:
            state = self._client.get_state()
            self.state.last_status = str(state)
            self.state.connection = ConnectionStatus.CONNECTED
        except Exception as err:  # noqa: BLE001
            self.state.connection = ConnectionStatus.ERROR
            self.state.error = str(err)
            self.state.last_status = str(err)
        self.state.active_panel = PanelKind.STATUS
        self.state.panel_index = 0

    def _cmd_approve(self, args: list[str]) -> None:
        try:
            approvals = self._client.list_pending_approvals()
            hrot = self._client.list_pending_hrot()
            all_items = approvals + hrot
            self.state.approvals = all_items
        except Exception as err:  # noqa: BLE001
            self.state.panel_message = f"Erreur : {err}"
            return
        self.state.active_panel = PanelKind.APPROVALS
        self.state.panel_index = 0

    def _approve_selected(self, approved: bool) -> None:
        items = self.state.approvals
        if not items or self.state.panel_index >= len(items):
            return
        item = items[self.state.panel_index]
        reason = "approved via ethan cli tui" if approved else "rejected via ethan cli tui"
        ok = False
        if item.kind == "approval":
            ok = self._client.resolve_approval(item.id, approved, reason)
        else:
            ok = self._client.resolve_hrot(item.id, approved, reason)
        if ok:
            self.state.approvals.pop(self.state.panel_index)
            if self.state.panel_index >= len(self.state.approvals) and self.state.panel_index > 0:
                self.state.panel_index -= 1
            self.state.panel_message = f"{'Approuvé' if approved else 'Rejeté'} : {item.id}"
        else:
            self.state.panel_message = f"Échec de la résolution : {item.id}"

    def _resolve_pending_permission(self, approved: bool) -> None:
        perm = self.state.pending_permission
        if perm is None:
            return
        self.state.pending_permission = None
        reason = "approved via ethan tui" if approved else "rejected via ethan tui"
        # Résolution en thread pour ne pas bloquer la boucle principale ;
        # le flux SSE côté Core est débloqué par cet appel.
        def _worker() -> None:
            try:
                self._client.resolve_approval(perm.request_id, approved, reason)
            except Exception:  # noqa: BLE001
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_history(self, args: list[str]) -> None:
        self.state.messages.append(Message(role="system", content="Historique local :", status="done"))
        for m in self.state.messages[:-1]:
            self.state.messages[-1].content += f"\n  [{m.role}] {m.content[:80]}"
        self.state.messages[-1].touch()

    def _cmd_retry(self, args: list[str]) -> None:
        self._load_initial()

    def _autocomplete(self) -> None:
        # Complétion des commandes slash
        if not self.state.input.startswith("/"):
            return
        prefix = self.state.input[1:]
        matches = [name for name in self._slash_commands if name.startswith(prefix)]
        if len(matches) == 1:
            self.state.input = "/" + matches[0] + " "
            self.state.cursor = len(self.state.input)
        elif len(matches) > 1:
            self.state.panel_message = "  ".join("/" + m for m in matches)

    # ── Rendu ──────────────────────────────────────────────────────────

    def _render(self, cols: int, rows: int) -> str:
        console = self._console
        console.width = cols
        console.height = rows

        header = self._render_header(cols)
        input_panel = self._render_input(cols)
        status_line = self._render_status(cols)

        body_height = max(4, rows - 1 - 3 - 1)  # header 1 ligne, input 3, status 1

        if cols >= 100:
            sidebar_width = 34
            conv_width = cols - sidebar_width
            sidebar = self._render_sidebar_panel(sidebar_width, body_height)
        else:
            conv_width = cols
            sidebar = None

        conv_panel = self._render_conversation_panel(conv_width, body_height)

        from rich.layout import Layout as RLayout

        layout = RLayout()
        layout.split_column(
            RLayout(header, name="header", size=3),
            RLayout(name="body", ratio=1),
            RLayout(input_panel, name="input", size=3),
            RLayout(status_line, name="status", size=1),
        )
        if sidebar is not None:
            layout["body"].split_row(
                RLayout(conv_panel, name="conv", ratio=1),
                RLayout(sidebar, name="sidebar", size=34),
            )
        else:
            layout["body"].update(conv_panel)

        with console.capture() as capture:
            console.print(layout)
        frame = capture.get()
        lines = frame.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        if len(lines) < rows:
            lines += [""] * (rows - len(lines))
        lines = lines[:rows]
        return "\n".join(lines)

    def _render_conversation_panel(self, cols: int, height: int) -> object:
        from rich.text import Text as RText
        from rich.console import Group as RGroup

        if self.state.pending_permission is not None:
            perm = self.state.pending_permission
            lines = [
                RText(""),
                RText("  ⚠ Autorisation HROT requise", style="bold red"),
                RText(f"    Outil : {perm.tool}", style="bold"),
                RText(f"    Raison : {perm.reason}", style="dim"),
                RText(f"    Request : {perm.request_id}", style="dim"),
                RText(""),
                RText("    [a]utoriser  [r]efuser  (Enter=autoriser, Esc=refuser)", style="cyan"),
                RText(""),
            ]
            if len(lines) < height:
                lines = lines + [RText("")] * (height - len(lines))
            lines = lines[:height]
            return RGroup(*lines)

        if self.state.active_panel != PanelKind.NONE:
            return self._render_panel(cols, height)

        lines = self._conversation_lines(cols)
        total = len(lines)
        visible = height
        if total <= visible:
            start = 0
        else:
            start = max(0, total - visible - self.state.scroll_offset)
        window = lines[start : start + visible]
        if len(window) < visible:
            window = [RText("")] * (visible - len(window)) + window
        return RGroup(*window)

    def _render_sidebar_panel(self, width: int, height: int) -> object:
        from rich.panel import Panel as RPanel
        from rich.text import Text as RText
        from rich.console import Group as RGroup

        lines = []

        # Identité visuelle : nom sobre, sans logo ni ASCII art
        lines.append(RText("  Ethan", style="bold cyan"))
        lines.append(RText(""))

        def section(title: str, content: list, focused: bool = False) -> None:
            marker = ">" if focused else " "
            style = "bold reverse" if focused else "bold cyan"
            lines.append(RText(f"{marker} {title}", style=style))
            for c in content:
                lines.append(c)

        chat = self.state.current_chat_id or "nouvelle"
        if len(chat) > 12:
            chat = chat[:8] + "..."
        title = "-"
        for c in self.state.chats:
            if c.id == self.state.current_chat_id:
                title = c.title[:18]
                break
        # Recent sessions list (max 4)
        recent = self.state.chats[:4]
        session_lines = [
            RText(f"  actif: {chat}  msgs: {len(self.state.messages)}"),
            RText(f"  titre: {title}"),
        ]
        if len(recent) > 1:
            session_lines.append(RText("  --- recent ---", style="dim"))
            for c in recent:
                marker = ">" if c.id == self.state.current_chat_id else " "
                session_lines.append(RText(f"  {marker} {c.id[:8]} {c.title[:14]}", style="dim" if c.id != self.state.current_chat_id else "bold"))
        session_lines.append(RText("  /new /sessions", style="dim"))
        section("SESSION", session_lines, focused=(self.state.sidebar_focus and self.state.sidebar_index == 0))

        agent_name = "-"
        if self.state.selected_agent_id:
            for a in self.state.agents:
                if a.id == self.state.selected_agent_id:
                    agent_name = a.name
                    break
            else:
                agent_name = self.state.selected_agent_id[:8]
        section("AGENT", [
            RText(f"  actif: {agent_name}  ({len(self.state.agents)})"),
            RText("  /agents", style="dim"),
        ], focused=(self.state.sidebar_focus and self.state.sidebar_index == 1))

        model = self.state.selected_model_id or "auto"
        section("MODEL", [
            RText(f"  actif: {model[:20]}  ({len(self.state.models)})"),
            RText("  /models", style="dim"),
        ], focused=(self.state.sidebar_focus and self.state.sidebar_index == 2))

        provider = self.state.selected_provider_id or "auto"
        prov_status = "-"
        for p in self.state.providers:
            if p.id == provider:
                prov_status = p.status or "-"
                break
        section("PROVIDER", [
            RText(f"  actif: {provider}  ({prov_status})"),
            RText(f"  dispo: {len(self.state.providers)}  /providers", style="dim"),
        ], focused=(self.state.sidebar_focus and self.state.sidebar_index == 3))

        n_tools = len(self.state.tools)
        n_selected = len(self.state.selected_tool_ids)
        section("TOOLS", [
            RText(f"  dispo: {n_tools}  sel: {n_selected}"),
            RText("  /tools", style="dim"),
        ], focused=(self.state.sidebar_focus and self.state.sidebar_index == 4))

        n_pending = len(self.state.approvals) + (1 if self.state.pending_permission else 0)
        hrot_status = "decision requise" if self.state.pending_permission else ("en attente" if n_pending else "aucune")
        section("HROT", [
            RText(f"  en attente: {n_pending}  {hrot_status}", style="red" if self.state.pending_permission else "dim"),
            RText("  /approve", style="dim"),
        ], focused=(self.state.sidebar_focus and self.state.sidebar_index == 5))

        if len(lines) < height:
            lines = lines + [RText("")] * (height - len(lines))
        lines = lines[:height]
        return RPanel(RGroup(*lines), title="ETHAN", border_style="cyan", width=width, height=height)

    def _render_header(self, cols: int) -> object:
        from rich.text import Text as RText
        agent_name = "—"
        if self.state.selected_agent_id:
            for agent in self.state.agents:
                if agent.id == self.state.selected_agent_id:
                    agent_name = agent.name
                    break
            else:
                agent_name = self.state.selected_agent_id[:8]
        model = self.state.selected_model_id or "auto"
        provider = self.state.selected_provider_id or "auto"
        session = (self.state.current_chat_id or "nouvelle")
        if len(session) > 12:
            session = session[:8] + "…"
        status = "●" if self.state.connection == ConnectionStatus.CONNECTED else "○"
        if self.state.connection == ConnectionStatus.ERROR:
            status = "✗"
        text = RText()
        text.append(f" {status} ETHAN TUI", style="bold cyan")
        text.append(f"  │  agent: {agent_name}", style="dim")
        text.append(f"  │  model: {model}", style="dim")
        text.append(f"  │  provider: {provider}", style="dim")
        text.append(f"  │  session: {session}", style="dim")
        if self.state.error:
            text.append(f"  │  err: {self.state.error[:30]}", style="red")
        if len(text.plain) < cols:
            text.append(" " * (cols - len(text.plain)))
        return text

    def _render_body(self, cols: int, rows: int) -> list[object]:
        # body_height : on réserve header(3) + input(3) + status(1)
        body_height = max(4, rows - 5)
        if self.state.active_panel != PanelKind.NONE:
            return [self._render_panel(cols, body_height)]
        # Conversation
        lines = self._conversation_lines(cols)
        total = len(lines)
        visible = body_height
        # scroll_offset en lignes depuis le bas
        if total <= visible:
            start = 0
        else:
            start = max(0, total - visible - self.state.scroll_offset)
        window = lines[start : start + visible]
        # Pad
        if len(window) < visible:
            window = [Text("")] * (visible - len(window)) + window
        return window

    def _conversation_lines(self, cols: int) -> list[Text]:
        lines: list[Text] = []
        if not self.state.messages:
            lines.append(Text("  Bienvenue dans ETHAN TUI. /help pour les commandes, /retry pour (re)charger.", style="dim"))
            lines.append(Text(""))
            return lines
        for msg in self.state.messages:
            if msg.role == "user":
                lines.append(Text("▸ vous", style="bold cyan"))
                for cl in msg.content.split("\\n"):
                    lines.append(Text(f"  {cl}", style="cyan"))
            elif msg.role == "assistant":
                if msg.content:
                    # Rendu Markdown via console temporaire
                    md = Markdown(msg.content)
                    buf = StringIO()
                    c = Console(file=buf, force_terminal=True, width=max(20, cols - 2), no_color=not self._color, color_system="truecolor" if self._color else None)
                    c.print(md)
                    for raw_line in buf.getvalue().split("\n"):
                        lines.append(Text(raw_line))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        status = tc.status or "pending"
                        icon = {"success": "✓", "rejected": "✗", "failed": "✗", "timeout": "⏱", "pending": "…", "stopped": "■"}.get(status, "·")
                        style = "green" if status == "success" else ("red" if status in ("rejected", "failed") else "yellow")
                        # Durée (mesurée côté client, réelle)
                        dur = ""
                        if tc.ended_at > tc.started_at > 0:
                            dur = f"  {tc.ended_at - tc.started_at:.1f}s"
                        toggle = "[-]" if tc.expanded else "[+]"
                        lines.append(Text(f"  ▶ {tc.name}  {icon} {status}{dur}  {toggle}", style=style))
                        if tc.expanded:
                            lines.append(Text(f"    params: {tc.params}", style="dim"))
                            if tc.output:
                                out = tc.output
                                if len(out) > 500:
                                    out = out[:500] + "…"
                                for ol in out.split("\n")[:8]:
                                    lines.append(Text(f"    → {ol}", style="dim"))
                            if tc.status in ("rejected", "failed", "timeout") and tc.output:
                                lines.append(Text(f"    ✗ {tc.output[:200]}", style="red"))
                if msg.status == "pending" and not msg.content and not msg.tool_calls:
                    lines.append(Text("  …", style="dim"))
            else:
                lines.append(Text(f"  · {msg.content}", style="dim"))
            lines.append(Text(""))

        # Permission HROT inline (si en attente)
        if self.state.pending_permission is not None:
            perm = self.state.pending_permission
            lines.append(Text(""))
            lines.append(Text("  ⚠ Autorisation HROT requise", style="bold red"))
            lines.append(Text(f"    Outil : {perm.tool}", style="bold"))
            lines.append(Text(f"    Raison : {perm.reason}", style="dim"))
            lines.append(Text(f"    Request : {perm.request_id}", style="dim"))
            lines.append(Text(""))
            lines.append(Text("    [a]utoriser  [r]efuser  (Enter=autoriser, Esc=refuser)", style="cyan"))
            lines.append(Text(""))

        return lines

    def _render_panel(self, cols: int, body_height: int) -> object:
        # Retourne un Panel qui occupe body_height lignes.
        kind = self.state.active_panel
        if kind == PanelKind.HELP:
            content = "\n".join(HELP_LINES)
            return Panel(Text(content), title="Aide", border_style="cyan", height=body_height)
        if kind == PanelKind.SESSIONS:
            table = Table(title="Sessions (Enter pour reprendre, Esc pour fermer)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=12)
            table.add_column("Titre", width=40)
            table.add_column("Mis à jour", width=20)
            for idx, chat in enumerate(self.state.chats):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", chat.id[:8], chat.title[:40], chat.updated_at[:19])
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="cyan", height=body_height)
        if kind == PanelKind.AGENTS:
            table = Table(title="Agents (Enter pour sélectionner)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=12)
            table.add_column("Nom", width=24)
            table.add_column("Modèle", width=24)
            table.add_column("Provider", width=14)
            for idx, agent in enumerate(self.state.agents):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", agent.id[:8], agent.name[:24], agent.model[:24], agent.provider[:14])
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="cyan", height=body_height)
        if kind == PanelKind.MODELS:
            table = Table(title="Modèles (Enter pour sélectionner)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=40)
            table.add_column("Provider", width=14)
            table.add_column("Contexte", width=10)
            for idx, model in enumerate(self.state.models):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", model.id[:40], model.provider[:14], str(model.context_length))
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="cyan", height=body_height)
        if kind == PanelKind.PROVIDERS:
            table = Table(title="Providers (Enter pour sélectionner)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=16)
            table.add_column("Nom", width=20)
            table.add_column("Statut", width=12)
            table.add_column("Défaut", width=8)
            for idx, provider in enumerate(self.state.providers):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", provider.id[:16], provider.name[:20], provider.status[:12], "oui" if provider.is_default else "")
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="cyan", height=body_height)
        if kind == PanelKind.TOOLS:
            table = Table(title="Outils (Enter pour sélectionner/désélectionner)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=28)
            table.add_column("Nom", width=20)
            table.add_column("Catégorie", width=12)
            table.add_column("Risque", width=10)
            table.add_column("Sél.", width=6)
            for idx, tool in enumerate(self.state.tools):
                marker = ">" if idx == self.state.panel_index else " "
                selected = "✓" if tool.id in self.state.selected_tool_ids else " "
                table.add_row(f"{marker}{idx}", tool.id[:28], tool.name[:20], tool.category[:12], tool.risk_level[:10], selected)
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="cyan", height=body_height)
        if kind == PanelKind.APPROVALS:
            table = Table(title="Autorisations HROT en attente (a=approuver, r=rejeter)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("ID", width=16)
            table.add_column("Type", width=10)
            table.add_column("Catégorie", width=16)
            table.add_column("Titre", width=32)
            table.add_column("Expire", width=20)
            for idx, item in enumerate(self.state.approvals):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", item.id[:16], item.kind, item.category[:16], item.title[:32], item.expires_at[:19])
            if self.state.panel_message:
                table.caption = self.state.panel_message
            return Panel(table, border_style="red", height=body_height)
        if kind == PanelKind.STATUS:
            content = self.state.last_status or "Aucune donnée."
            return Panel(Text(content[:4000]), title="État Core", border_style="cyan", height=body_height)
        if kind == PanelKind.PALETTE:
            from rich.table import Table as RTable
            table = RTable(title="Palette de commandes (Enter pour exécuter, Esc pour fermer)", show_header=True, header_style="bold")
            table.add_column("#", width=4)
            table.add_column("Commande", width=16)
            table.add_column("Description", width=40)
            for idx, (name, cmd) in enumerate(self._slash_commands.items()):
                marker = ">" if idx == self.state.panel_index else " "
                table.add_row(f"{marker}{idx}", f"/{name}", cmd.description)
            return Panel(table, border_style="magenta", height=body_height)
        return Panel(Text(""), height=body_height)

    def _render_input(self, cols: int) -> object:
        from rich.panel import Panel as RPanel
        from rich.text import Text as RText

        text = self.state.input
        cursor = self.state.cursor
        max_lines = 5
        width = max(10, cols - 4)

        if not text:
            rendered = RText("Message ETHAN… (Entrée pour envoyer, Ctrl+J nouvelle ligne, /help)", style="dim")
            return RPanel(rendered, title="composer", border_style="green", height=3)

        lines = text.split("\n")
        before_cursor = text[:cursor]
        cursor_line_idx = before_cursor.count("\n")
        cursor_col = len(before_cursor.split("\n")[-1])

        if len(lines) > max_lines:
            start_line = len(lines) - max_lines
            lines = lines[start_line:]
            cursor_line_idx = cursor_line_idx - start_line
            if cursor_line_idx < 0:
                cursor_line_idx = 0

        rendered = RText()
        for i, line in enumerate(lines):
            if i > 0:
                rendered.append("\n")
            if len(line) > width:
                if i == cursor_line_idx:
                    start_col = max(0, cursor_col - width // 2)
                    end_col = start_col + width
                    if end_col > len(line):
                        end_col = len(line)
                        start_col = max(0, end_col - width)
                    visible = line[start_col:end_col]
                    if start_col > 0:
                        rendered.append("…", style="dim")
                    cpos = cursor_col - start_col
                    if cpos < 0:
                        cpos = 0
                    if cpos > len(visible):
                        cpos = len(visible)
                    rendered.append(visible[:cpos])
                    rendered.append("█", style="reverse")
                    rendered.append(visible[cpos:])
                    if end_col < len(line):
                        rendered.append("…", style="dim")
                else:
                    rendered.append(line[:width - 1] + "…" if len(line) > width else line)
            else:
                if i == cursor_line_idx:
                    rendered.append(line[:cursor_col])
                    rendered.append("█", style="reverse")
                    rendered.append(line[cursor_col:])
                else:
                    rendered.append(line)

        height = min(max_lines + 2, max(3, len(text.split("\n")) + 2))
        title = "composer"
        if "\n" in text:
            title = f"composer ({text.count(chr(10)) + 1} lignes)"
        return RPanel(rendered, title=title, border_style="green", height=height)

    def _render_status(self, cols: int) -> Text:
        conn = "● connecté" if self.state.connection == ConnectionStatus.CONNECTED else "○ déconnecté"
        if self.state.connection == ConnectionStatus.ERROR:
            conn = "✗ erreur"
        agent = self.state.selected_agent_id[:8] if self.state.selected_agent_id else "—"
        model = self.state.selected_model_id or "auto"
        chat = (self.state.current_chat_id[:8] + "…") if self.state.current_chat_id else "nouvelle"
        stream = "streaming…" if self.state.streaming else "prêt"
        msg = f" {conn}  │  agent {agent}  │  model {model}  │  session {chat}  │  {stream}  │  /help"
        if self.state.error and not self.state.streaming:
            msg += f"  │  {self.state.error[:40]}"
        text = Text(msg, style="reverse")
        # Pad to cols
        if len(msg) < cols:
            text.append(" " * (cols - len(msg)))
        return text

    def _paint(self, frame: str) -> None:
        sys.stdout.write("\x1b[H" + frame)
        sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du TUI."""
    args = list(sys.argv[1:] if argv is None else argv)

    # Aide / version
    if "--help" in args or "-h" in args:
        sys.stdout.write(
            "ETHAN TUI — interface plein écran.\n"
            "Usage: ethan tui [--api-url URL] [--timeout SEC] [--session ID] [--no-color]\n"
            "       ethan cli  (sans arguments)\n"
        )
        return 0
    if "--version" in args or "-V" in args:
        from interfaces.cli._version import __version__

        sys.stdout.write(f"ETHAN TUI v{__version__}\n")
        return 0

    # Séparer les options globales des options TUI
    global_args: list[str] = []
    session_id: str | None = None
    remaining: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--api-url", "--timeout", "--profile", "--token"):
            global_args.append(arg)
            if i + 1 < len(args):
                global_args.append(args[i + 1])
                i += 2
                continue
            i += 1
            continue
        if arg in ("--no-color", "-q", "--quiet"):
            global_args.append(arg)
            i += 1
            continue
        if arg == "--session":
            if i + 1 < len(args):
                session_id = args[i + 1]
                i += 2
                continue
            i += 1
            continue
        if arg.startswith("--session="):
            session_id = arg.split("=", 1)[1]
            i += 1
            continue
        remaining.append(arg)
        i += 1

    # Installer le contexte global
    try:
        ctx = parse_global_options(global_args if global_args else [])
        set_context(ctx)
    except Exception:  # noqa: BLE001
        ctx = get_context()
        set_context(ctx)

    color = ctx.color if hasattr(ctx, "color") else True

    app = TuiApp(session_id=session_id, color=color)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())

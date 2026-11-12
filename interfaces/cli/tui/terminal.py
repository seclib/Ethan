"""Lecture clavier bas niveau pour le TUI ETHAN.

Utilise ``termios``/``tty``/``select`` (stdlib) : aucune nouvelle
dépendance. Si le terminal n'est pas un TTY ou si termios est indisponible,
le TUI bascule en mode dégradé (voir `Terminal.is_interactive`).
"""

from __future__ import annotations

import io
import os
import select
import sys
import termios
import tty
from typing import TextIO

from interfaces.cli.tui.models import KeyKind, Keypress


class Terminal:
    """Abstraction d'un terminal interactif en mode brut."""

    def __init__(self, stream: TextIO = sys.stdin) -> None:
        self._stream = stream
        try:
            self._fd = stream.fileno()
        except (io.UnsupportedOperation, ValueError, OSError, AttributeError):
            self._fd = -1
        self._original: termios.struct_termios | None = None
        self._raw = False

    @property
    def is_interactive(self) -> bool:
        try:
            return bool(self._stream.isatty())
        except (OSError, ValueError):
            return False

    def enter_raw(self) -> bool:
        if not self.is_interactive:
            return False
        try:
            self._original = termios.tcgetattr(self._fd)
            tty.setraw(self._fd)
            self._raw = True
            return True
        except (termios.error, OSError, ValueError):
            self._original = None
            self._raw = False
            return False

    def restore(self) -> None:
        if self._original is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._original)
            except (termios.error, OSError):
                pass
            self._original = None
        self._raw = False

    def size(self) -> tuple[int, int]:
        """Retourne (colonnes, lignes)."""
        try:
            import shutil

            cols, rows = shutil.get_terminal_size(fallback=(80, 24))
            return cols, rows
        except Exception:  # noqa: BLE001
            return 80, 24

    def read_keypress(self, timeout: float = 0.05) -> Keypress | None:
        """Lit une touche (ou None si rien dans ``timeout``)."""
        if not self._raw:
            return None
        ready, _, _ = select.select([self._fd], [], [], timeout)
        if not ready:
            return None
        try:
            first = os.read(self._fd, 1)
        except OSError:
            return None
        if not first:
            return None

        # Ctrl-C / Ctrl-D
        if first == b"\x03":
            return Keypress(KeyKind.CTRL_C)
        if first == b"\x04":
            return Keypress(KeyKind.CTRL_D)
        if first == b"\x09":
            return Keypress(KeyKind.TAB)
        if first == b"\r":
            return Keypress(KeyKind.ENTER)
        if first == b"\n":
            return Keypress(KeyKind.NEWLINE)
        if first in (b"\x7f", b"\x08"):
            return Keypress(KeyKind.BACKSPACE)
        if first == b"\x01":
            return Keypress(KeyKind.CTRL_A)
        if first == b"\x05":
            return Keypress(KeyKind.CTRL_E)
        if first == b"\x0b":
            return Keypress(KeyKind.CTRL_K)
        if first == b"\x0c":
            return Keypress(KeyKind.CTRL_L)
        if first == b"\x15":
            return Keypress(KeyKind.CTRL_U)
        if first == b"\x17":
            return Keypress(KeyKind.CTRL_W)

        # Séquence d'échappement
        if first == b"\x1b":
            return self._read_escape()

        # Octet UTF-8 multioctet
        if first[0] >= 0xC0:
            needed = 1 if first[0] < 0xE0 else (2 if first[0] < 0xF0 else 3)
            data = first
            for _ in range(needed):
                ready, _, _ = select.select([self._fd], [], [], 0.01)
                if not ready:
                    break
                data += os.read(self._fd, 1)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = ""
            if text:
                return Keypress(KeyKind.CHARACTER, text)
            return None

        # ASCII imprimable
        try:
            text = first.decode("ascii")
        except UnicodeDecodeError:
            text = ""
        if text and text.isprintable():
            return Keypress(KeyKind.CHARACTER, text)
        return None

    def _read_escape(self) -> Keypress | None:
        # Attendre la suite avec un court délai.
        ready, _, _ = select.select([self._fd], [], [], 0.02)
        if not ready:
            return Keypress(KeyKind.ESCAPE)
        data = os.read(self._fd, 1)
        if data == b"[":
            # CSI sequence
            seq = b""
            while True:
                ready, _, _ = select.select([self._fd], [], [], 0.02)
                if not ready:
                    break
                ch = os.read(self._fd, 1)
                seq += ch
                if ch and ch[-1:] in b"~ABCDEFGHIJKLMNPQRSTUVWXZ":
                    break
                if len(seq) > 16:
                    break
            text = seq.decode("ascii", errors="ignore")

            # Bracketed paste start: ESC[200~
            if text == "200~":
                pasted = b""
                while True:
                    ready, _, _ = select.select([self._fd], [], [], 0.5)
                    if not ready:
                        break
                    ch = os.read(self._fd, 1)
                    if ch == b"\x1b":
                        seq2 = b""
                        ready2, _, _ = select.select([self._fd], [], [], 0.05)
                        if ready2:
                            seq2 += os.read(self._fd, 1)
                            if seq2 == b"[":
                                while True:
                                    ready3, _, _ = select.select([self._fd], [], [], 0.05)
                                    if not ready3:
                                        break
                                    ch3 = os.read(self._fd, 1)
                                    seq2 += ch3
                                    if ch3 == b"~":
                                        break
                                if seq2 == b"[201~":
                                    break
                                else:
                                    pasted += ch + seq2
                            else:
                                pasted += ch + seq2
                    else:
                        pasted += ch
                try:
                    decoded = pasted.decode("utf-8")
                except UnicodeDecodeError:
                    decoded = pasted.decode("utf-8", errors="replace")
                if decoded:
                    return Keypress(KeyKind.CHARACTER, decoded)
                return None

            mapping = {
                "A": KeyKind.UP,
                "B": KeyKind.DOWN,
                "C": KeyKind.RIGHT,
                "D": KeyKind.LEFT,
                "H": KeyKind.HOME,
                "F": KeyKind.END,
                "Z": KeyKind.TAB,
            }
            if text in ("~",):
                pass
            if text and text[-1] in mapping and text[:-1].isdigit() is False and "~" not in text:
                return Keypress(mapping[text[-1]])
            # Numeric CSI
            if text.endswith("~"):
                num = text[:-1]
                if num == "3":
                    return Keypress(KeyKind.DELETE)
                if num in ("5", "5~"):
                    return Keypress(KeyKind.PAGE_UP)
                if num in ("6", "6~"):
                    return Keypress(KeyKind.PAGE_DOWN)
                if num in ("1", "7"):
                    return Keypress(KeyKind.HOME)
                if num in ("4", "8"):
                    return Keypress(KeyKind.END)
            # SGR mouse wheel (CSI < ... M/m) — ignore
            if text.startswith("<"):
                return None
            # Application-mode arrows (ESC O A)
            return Keypress(KeyKind.ESCAPE)
        if data == b"O":
            ready, _, _ = select.select([self._fd], [], [], 0.02)
            if ready:
                ch = os.read(self._fd, 1)
                mapping = {b"A": KeyKind.UP, b"B": KeyKind.DOWN, b"C": KeyKind.RIGHT, b"D": KeyKind.LEFT, b"H": KeyKind.HOME, b"F": KeyKind.END}
                if ch in mapping:
                    return Keypress(mapping[ch])
            return Keypress(KeyKind.ESCAPE)
        try:
            ch = data.decode("ascii")
            if ch.isprintable():
                return Keypress(KeyKind.CHARACTER, ch)
        except UnicodeDecodeError:
            pass
        return Keypress(KeyKind.ESCAPE)


__all__ = ["Terminal"]

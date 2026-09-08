/**
 * ETHAN WebUI — Keyboard Shortcuts registry (UI-only).
 *
 * These shortcuts are managed entirely by the WebUI layer. They dispatch
 * to internal routes (/chat, /projects, /knowledge, /library, /settings)
 * and never invoke Runtime business logic directly.
 *
 * The authoritative source for shortcut bindings is this file.
 * The WebUI listener hook (use-keyboard.ts) reads from here.
 */

export interface Shortcut {
  id: string;
  label: string;
  /** Keyboard shortcut string (human-readable) */
  display: string;
  /** Route or action the shortcut triggers */
  action: "route" | "command";
  /** Target route for "route" actions */
  target?: string;
}

export const SHORTCUTS: Shortcut[] = [
  {
    id: "new-chat",
    label: "New Chat",
    display: "⌘N",
    action: "route",
    target: "/chat",
  },
  {
    id: "new-project",
    label: "New Project",
    display: "⌘⇧P",
    action: "route",
    target: "/projects/new",
  },
  {
    id: "search",
    label: "Search",
    display: "⌘K",
    action: "command",
    target: "command-palette",
  },
  {
    id: "library",
    label: "Library",
    display: "⌘L",
    action: "route",
    target: "/library",
  },
  {
    id: "settings",
    label: "Settings",
    display: "⌘,",
    action: "route",
    target: "/settings",
  },
];

/** Map of key combos to shortcut ids (for the listener hook). */
export const SHORTCUT_KEYS: Record<string, string> = {
  "KeyN": "new-chat",
  "KeyP": "new-project",
  "KeyK": "search",
  "KeyL": "library",
  "Comma": "settings",
};

/** Whether to use Ctrl (Windows/Linux) vs Cmd (Mac). */
export const MODIFIER_KEY =
  typeof navigator !== "undefined" && navigator.platform.includes("Mac")
    ? "metaKey"
    : "ctrlKey";

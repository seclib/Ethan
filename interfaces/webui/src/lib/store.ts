import { create } from "zustand";
import { persist } from "@/lib/persistence";

export type AppPage =
  | "dashboard"
  | "assistant"
  | "knowledge"
  | "memory"
  | "agents"
  | "planner"
  | "models"
  | "providers"
  | "plugins"
  | "tools"
  | "documents"
  | "settings"
  | "logs"
  | "terminal";

export type NavGroup = "observer" | "cognition" | "extensions" | "system";

export interface NavItem {
  id: AppPage;
  label: string;
  icon: string;
  group: NavGroup;
  shortcut: string;
  breadcrumb: string[];
}

export const NAV_ITEMS: NavItem[] = [
  { id: "dashboard",  label: "Dashboard",  icon: "◉", group: "observer",    shortcut: "⌘1", breadcrumb: ["Dashboard"] },
  { id: "assistant",  label: "Assistant",  icon: "💬", group: "observer",    shortcut: "⌘2", breadcrumb: ["Assistant"] },
  { id: "knowledge",  label: "Knowledge",  icon: "◈", group: "observer",    shortcut: "⌘3", breadcrumb: ["Knowledge"] },
  { id: "memory",     label: "Memory",     icon: "◆", group: "observer",    shortcut: "⌘4", breadcrumb: ["Memory"] },
  { id: "agents",     label: "Agents",     icon: "⚡", group: "cognition",   shortcut: "⌘5", breadcrumb: ["Agents"] },
  { id: "planner",    label: "Planner",    icon: "📋", group: "cognition",   shortcut: "⌘6", breadcrumb: ["Planner"] },
  { id: "models",     label: "Models",     icon: "🤖", group: "cognition",   shortcut: "⌘7", breadcrumb: ["Models"] },
  { id: "providers",  label: "Providers",  icon: "🔌", group: "cognition",   shortcut: "⌘8", breadcrumb: ["Providers"] },
  { id: "plugins",    label: "Plugins",    icon: "🧩", group: "extensions",  shortcut: "⌘9", breadcrumb: ["Plugins"] },
  { id: "tools",      label: "Tools",      icon: "🛠",  group: "extensions", shortcut: "⌘0", breadcrumb: ["Tools"] },
  { id: "documents",  label: "Documents",  icon: "📄", group: "extensions", shortcut: "⌘-", breadcrumb: ["Documents"] },
  { id: "settings",   label: "Settings",   icon: "⚙",  group: "system",     shortcut: "⌘,", breadcrumb: ["Settings"] },
  { id: "logs",       label: "Logs",       icon: "📜", group: "system",     shortcut: "⌘L", breadcrumb: ["Logs"] },
  { id: "terminal",   label: "Terminal",   icon: "⌨",  group: "system",     shortcut: "⌘`", breadcrumb: ["Terminal"] },
];

export const GROUP_LABELS: Record<NavGroup, string> = {
  observer: "Observer",
  cognition: "Cognition",
  extensions: "Extensions",
  system: "System",
};

const ITEM_MAP = Object.fromEntries(NAV_ITEMS.map((i) => [i.id, i]));

// ───────── Page titles ─────────
export const PAGE_TITLES: Record<AppPage, string> = {
  dashboard: "Dashboard",
  assistant: "Assistant",
  knowledge: "Knowledge",
  memory: "Memory",
  agents: "Agents",
  planner: "Planner",
  models: "Models",
  providers: "Providers",
  plugins: "Plugins",
  tools: "Tools",
  documents: "Documents",
  settings: "Settings",
  logs: "Logs",
  terminal: "Terminal",
};

export function getBreadcrumbs(page: AppPage): string[] {
  return ITEM_MAP[page]?.breadcrumb ?? [PAGE_TITLES[page]];
}

// ───────── Context menu ─────────
export interface ContextMenuState {
  open: boolean;
  x: number;
  y: number;
  page: AppPage | null;
}

// ───────── Inspector ─────────
interface InspectorState {
  open: boolean;
  type: "goal" | "mission" | "skill" | "fact" | "event" | null;
  id: string | null;
  data: unknown | null;
}

// ───────── Store ─────────
interface AppState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  currentPage: AppPage;
  setPage: (page: AppPage) => void;
  theme: "dark" | "light";
  toggleTheme: () => void;
  contextMenu: ContextMenuState;
  openContextMenu: (x: number, y: number, page: AppPage) => void;
  closeContextMenu: () => void;
  inspector: InspectorState;
  openInspector: (type: InspectorState["type"], id: string, data?: unknown) => void;
  closeInspector: () => void;
}

const savedPage = () => {
  try {
    const raw = localStorage.getItem("ethan:page");
    if (raw && ITEM_MAP[raw as AppPage]) return raw as AppPage;
  } catch {}
  return "dashboard" as AppPage;
};

const savedSidebar = () => {
  try {
    const raw = localStorage.getItem("ethan:sidebar");
    return raw !== "false";
  } catch {}
  return true;
};

export const useStore = create<AppState>((set) => ({
  sidebarOpen: savedSidebar(),
  toggleSidebar: () =>
    set((s) => {
      const next = !s.sidebarOpen;
      try { localStorage.setItem("ethan:sidebar", String(next)); } catch {}
      return { sidebarOpen: next };
    }),
  currentPage: savedPage(),
  setPage: (page) => {
    try { localStorage.setItem("ethan:page", page); } catch {}
    set({ currentPage: page });
  },
  theme: "dark",
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      if (typeof document !== "undefined") {
        document.documentElement.classList.toggle("light", next === "light");
      }
      return { theme: next };
    }),
  contextMenu: { open: false, x: 0, y: 0, page: null },
  openContextMenu: (x, y, page) => set({ contextMenu: { open: true, x, y, page } }),
  closeContextMenu: () => set({ contextMenu: { open: false, x: 0, y: 0, page: null } }),
  inspector: { open: false, type: null, id: null, data: null },
  openInspector: (type, id, data) =>
    set({ inspector: { open: true, type, id, data: data ?? null } }),
  closeInspector: () =>
    set({ inspector: { open: false, type: null, id: null, data: null } }),
}));
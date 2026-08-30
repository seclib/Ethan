"use client";

/**
 * ETHAN WebUI — Sidebar (refonte Open-WebUI)
 *
 * Une seule barre latérale, toujours montée dans le shell, repliable :
 *  - sur la page chat (/) → groupe CONVERSATIONS
 *  - partout → groupe NAVIGATION (taxinomie unique NAV_SECTIONS), collapsible
 * Le sélecteur Agent/Model reste dans le header du chat (AssistantTopBar).
 */

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useChatSidebarStore } from "@/store/chat-sidebar.store";
import { useUIStore } from "@/store/ui.store";
import { NAV_SECTIONS_PRIMARY, NAV_SECTIONS_ADMIN } from "./nav-config";
import type { NavItem, NavSection } from "./nav-config";
import { useAuth } from "@/providers/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Pin, Plus, Trash2, MessageSquare, Search, Settings, ExternalLink,
  ChevronDown, LogOut, SquarePen, PanelLeftClose,
} from "lucide-react";
import { LogoSquare } from "@/components/shared/logo";
import type { EthChat } from "@/components/features/assistant/hooks/use-chats";

export interface AppSidebarProps {
  expanded: boolean;
  onToggle: () => void;
}

/**
 * Sections rendues dans la sidebar déployée (conversation-centric) :
 * navigation quotidienne + Administration compacte en bas.
 * Les entrées techniques (Models, Providers, Knowledge…) sont déléguées à
 * la navigation secondaire (Settings + palette Ctrl+K) — voir nav-config v5.
 */
const SIDEBAR_SECTIONS = [...NAV_SECTIONS_PRIMARY, ...NAV_SECTIONS_ADMIN];

/** Breakpoint mobile partagé (SSR-safe : false tant que non monté). */
function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(false);
  React.useEffect(() => {
    const mq = window.matchMedia("(max-width: 767px)");
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return isMobile;
}

export function AppSidebar({ expanded, onToggle }: AppSidebarProps) {
  const pathname = usePathname();
  const chatState = useChatSidebarStore();
  const router = useRouter();
  const { openCommandPalette } = useUIStore();
  const setPendingChat = useChatSidebarStore((s) => s.setPendingChat);
  // Clic sur une conversation hors page chat : on enregistre la cible puis on
  // navigue vers "/" — la page chat ouvrira la conversation au montage.
  const selectFromSidebar = (id: string) => {
    if (chatState.onSelectChat) { chatState.onSelectChat(id); }
    else { setPendingChat(id); router.push("/"); }
  };
  const handleNewChat = () => {
    if (chatState.onNewChat) { chatState.onNewChat(); }
    else { window.location.href = "/"; }
  };
  const [openGroups, setOpenGroups] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    if (!expanded) {
      document.documentElement.classList.add("sidebar-collapsed");
    } else {
      document.documentElement.classList.remove("sidebar-collapsed");
    }
  }, [expanded]);

  React.useEffect(() => {
    if (pathname) {
      SIDEBAR_SECTIONS.forEach((sec) => {
        if (sec.items.some((it) => it.href === pathname)) {
          setOpenGroups((g) => ({ ...g, [sec.id]: true }));
        }
      });
    }
  }, [pathname]);

  /**
   * Responsive — mobile (< 768px) : la sidebar déployée devient un drawer
   * en overlay (cf. classe `.sidebar-mobile-open` + backdrop). L'état runtime
   * est ajusté SANS écrire la préférence utilisateur : sur desktop la session
   * démarre toujours déployée, sauf préférence explicite.
   */
  const isMobile = useIsMobile();
  const setSidebarExpanded = useUIStore((s) => s.setSidebarExpanded);
  const prevMobile = React.useRef<boolean | null>(null);
  React.useEffect(() => {
    const wasMobile = prevMobile.current;
    prevMobile.current = isMobile;
    // Ferme (runtime, sans persister) au montage mobile et au passage desktop→mobile.
    if (isMobile && (wasMobile === null || !wasMobile) && expanded) {
      setSidebarExpanded(false);
    }
  }, [isMobile, expanded, setSidebarExpanded]);

  if (!expanded) {
    return (
      <nav className="sidebar sidebar-collapsed" id="sidebar">
        <div className="sidebar-header" style={{ justifyContent: "center", padding: "10px 4px 4px" }}>
          <button onClick={onToggle} className="sidebar-collapsed-btn" aria-label="Ouvrir la sidebar" title="Ouvrir la sidebar">
            <LogoSquare size={18} />
          </button>
        </div>
        <div className="flex flex-col items-center gap-1 px-1 pb-1">
          {/* Rail replié MINIMAL (Open-WebUI) : uniquement les actions utiles —
              pas de colonne d'icônes techniques. La navigation complète vit
              dans la sidebar déployée / Settings / palette Ctrl+K. */}
          <button onClick={handleNewChat} className="sidebar-collapsed-btn" title="Nouveau chat" aria-label="Nouveau chat">
            <SquarePen size={16} />
          </button>
          <button onClick={openCommandPalette} className="sidebar-collapsed-btn" title="Rechercher (Ctrl+K)" aria-label="Rechercher">
            <Search size={16} />
          </button>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ flexShrink: 0 }}>
          <UserBar expanded={false} />
        </div>
      </nav>
    );
  }

  return (
    <>
      {/* Backdrop mobile : ferme le drawer sans persister de préférence */}
      {isMobile && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={() => setSidebarExpanded(false)}
          aria-hidden
        />
      )}
      <nav
        className={cn("sidebar", isMobile && "sidebar-mobile-open")}
        id="sidebar"
        style={{
          display: "flex", flexDirection: "column", zIndex: 49, flexShrink: 0,
        }}
      >
      <div className="sidebar-header">
        <div className="sidebar-brand flex items-center gap-2">
          <LogoSquare size={18} />
          <span>ETHAN</span>
        </div>
        <button onClick={onToggle} className="sidebar-hamburger" title="Replier" aria-label="Replier la sidebar">
          <PanelLeftClose size={16} />
        </button>
      </div>
      <div className="sidebar-actions">
        <button onClick={handleNewChat} className="sidebar-new-chat" aria-label="Nouveau chat">
          <span>Nouveau chat</span>
          <SquarePen size={15} />
        </button>
        <button onClick={openCommandPalette} className="sidebar-search" aria-label="Rechercher" title="Rechercher (Ctrl+K)">
          <Search size={15} />
          <span>Rechercher…</span>
          <kbd>Ctrl K</kbd>
        </button>
      </div>
      <div className="sidebar-inner custom-scrollbar" style={{ flex: 1, overflowY: "auto" }}>
        {/* Sidebar conversation-centric (Open-WebUI) : les conversations
            restent visibles sur toutes les pages tant que le store en a. */}
        {chatState.chats.length > 0 && (
          <ChatSection
            chats={chatState.chats} pinnedChats={chatState.pinnedChats}
            regularChats={chatState.regularChats} currentChatId={chatState.currentChatId}
            onNewChat={handleNewChat} onSelectChat={selectFromSidebar}
            onDeleteChat={chatState.onDeleteChat} onTogglePin={chatState.onTogglePin}
            onRenameChat={chatState.onRenameChat}
          />
        )}
        <NavigationSection
          sections={SIDEBAR_SECTIONS}
          pathname={pathname}
          openGroups={openGroups}
          setOpenGroups={setOpenGroups}
        />
        {/* Settings — pied de la sidebar (navigation secondaire : capacités
            techniques via Settings + palette Ctrl+K) */}
        <div className="sidebar-nav-group border-t border-line-1/40 pt-1">
          <Link
            href="/settings"
            className={cn("sidebar-nav-item", pathname === "/settings" && "active")}
            title="Paramètres ETHAN — modèles, providers, outils, préférences"
          >
            <Settings size={15} className="sidebar-nav-icon" />
            <span>Settings</span>
            {pathname.startsWith("/settings") && (
              <span className="ml-auto text-[10px] text-foreground-tertiary">↳</span>
            )}
          </Link>
        </div>
      </div>
      <UserBar expanded={expanded} />
    </nav>
    </>
  );
}

/* ── Conversations (vue Chat) ── */

function groupChatsByPeriod(chats: EthChat[]): { label: string; items: EthChat[] }[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7);
  const monthAgo = new Date(today); monthAgo.setDate(monthAgo.getDate() - 30);
  const groups: { label: string; items: EthChat[] }[] = [
    { label: "Aujourd'hui", items: [] },
    { label: "Hier", items: [] },
    { label: "7 derniers jours", items: [] },
    { label: "30 derniers jours", items: [] },
    { label: "Plus ancien", items: [] },
  ];
  for (const chat of chats) {
    const d = new Date(chat.updated_at);
    if (d >= today) groups[0].items.push(chat);
    else if (d >= yesterday) groups[1].items.push(chat);
    else if (d >= weekAgo) groups[2].items.push(chat);
    else if (d >= monthAgo) groups[3].items.push(chat);
    else groups[4].items.push(chat);
  }
  return groups.filter((g) => g.items.length > 0);
}

function ChatSection(props: {
  chats: EthChat[]; pinnedChats: EthChat[]; regularChats: EthChat[];
  currentChatId: string | null;
  onNewChat?: (() => void) | null; onSelectChat?: ((id: string) => void) | null;
  onDeleteChat?: ((id: string) => void) | null;
  onTogglePin?: ((id: string, cur: boolean) => void) | null;
  onRenameChat?: ((id: string, t: string) => void) | null;
}) {
  const { pinnedChats, regularChats, currentChatId } = props;
  const [search, setSearch] = React.useState("");
  const filtered = React.useMemo(() => {
    if (!search.trim()) return regularChats;
    const q = search.toLowerCase();
    return regularChats.filter((c) => c.title.toLowerCase().includes(q));
  }, [regularChats, search]);
  const grouped = React.useMemo(() => groupChatsByPeriod(filtered), [filtered]);

  return (
    <div className="sidebar-nav-group" style={{ padding: "8px 0" }}>
      <div className="section-title">Conversations</div>
      <div className="px-2 pb-2">
        <Button
          variant="default"
          size="sm"
          onClick={() => props.onNewChat?.()}
          className="w-full"
        >
          <Plus size={15} /> <span>Nouveau chat</span>
        </Button>
      </div>
      <div className="px-2 pb-2">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
          <input
            type="text" value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher conversations..."
            className="w-full rounded-md border border-line-2 bg-bg-1 py-1.5 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
        </div>
      </div>
      {pinnedChats.length > 0 && (
        <div className="px-1">
          <div className="section-title">Épinglés</div>
          {pinnedChats.map((c) => (
            <ChatItem
              key={c.id} chat={c} isActive={c.id === currentChatId}
              onSelect={() => props.onSelectChat?.(c.id)}
              onDelete={(e) => { e.stopPropagation(); props.onDeleteChat?.(c.id); }}
              onPin={(e) => { e.stopPropagation(); props.onTogglePin?.(c.id, c.pinned); }}
              onRename={(t) => props.onRenameChat?.(c.id, t)}
            />
          ))}
        </div>
      )}
      {grouped.map((g) => (
        <div key={g.label} className="px-1">
          <div className="section-title">{g.label}</div>
          {g.items.map((c) => (
            <ChatItem
              key={c.id} chat={c} isActive={c.id === currentChatId}
              onSelect={() => props.onSelectChat?.(c.id)}
              onDelete={(e) => { e.stopPropagation(); props.onDeleteChat?.(c.id); }}
              onPin={(e) => { e.stopPropagation(); props.onTogglePin?.(c.id, c.pinned); }}
              onRename={(t) => props.onRenameChat?.(c.id, t)}
            />
          ))}
        </div>
      ))}
      {props.chats.length === 0 && (
        <div className="px-3 py-6 text-center text-sm text-foreground-tertiary">Aucune conversation</div>
      )}
    </div>
  );
}

function ChatItem({ chat, isActive, onSelect, onDelete, onPin, onRename }: {
  chat: EthChat; isActive: boolean;
  onSelect: () => void; onDelete: (e: React.MouseEvent) => void;
  onPin: (e: React.MouseEvent) => void; onRename: (t: string) => void;
}) {
  const [renaming, setRenaming] = React.useState(false);
  const [value, setValue] = React.useState(chat.title);
  const inputRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => { if (renaming) { inputRef.current?.focus(); inputRef.current?.select(); } }, [renaming]);
  const commit = () => { setRenaming(false); const t = value.trim(); if (t && t !== chat.title) onRename(t); };
  return (
    <div
      onClick={onSelect} className={cn("list-item", isActive && "active")}
      role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" && !renaming) onSelect(); }}
    >
      <MessageSquare size={14} className="shrink-0 opacity-50" />
      {renaming ? (
        <input
          ref={inputRef} value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") { setRenaming(false); setValue(chat.title); }
          }}
          onClick={(e) => e.stopPropagation()}
          className="sidebar-rename-input" aria-label="Renommer"
        />
      ) : (
        <span
          className="flex-1 truncate" title="Double-clic pour renommer"
          onDoubleClick={(e) => { e.stopPropagation(); setValue(chat.title); setRenaming(true); }}
        >{chat.title}</span>
      )}
      <span className="sidebar-item-actions" onClick={(e) => e.stopPropagation()}>
        <button onClick={onPin} className="sidebar-action-btn" title={chat.pinned ? "Désépingler" : "Épingler"}>
          <Pin size={12} />
        </button>
        <button onClick={onDelete} className="sidebar-action-btn" title="Supprimer">
          <Trash2 size={12} />
        </button>
      </span>
    </div>
  );
}

/* ── Navigation (permanent) ── */

function NavigationSection({
  sections,
  pathname, openGroups, setOpenGroups,
}: {
  sections: NavSection[];
  pathname: string;
  openGroups: Record<string, boolean>;
  setOpenGroups: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
}) {
  return (
    <div className="sidebar-nav-group">
            {sections.map((section) => {
        const isOpen = openGroups[section.id] ?? true;
        if (!section.collapsible && section.items.length <= 1) {
          const item = section.items[0];
          return (
            <Link
              key={item.href} href={item.href}
              className={cn("sidebar-nav-item", pathname === item.href && "active")}
              title={item.label}
            >
              <ItemIcon icon={item.icon} />
              <span>{item.label}</span>
            </Link>
          );
        }
        return (
          <div key={section.id}>
                        <button
              className={cn("sidebar-nav-section-header", section.items.some((it) => it.href === pathname) && "active")}
              onClick={() => setOpenGroups((g) => ({ ...g, [section.id]: !g[section.id] }))}
              aria-expanded={isOpen}
              title={section.description ?? section.label}
            >
              <span className="sidebar-nav-item-outer">
                <span>{section.label}</span>
              </span>
              <ChevronDown size={14} className={cn("sidebar-nav-chevron", !isOpen && "rotate-[-90deg]")} />
            </button>
            {isOpen && (
              <div className="sidebar-nav-sub">
                {section.items.map((item) =>
                  item.external ? (
                    <a
                      key={item.href} href={item.href} target="_blank" rel="noreferrer"
                      className="sidebar-nav-item"
                      title={item.label}
                    >
                      <ItemIcon icon={item.icon} />
                      <span>{item.label}</span>
                      <ExternalLink size={11} className="ml-auto opacity-40" />
                    </a>
                  ) : (
                    <Link
                      key={item.href} href={item.href}
                      className={cn("sidebar-nav-item", pathname === item.href && "active")}
                    >
                      <ItemIcon icon={item.icon} />
                      <span>{item.label}</span>
                    </Link>
                  ),
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ItemIcon({ icon }: { icon: NavItem["icon"] }) {
  const Icon = icon;
  return Icon ? <Icon size={15} className="sidebar-nav-icon" /> : <span className="w-4" />;
}

/* ── User bar ── */

export function UserBar({ expanded = true }: { expanded?: boolean }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const displayName = user?.name || user?.email || "Utilisateur";
  const initial = (displayName[0] || "E").toUpperCase();
  return (
    <div className="sidebar-user-bar">
      {expanded && (
        <div className="user-bar-left" title={user?.email ? `${displayName} — ${user.email}` : displayName}>
          <div className="user-bar-avatar" aria-hidden>{initial}</div>
          <span className="user-bar-name truncate">{displayName}</span>
        </div>
      )}
      <div className="user-bar-actions">
        <Link
          href="/settings"
          className={cn("user-bar-btn", pathname === "/settings" && "active")}
          title="Paramètres" aria-label="Paramètres"
        >
          <Settings size={15} />
        </Link>
        <button onClick={() => logout?.()} className="user-bar-btn" title="Déconnexion" aria-label="Déconnexion">
          <LogOut size={15} />
        </button>
      </div>
    </div>
  );
}

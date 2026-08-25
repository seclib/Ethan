"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui.store";
import { useChatSidebarStore } from "@/store/chat-sidebar.store";
import type { EthChat } from "@/components/features/assistant/hooks/use-chats";
import { ModelSelector } from "@/components/shared/model-selector";
import {
  MessageSquare,
  Network,
  Database,
  FileText,
  Bot,
  Settings,
  Search,
  Plus,
  Target,
  Layers,
  Cpu,
  Sparkles,
  Menu,
  Pin,
  Trash2,
  Calendar,
  StickyNote,
  ShieldCheck,
  Inbox,
  Telescope,
  BookOpen,
} from "lucide-react";
import { LogoSquare } from "@/components/shared/logo";

/**
 * IconRail — barre d'icônes verticale (navigation globale).
 * Toujours visible sur toutes les pages.
 * Style Odysseus : .icon-rail
 */
export function IconRail() {
  const pathname = usePathname();
  const items = [
    { href: "/", label: "Chat", icon: MessageSquare },
    { href: "/workspace", label: "Workspace", icon: Network },
    { href: "/calendar", label: "Calendar", icon: Calendar },
    { href: "/notes", label: "Notes", icon: StickyNote },
    { href: "/knowledge", label: "Knowledge", icon: Database },
    { href: "/missions", label: "Missions", icon: Target },
    { href: "/agents", label: "Agents", icon: Bot },
    { href: "/tools", label: "Tools", icon: FileText },
    { href: "/providers", label: "Providers", icon: Layers },
    { href: "/models", label: "Models", icon: Cpu },
  ];
  return (
    <div className="icon-rail" id="icon-rail">
      <button className="icon-rail-btn" title="Search (Ctrl+K)" aria-label="Search (Ctrl+K)">
        <Search size={16} />
      </button>
      <Link href="/" className={cn("icon-rail-btn rail-new-chat", pathname === "/" && "active-section")} title="Chat" aria-label="Chat">
        <Plus size={16} />
      </Link>
      <div className="rail-separator"></div>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href;
        return (
          <Link key={item.href} href={item.href} className={cn("icon-rail-btn", isActive && "active-section")} title={item.label} aria-label={item.label}>
            <Icon size={16} />
          </Link>
        );
      })}
      <div className="rail-separator"></div>
      <div style={{ flex: 1 }}></div>
      <Link href="/settings" className={cn("icon-rail-btn", pathname === "/settings" && "active-section")} title="Settings" aria-label="Settings">
        <Settings size={16} />
      </Link>
    </div>
  );
}

/**
 * Sidebar — composant combiné (IconRail + AppSidebar).
 * Conservé pour compatibilité.
 */
export function Sidebar() {
  return (
    <>
      <IconRail />
      <AppSidebar />
    </>
  );
}



/* ═══ AppSidebar — LA sidebar unique du shell (modèle Odysseus) ═══
 * Une seule sidebar toujours montée dans le layout :
 *  - sur la page chat (/) → vue Chats (conversations groupées par période)
 *  - ailleurs            → vue Navigation (list-items vers les sections)
 * Barre utilisateur en bas (user-bar).
 */
export function AppSidebar() {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar } = useUIStore();
  const chatState = useChatSidebarStore();
  const isChatRoute = pathname === "/";
  const hasChatHandlers = !!chatState.onSelectChat;

  return (
    <nav
      className="sidebar"
      id="sidebar"
      style={{
        width: sidebarExpanded ? "240px" : "0px",
        overflow: "hidden",
        transition: "width 0.2s ease",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        zIndex: 49,
        flexShrink: 0,
      }}
    >
      <div className="sidebar-header">
        <button onClick={toggleSidebar} className="sidebar-hamburger" title="Toggle sidebar" aria-label="Toggle sidebar">
          <Menu size={16} />
        </button>
        <div className="sidebar-brand flex items-center gap-2">
          <LogoSquare size={20} />
          <span>ETHAN</span>
        </div>
      </div>

      {isChatRoute && hasChatHandlers ? (
        <ChatSidebarContent
          chats={chatState.chats}
          pinnedChats={chatState.pinnedChats}
          regularChats={chatState.regularChats}
          currentChatId={chatState.currentChatId}
          onNewChat={chatState.onNewChat}
          onSelectChat={chatState.onSelectChat}
          onDeleteChat={chatState.onDeleteChat}
          onTogglePin={chatState.onTogglePin}
        />
      ) : (
        <NavigationContent pathname={pathname} />
      )}

      <UserBar />
    </nav>
  );
}

function groupChatsByPeriod(chats: EthChat[]): { label: string; items: EthChat[] }[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);
  const monthAgo = new Date(today);
  monthAgo.setDate(monthAgo.getDate() - 30);

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

/* ─── Vue Chats (page chat) ─── */
interface ChatSidebarViewProps {
  chats: EthChat[];
  pinnedChats: EthChat[];
  regularChats: EthChat[];
  currentChatId: string | null;
  onNewChat: (() => void) | null;
  onSelectChat: ((chatId: string) => void) | null;
  onDeleteChat: ((chatId: string) => void) | null;
  onTogglePin: ((chatId: string, currentPinned: boolean) => void) | null;
}

function ChatSidebarContent(props: ChatSidebarViewProps) {
  const { pinnedChats, regularChats, chats, currentChatId } = props;
  const [search, setSearch] = React.useState("");

  const filteredChats = React.useMemo(() => {
    if (!search.trim()) return regularChats;
    const q = search.toLowerCase();
    return regularChats.filter((c) => c.title.toLowerCase().includes(q));
  }, [regularChats, search]);

  const grouped = React.useMemo(() => groupChatsByPeriod(filteredChats), [filteredChats]);

  return (
    <div className="sidebar-inner custom-scrollbar">
      <button
        onClick={() => props.onNewChat?.()}
        className="btn btn-primary"
        style={{ width: "100%", justifyContent: "center", gap: "8px", padding: "8px", marginBottom: "6px" }}
      >
        <Plus size={15} />
        <span>Nouveau chat</span>
      </button>

      <div className="relative mt-1 mb-2">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher..."
          className="input"
          style={{ width: "100%", paddingLeft: "32px" }}
        />
      </div>

      {pinnedChats.length > 0 && (
        <div className="mt-2">
          <div className="section-title">Épinglés</div>
          {pinnedChats.map((chat) => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isActive={chat.id === currentChatId}
              onSelect={() => props.onSelectChat?.(chat.id)}
              onDelete={(e) => { e.stopPropagation(); props.onDeleteChat?.(chat.id); }}
              onPin={(e) => { e.stopPropagation(); props.onTogglePin?.(chat.id, chat.pinned); }}
            />
          ))}
        </div>
      )}

      {grouped.map((group) => (
        <div key={group.label} className="mt-2">
          <div className="section-title">{group.label}</div>
          {group.items.map((chat) => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isActive={chat.id === currentChatId}
              onSelect={() => props.onSelectChat?.(chat.id)}
              onDelete={(e) => { e.stopPropagation(); props.onDeleteChat?.(chat.id); }}
              onPin={(e) => { e.stopPropagation(); props.onTogglePin?.(chat.id, chat.pinned); }}
            />
          ))}
        </div>
      ))}

      {chats.length === 0 && (
        <div className="px-2 py-8 text-center text-sm text-foreground-tertiary">Aucune conversation</div>
      )}

      <div className="mt-4 border-t border-line-1 pt-3">
        <div className="section-title">Modèle</div>
        <div className="px-2 py-1">
          <ModelSelector variant="compact" />
        </div>
      </div>
    </div>
  );
}

function ChatItem({ chat, isActive, onSelect, onDelete, onPin }: {
  chat: EthChat;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onPin: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={cn("list-item", isActive && "active")}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") onSelect(); }}
    >
      <MessageSquare size={14} className="shrink-0 opacity-50" />
      <span className="flex-1 truncate">{chat.title}</span>
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

/* ─── Vue Navigation (pages admin) ─── */
function NavigationContent({ pathname }: { pathname: string }) {
  const sections = [
    { href: "/workspace", label: "Workspace", icon: Network },
    { href: "/calendar", label: "Calendar", icon: Calendar },
    { href: "/notes", label: "Notes", icon: StickyNote },
    { href: "/knowledge", label: "Knowledge", icon: Database },
    { href: "/missions", label: "Missions", icon: Target },
    { href: "/agents", label: "Agents", icon: Bot },
    { href: "/skills", label: "Skills", icon: Sparkles },
    { href: "/tools", label: "Tools", icon: FileText },
    { href: "/inbox", label: "Inbox", icon: Inbox },
    { href: "/research", label: "Research", icon: Telescope },
    { href: "/cookbook", label: "Cookbook", icon: BookOpen },
  ];
  const system = [
    { href: "/providers", label: "Providers", icon: Layers },
    { href: "/models", label: "Models", icon: Cpu },
    { href: "/settings", label: "Settings", icon: Settings },
    { href: "/security", label: "Security", icon: ShieldCheck },
  ];

  return (
    <div className="sidebar-inner custom-scrollbar">
      <div className="section-title">Navigation</div>
      {sections.map((item) => {
        const Icon = item.icon;
        return (
          <Link key={item.href} href={item.href} className={cn("list-item", pathname === item.href && "active")}>
            <Icon size={15} className="sidebar-action-icon" />
            <span>{item.label}</span>
          </Link>
        );
      })}

      <div className="rail-separator"></div>

      <div className="section-title">Système</div>
      {system.map((item) => {
        const Icon = item.icon;
        return (
          <Link key={item.href} href={item.href} className={cn("list-item", pathname === item.href && "active")}>
            <Icon size={15} className="sidebar-action-icon" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </div>
  );
}

/* ─── User bar (bas de sidebar, comme Odysseus) ─── */
function UserBar() {
  const pathname = usePathname();
  return (
    <div className="sidebar-user-bar">
      <div className="user-bar-left">
        <div className="user-bar-avatar">E</div>
        <span className="user-bar-name">User</span>
      </div>
      <div className="user-bar-actions">
        <Link
          href="/settings"
          className={cn("user-bar-btn", pathname === "/settings" && "active")}
          title="Settings"
          aria-label="Settings"
        >
          <Settings size={15} />
        </Link>
      </div>
    </div>
  );
}
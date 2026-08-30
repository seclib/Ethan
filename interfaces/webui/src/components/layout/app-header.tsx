"use client";

/**
 * AppHeader — bandeau supérieur global du shell ETHAN (structure cible
 * Header / Sidebar / Main). Fin et discret : il porte le libellé de la
 * page courante (taxinomie nav-config) et l'état de connexion temps réel.
 *
 * Il est masqué sur "/" : la page chat possède déjà sa top bar contextuelle
 * (titre conversation + sélecteur modèle/agent). Aucune logique métier ici,
 * conformément à AGENTS.md — pure présentation de navigation.
 */

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useWebSocket } from "@/providers/websocket-provider";
import { NAV_ITEMS_FLAT } from "./nav-config";
import { LogoSquare } from "@/components/shared/logo";
import { Activity } from "lucide-react";

const WS_LABELS: Record<string, string> = {
  connected: "ETHAN connecté",
  connecting: "Connexion…",
  reconnecting: "Reconnexion…",
  disconnected: "Hors ligne",
  error: "Erreur connexion",
};

export function AppHeader() {
  const pathname = usePathname();
  const { status } = useWebSocket();

  if (pathname === "/") return null;

  // Libellé de page : correspondance exacte, puis préfixe (/models/detail → Modèles).
  const current =
    NAV_ITEMS_FLAT.find((i) => i.href === pathname) ??
    NAV_ITEMS_FLAT.filter((i) => pathname.startsWith(i.href)).sort((a, b) => b.href.length - a.href.length)[0];
  const label = current?.label ?? "Ethan";

  return (
    <header className="app-header">
      <div className="app-header-left">
        <Link href="/" className="app-header-home" aria-label="Retour au chat" title="Retour au chat">
          <LogoSquare size={16} />
        </Link>
        <span className="app-header-crumb">Ethan</span>
        <span className="app-header-sep" aria-hidden="true">/</span>
        <span className="app-header-page">{label}</span>
      </div>
      <div className="app-header-right">
        <span className={cn("ws-dot", `ws-${status}`)} aria-hidden="true" />
        <Activity size={12} aria-hidden="true" />
        <span>{WS_LABELS[status] ?? status}</span>
      </div>
    </header>
  );
}
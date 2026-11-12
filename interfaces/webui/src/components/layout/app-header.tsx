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
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useWebSocket } from "@/providers/websocket-provider";
import { useI18n } from "@/lib/i18n";
import { NAV_ITEMS_FLAT } from "./nav-config";
import { LogoSquare } from "@/components/shared/logo";
import { LanguageSelector } from "@/components/shared/language-selector";
import { Activity, ArrowLeft, ChevronLeft } from "lucide-react";

const WS_LABELS: Record<string, string> = {
  connected: "ETHAN connecté",
  connecting: "Connexion…",
  reconnecting: "Reconnexion…",
  disconnected: "Hors ligne",
  error: "Erreur connexion",
};



/**
 * Destination "parent" d'une route imbriquée, utilisée comme repli lorsque
 * l'historique du navigateur ne contient pas de page ETHAN précédente (chargement
 * direct d'une URL, rechargement, lien profond). La valeur `null` signifie
 * qu'il n'y a pas de parent applicatif au-dessus de la route courante.
 */
export function getParentPath(pathname: string | null | undefined): string | null {
  if (!pathname) return null;
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length <= 1) return null;
  return "/" + segments.slice(0, -1).join("/");
}

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { status } = useWebSocket();
  const { t } = useI18n();

  if (pathname === "/") return null;

  // Libellé de page : correspondance exacte, puis préfixe (/models/detail → Modèles).
  const current =
    NAV_ITEMS_FLAT.find((i) => i.href === pathname) ??
    NAV_ITEMS_FLAT.filter((i) => pathname.startsWith(i.href)).sort((a, b) => b.href.length - a.href.length)[0];
  const label = current ? t(current.label) : "Ethan";
  const parentPath = getParentPath(pathname);

  /**
   * Retour intelligent :
   *  - si le navigateur dispose d'un historique interne ETHAN, on revient à
   *    la page précédente (pas de redirection codée en dur vers Settings) ;
   *  - sinon (URL directe / rechargement / lien profond), on remonte d'un
   *    niveau dans la hiérarchie, avec repli vers la section racine (/).
   * On n'utilise jamais `router.back()` à l'aveugle : sans historique il ne
   * fait rien, et l'utilisateur resterait bloqué dans la vue imbriquée.
   */
  const handleBack = () => {
    const hasHistory =
      typeof window !== "undefined" &&
      typeof window.history !== "undefined" &&
      window.history.length > 1 &&
      window.history.state !== null;
    if (hasHistory) {
      router.back();
      return;
    }
    if (parentPath) router.push(parentPath);
    else router.push("/");
  };

  return (
    <header className="app-header">
      <div className="app-header-left">
        <button
          type="button"
          className="app-sidebar-toggle"
          aria-label="Page précédente"
          title="Page précédente"
          onClick={handleBack}
          data-testid="app-header-back"
        >
          <ArrowLeft size={15} />
        </button>
        {parentPath && parentPath !== "/" && (
          <button
            type="button"
            className="app-sidebar-toggle"
            aria-label="Niveau supérieur"
            title="Niveau supérieur"
            onClick={() => router.push(parentPath)}
            data-testid="app-header-parent"
          >
            <ChevronLeft size={14} />
          </button>
        )}
        <Link
          href="/"
          className="app-header-home"
          aria-label="Retour au chat"
          title="Menu principal"
          data-testid="app-header-home"
        >
          <LogoSquare size={16} />
        </Link>
        <span className="app-header-crumb">Ethan</span>
        <span className="app-header-sep" aria-hidden="true">/</span>
        <span className="app-header-page">{label}</span>
      </div>
      <div className="app-header-right">
        <LanguageSelector />
        <span className={cn("ws-dot", `ws-${status}`)} aria-hidden="true" />
        <Activity size={12} aria-hidden="true" />
        <span>{WS_LABELS[status] ?? status}</span>
      </div>
    </header>
  );
}
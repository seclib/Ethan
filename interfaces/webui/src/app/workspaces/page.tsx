import Link from "next/link";
import { ArrowRight, Server, BookOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";

/**
 * Index Workspaces — destination du bouton « niveau supérieur » de l'AppHeader
 * pour les routes imbriquées (`/workspaces/mcp`, `/workspaces/observatory`).
 * Cette page n'est pas un gestionnaire : elle énumère uniquement les sections
 * Workspaces existantes, dont la vérité métier reste dans ETHAN Core.
 */
const WORKSPACES = [
  {
    href: "/workspaces/observatory",
    title: "DAËNA",
    description:
      "Environnement de mémoire et de connaissances — Vault, Graph, Timeline, Search, Engineering, AI Insights.",
    icon: BookOpen,
  },
  {
    href: "/workspaces/mcp",
    title: "MCP",
    description:
      "Serveurs MCP connectés au Core — ajout, test, activation et synchronisation.",
    icon: Server,
  },
] as const;

export default function WorkspacesPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <PageHeader
        title="Workspaces"
        description="Sections de gestion opérationnelle d'ETHAN"
      />
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {WORKSPACES.map(({ href, title, description, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-lg border border-line-1 bg-bg-1 p-4 transition-colors hover:border-line-2 hover:bg-bg-2"
            >
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-foreground-tertiary" />
                <span className="text-sm font-semibold text-foreground">{title}</span>
                <ArrowRight className="ml-auto h-3.5 w-3.5 text-foreground-tertiary transition-transform group-hover:translate-x-0.5" />
              </div>
              <p className="mt-2 text-xs text-foreground-tertiary">{description}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

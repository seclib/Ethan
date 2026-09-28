"use client";

/**
 * Mission → Connections — services connectés utilisables par les workflows.
 *
 * AFFICHAGE SEUL : le catalogue et les connexions viennent du Core via la
 * même couche que la page /connections (lib/api/connections). La gestion
 * (connexion OAuth, révocation, credentials) reste dans /connections —
 * ce qui garantit une seule source de vérité (AGENTS.md : pas de doublon).
 *
 * Les futurs nœuds de workflow référenceront ces providers (ex. : nœud
 * GitHub, nœud Notion…) — c'est la raison de cette vue dans Mission.
 */

import * as React from "react";
import Link from "next/link";
import { listProviders, listConnections } from "@/lib/api/connections";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Plug, ArrowUpRight } from "lucide-react";
import type { ConnectionCatalog, Connection } from "@/lib/api/connections";

export default function MissionConnectionsPage() {
  const [providers, setProviders] = React.useState<ConnectionCatalog[]>([]);
  const [connections, setConnections] = React.useState<Connection[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    Promise.all([listProviders(), listConnections()])
      .then(([p, c]) => {
        if (cancelled) return;
        setProviders(p);
        setConnections(c);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erreur inconnue");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const connectedIds = new Set(
    connections.filter((c) => c.status === "connected").map((c) => c.provider),
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Plug size={17} className="text-accent" aria-hidden="true" /> Connections
          </h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Services connectés ETHAN — utilisables comme nœuds dans les futurs workflows.
          </p>
        </div>
        <Link
          href="/connections"
          className="flex items-center gap-1 rounded-md border border-line-2 px-3 py-1.5 text-sm text-foreground-secondary transition-colors hover:bg-elevated hover:text-foreground"
        >
          Gérer dans Connections <ArrowUpRight size={14} aria-hidden="true" />
        </Link>
      </div>

      {error && (
        <Card variant="outlined">
          <CardContent className="text-sm text-destructive">
            Impossible de récupérer le catalogue depuis le Core : {error}
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangle" className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {providers.map((provider) => {
            const connected = connectedIds.has(provider.id);
            return (
              <Card key={provider.id} variant="outlined">
                <CardContent className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium text-foreground">{provider.label}</span>
                      <Badge variant={connected ? "success" : "dim"} dot>
                        {connected ? "connected" : "not connected"}
                      </Badge>
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                      {provider.description}
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-foreground-tertiary">
                      {provider.scopes.length} scope(s) déclaré(s)
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
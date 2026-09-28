"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, Loader2, Globe, Shield, ExternalLink, CheckSquare, Square,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUIStore } from "@/store/ui.store";
import {
  searchWeb, listSearchEngines, listNetworkProfiles,
  type SearchEngine, type SearchResult, type SearchResponse, type NetworkProfileView,
} from "@/lib/api/web-search";

export function WebSearchPanel() {
  const addToast = useUIStore((s) => s.addToast);

  const { data: engines = [] } = useQuery<SearchEngine[]>({
    queryKey: ["search-engines"],
    queryFn: () => listSearchEngines(),
    staleTime: Infinity,
  });
  const { data: profiles = [] } = useQuery<NetworkProfileView[]>({
    queryKey: ["network-profiles"],
    queryFn: () => listNetworkProfiles(),
    staleTime: Infinity,
  });

  const [query, setQuery] = React.useState("");
  const [engine, setEngine] = React.useState("duckduckgo");
  const [maxResults, setMaxResults] = React.useState(10);
  const [searching, setSearching] = React.useState(false);
  const [searchResult, setSearchResult] = React.useState<SearchResponse | null>(null);
  const [selectedUrls, setSelectedUrls] = React.useState<Set<string>>(new Set());
  // Profils réseau (core/network) : identifiant seul — les credentials
  // restent dans le Core (variables d'environnement), jamais dans la WebUI.
  const [networkProfile, setNetworkProfile] = React.useState("direct");

  React.useEffect(() => {
    if (engines.length > 0 && !engines.find((e) => e.id === engine)) {
      setEngine(engines[0].id);
    }
  }, [engines, engine]);

  const runSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchResult(null);
    setSelectedUrls(new Set());
    try {
      const result = await searchWeb({
        query: query.trim(),
        engine,
        max_results: maxResults,
        network_profile: networkProfile || undefined,
      });
      setSearchResult(result);
      if (result.results.length === 0) {
        addToast({ type: "warning", message: "Aucun résultat trouvé." });
      } else {
        addToast({ type: "success", message: `${result.results.length} résultats trouvés.` });
      }
    } catch (err) {
      addToast({
        type: "error",
        message: `Échec : ${err instanceof Error ? err.message : "erreur inconnue"}`,
      });
    } finally {
      setSearching(false);
    }
  };

  const toggleUrl = (url: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(url)) next.delete(url); else next.add(url);
      return next;
    });
  };

  const selectAll = () => {
    if (!searchResult) return;
    if (selectedUrls.size === searchResult.results.length) {
      setSelectedUrls(new Set());
    } else {
      setSelectedUrls(new Set(searchResult.results.map((r) => r.url)));
    }
  };

  const openUrl = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          className="flex-1"
          placeholder="Rechercher (osint, CVE, recon, sécurité...)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
        />
        <Button variant="primary" onClick={runSearch} disabled={searching || !query.trim()}>
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          <span className="ml-1 hidden sm:inline">{searching ? "..." : "Rechercher"}</span>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line-1 bg-bg-1 p-3">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-foreground-tertiary" />
          <label className="text-xs text-foreground-secondary">Moteur :</label>
          <select
            className="h-8 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm"
            value={engine}
            onChange={(e) => setEngine(e.target.value)}
          >
            {engines.map((eng) => (
              <option key={eng.id} value={eng.id}>{eng.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-foreground-secondary">Max :</label>
          <input
            type="number"
            min={1}
            max={50}
            className="h-8 w-16 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm"
            value={maxResults}
            onChange={(e) => setMaxResults(Math.max(1, Math.min(50, parseInt(e.target.value) || 10)))}
          />
        </div>
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-foreground-tertiary" />
          <label className="text-xs text-foreground-secondary">Network Profile :</label>
          <select
            className="h-8 max-w-64 rounded-lg border border-line-1 bg-bg-1 px-2 text-sm"
            value={networkProfile}
            onChange={(e) => setNetworkProfile(e.target.value)}
          >
            {(profiles.length > 0
              ? profiles
              : [{
                  id: "direct",
                  type: "direct",
                  host: null,
                  port: null,
                  timeout_seconds: 10,
                  enabled: true,
                  has_credentials: false,
                }]
            ).map((p) => (
              <option key={p.id} value={p.id} disabled={!p.enabled}>
                {p.id === "direct"
                  ? "Direct"
                  : `${p.id} (${p.type.toUpperCase()}${p.host ? ` ${p.host}:${p.port ?? ""}` : ""})${p.type === "vpn" ? " — intégration à venir" : ""}${p.enabled ? "" : " — désactivé"}`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {searchResult && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-foreground-secondary">
            <span>
              {searchResult.total_found} résultats en {searchResult.search_time_ms}ms
              {searchResult.metadata?.error != null && (
                <span className="ml-2 text-amber-500">(Erreur: {String(searchResult.metadata.error)})</span>
              )}
            </span>
            <button
              onClick={selectAll}
              className="flex items-center gap-1 text-xs text-foreground-tertiary hover:text-foreground"
            >
              {selectedUrls.size === searchResult.results.length ? (
                <CheckSquare className="h-3 w-3" />
              ) : (
                <Square className="h-3 w-3" />
              )}
              {selectedUrls.size === searchResult.results.length ? "Désélectionner" : "Tout sélectionner"}
            </button>
          </div>

          {searchResult.results.map((result, idx) => (
            <div
              key={`${result.url}-${idx}`}
              className={`group relative rounded-lg border p-3 transition-colors ${
                selectedUrls.has(result.url)
                  ? "border-accent-600 bg-accent-600/10"
                  : "border-line-1 bg-bg-1 hover:border-line-2"
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => toggleUrl(result.url)}
                  className="mt-0.5 shrink-0"
                >
                  {selectedUrls.has(result.url) ? (
                    <CheckSquare className="h-4 w-4 text-accent-600" />
                  ) : (
                    <Square className="h-4 w-4 text-foreground-tertiary" />
                  )}
                </button>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openUrl(result.url)}
                      className="text-sm font-medium text-foreground hover:text-accent-500 truncate"
                    >
                      {result.title || result.url}
                    </button>
                    <ExternalLink className="h-3 w-3 shrink-0 text-foreground-tertiary" />
                  </div>
                  <p className="mt-0.5 text-xs text-foreground-secondary line-clamp-2">
                    {result.snippet}
                  </p>
                                    <div className="mt-1 flex items-center gap-2 text-xs text-foreground-tertiary">
                    <span>{result.domain || (result.url ? new URL(result.url).hostname : "")}</span>
                    <span>•</span>
                    <span>{result.source_engine}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedUrls.size > 0 && (
        <div className="flex items-center gap-2 rounded-lg border border-line-1 bg-bg-1 p-3">
          <span className="text-sm text-foreground-secondary">
            {selectedUrls.size} page{selectedUrls.size > 1 ? "s" : ""} sélectionnée{selectedUrls.size > 1 ? "s" : ""}
          </span>
          <Button variant="primary" size="sm" onClick={() => {
            addToast({ type: "info", message: "Import vers Knowledge à venir." });
          }}>
            Importer vers Knowledge
          </Button>
          <Button variant="secondary" size="sm" onClick={() => {
            addToast({ type: "info", message: "Import vers Skills à venir." });
          }}>
            Importer vers Skills
          </Button>
        </div>
      )}
    </div>
  );
}

export type { SearchResponse, SearchResult, SearchEngine };

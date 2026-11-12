"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle } from "lucide-react";
import { listApplicationIntegrationCatalog, type ApplicationCatalogItem, type CatalogState } from "@/lib/api/application-integration-catalog";

function stateLabel(value: boolean | null | string): string {
  if (value === null) return "Inconnu";
  if (value === true) return "Confirmé";
  if (value === false) return "Non confirmé";
  if (value === "unknown") return "Inconnu";
  return String(value).charAt(0).toUpperCase() + String(value).slice(1);
}

function stateClass(value: boolean | null | string): string {
  if (value === "unknown" || value === null) return "bg-muted text-foreground-tertiary";
  if (value === "validated" || value === true) return "bg-success/10 text-success";
  if (value === "invalid" || value === false) return "bg-danger/10 text-danger";
  return "bg-muted text-foreground-secondary";
}

export function ApplicationCatalog() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["application-integration-catalog"],
    queryFn: () => listApplicationIntegrationCatalog(),
  });

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Catalogue d'intégration applicative</h2>
          <p className="text-xs text-foreground-tertiary">
            Projection read-only des applications découvertes et validées par le Core.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refetch()}
          className="rounded-lg border border-line-1 bg-muted px-3 py-1.5 text-xs text-foreground-secondary transition-colors hover:bg-accent/10"
        >
          Actualiser
        </button>
      </div>

      {isLoading && (
        <div className="flex h-full items-center justify-center text-sm text-foreground-tertiary">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Chargement du catalogue…
        </div>
      )}

      {!isLoading && error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error instanceof Error ? error.message : "Erreur de chargement"}</span>
        </div>
      )}

      {!isLoading && !error && data && data.items.length === 0 && (
        <div className="rounded-lg border border-line-1 bg-bg-1 p-6 text-center text-sm text-foreground-tertiary">
          Aucune application découverte.
        </div>
      )}

      {!isLoading && !error && data && data.source_errors.length > 0 && (
        <div className="mb-3 rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs text-warning">
          {data.source_errors.join("; ")}
        </div>
      )}

      <div className="grid min-h-0 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {data?.items.map((item) => (
          <div key={item.repository_path} className="rounded-xl border border-line-1 bg-bg-1 p-4">
            <div className="mb-2 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-sm font-semibold text-foreground">{item.repository_name}</h3>
                <p className="truncate text-xs text-foreground-tertiary">{item.repository_path}</p>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] ${stateClass(item.states.validated)}`}>
                {stateLabel(item.states.validated)}
              </span>
            </div>

            <div className="mb-2 text-xs text-foreground-secondary">
              {item.manifest_validation_status === "valid"
                ? "Manifeste validé"
                : `Manifeste : ${item.manifest_validation_status}`}
            </div>

            <div className="mb-3 flex flex-wrap gap-1.5">
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-foreground-secondary">
                {item.application_type || "type inconnu"}
              </span>
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-foreground-secondary">
                {item.declared_capabilities.length > 0 ? item.declared_capabilities.join(", ") : "aucune capacité déclarée"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-1 text-[10px] text-foreground-tertiary">
              {([
                ["Découverte", item.states.discovered],
                ["Validé", item.states.validated],
                ["Enregistré", item.states.registered],
                ["Installé", item.states.installed],
                ["Actif", item.states.running],
                ["Autorisé", item.states.authorized],
              ] as Array<[string, CatalogState]>).map(([label, value]) => (
                <div key={label} className="flex items-center gap-1">
                  <span>{label}:</span>
                  <span>{stateLabel(value)}</span>
                </div>
              ))}
            </div>

            {item.errors.length > 0 && (
              <div className="mt-3 rounded-lg border border-warning/30 bg-warning/10 p-2 text-xs text-warning">
                {item.errors.join("; ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

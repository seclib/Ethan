"use client";

/**
 * Page Cookbook — galerie de recettes installables en 1 clic (RFC-0003).
 * Une recette n'exécute jamais de code : elle crée des records
 * (prompts/skills/automations) via ETHAN Core.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listRecipes, installRecipe, uninstallRecipe, type RecipeSummary,
} from "@/lib/api/extensions";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { BookOpen, Download, Trash2 } from "lucide-react";

export default function CookbookPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: recipes = [], isLoading } = useQuery({
    queryKey: ["cookbook-recipes"],
    queryFn: listRecipes,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["cookbook-recipes"] });

  const install = useMutation({
    mutationFn: installRecipe,
    onSuccess: (_d, id) => { addToast({ type: "success", message: `Recette « ${id} » installée` }); invalidate(); },
    onError: (e: Error) => addToast({ type: "error", message: e.message }),
  });
  const uninstall = useMutation({
    mutationFn: uninstallRecipe,
    onSuccess: (_d, id) => { addToast({ type: "success", message: `Recette « ${id} » désinstallée` }); invalidate(); },
    onError: (e: Error) => addToast({ type: "error", message: e.message }),
  });

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)" }}>
        <h1 style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 18, color: "var(--fg)" }}>
          <BookOpen size={18} /> Cookbook
        </h1>
        <p style={{ fontSize: 12, opacity: 0.7 }}>
          Workflows préconfigurés — installation en 1 clic de prompts, skills et automations.
        </p>
      </header>

      <div className="custom-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
        {isLoading && <p style={{ opacity: 0.6 }}>Chargement…</p>}
        {!isLoading && recipes.length === 0 && (
          <p style={{ opacity: 0.6 }}>Aucune recette disponible.</p>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
          {recipes.map((r: RecipeSummary) => (
            <div key={r.id} className="panel" style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <h3 style={{ fontSize: 14, color: "var(--fg)" }}>{r.name}</h3>
                <span style={{ fontSize: 11, opacity: 0.6 }}>v{r.version}</span>
              </div>
              <p style={{ fontSize: 12, opacity: 0.75, margin: "8px 0" }}>{r.description || "—"} </p>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "10px 0" }}>
                {Object.entries(r.installs_summary).map(([kind, n]) => (
                  <span key={kind} style={{ fontSize: 11, border: "1px solid var(--border)", borderRadius: 999, padding: "2px 8px" }}>
                    {n} {kind}{n > 1 ? "s" : ""}
                  </span>
                ))}
              </div>
              {r.installed ? (
                <Button
                  variant="outline"
                  disabled={uninstall.isPending}
                  onClick={() => uninstall.mutate(r.id)}
                  style={{ width: "100%", gap: 6 }}
                >
                  <Trash2 size={14} /> Désinstaller
                </Button>
              ) : (
                <Button
                  disabled={install.isPending}
                  onClick={() => install.mutate(r.id)}
                  style={{ width: "100%", gap: 6 }}
                >
                  <Download size={14} /> Installer
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
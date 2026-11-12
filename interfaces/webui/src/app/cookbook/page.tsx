"use client";

/**
 * Page Cookbook — galerie de recettes installables en 1 clic (RFC-0003).
 * Une recette n'exécute jamais de code : elle crée des records
 * (prompts/skills/automations) via ETHAN Core.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listRecipes, getRecipeDetail, installRecipe, uninstallRecipe,
  type RecipeSummary, type RecipeDetail, type RecipeInstallItem,
} from "@/lib/api/extensions";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Search, TriangleAlert, CircleCheck } from "lucide-react";
import { BookOpen, Download, Trash2 } from "lucide-react";

const INSTALL_KIND_LABELS: Record<string, string> = {
  prompt: "Prompts",
  skill: "Skills",
  automation: "Automations",
};

const REQUIRE_KIND_LABELS: Record<string, string> = {
  skill: "Skill",
  tool: "Tool",
  mcp: "Serveur MCP",
  model: "Modèle",
  knowledge: "Base de connaissance",
};

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

  // ── Recherche + filtre par tag ────────────────────────────────────────
  const [search, setSearch] = React.useState("");
  const [activeTag, setActiveTag] = React.useState<string | null>(null);

  const allTags = React.useMemo(() => {
    // Les tags vivent au niveau détail (agrégés côté Core) ; pour la galerie
    // on filtre sur name/description, et les tags sont chargés paresseusement.
    return [] as string[];
  }, []);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return recipes;
    return recipes.filter(
      (r) => r.name.toLowerCase().includes(q) || (r.description || "").toLowerCase().includes(q),
    );
  }, [recipes, search]);

  // ── Détail recette ────────────────────────────────────────────────────
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const detailQuery = useQuery({
    queryKey: ["cookbook-recipe", detailId],
    queryFn: () => getRecipeDetail(detailId as string),
    enabled: detailId !== null,
  });
  const closeDetail = (open: boolean) => { if (!open) setDetailId(null); };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
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
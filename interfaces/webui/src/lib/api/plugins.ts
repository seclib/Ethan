"use client";

/**
 * ETHAN WebUI — Plugins API service
 *
 * Client HTTP fin sur les routes /v1/plugins de l'API ETHAN
 * (interfaces/api/routers/v1.py), qui délèguent au CoreWebUIStore du Core
 * (core/state/webui_store.py). Aucune logique métier ici.
 *
 * Capacités réellement exposées par l'API :
 *   GET  /v1/plugins              — liste
 *   GET  /v1/plugins/{id}         — informations plugin
 *   POST /v1/plugins/install      — installation ({id?, name})
 *   PUT  /v1/plugins/{id}/toggle  — activation/désactivation
 * Pas de route delete/update : le WebUI ne doit pas les simuler.
 */

import { apiFetch } from "@/lib/api/client";

export interface PluginInfo {
  id: string;
  name: string;
  /** "active" | "inactive" — arbitré par le Core (toggle_plugin). */
  status: string;
  version: string;
}

/** Liste des plugins connus du Core (défauts + installés). */
export function listPlugins(): Promise<PluginInfo[]> {
  return apiFetch<PluginInfo[]>("/v1/plugins");
}

/** Informations à jour d'un plugin. */
export function getPlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}`);
}

/**
 * Installe un plugin. Le Core crée l'enregistrement en statut « inactive » ;
 * si `id` est omis, le Core en génère un (uuid4).
 */
export function installPlugin(data: { id?: string; name: string }): Promise<PluginInfo> {
  return apiFetch<PluginInfo>("/v1/plugins/install", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Active/désactive un plugin (bascule gérée par le Core). 404 si inconnu. */
export function togglePlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}/toggle`, {
    method: "PUT",
  });
}

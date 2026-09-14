"use client";

/**
 * ETHAN WebUI — Plugins API service
 *
 * Client HTTP fin sur les routes /v1/plugins de l'API ETHAN
 * (interfaces/api/routers/v1.py), qui délèguent au PluginRegistry du Core
 * (core/plugins). Aucune logique métier ici : le WebUI affiche et envoie
 * les actions, le Core arbitre (catalogue, états, permissions).
 *
 * Routes réellement exposées :
 *   GET    /v1/plugins                          — vue fusionnée catalogue+état
 *   GET    /v1/plugins/categories               — catégories dynamiques
 *   GET    /v1/plugins/{id}                     — détail (manifest + état)
 *   GET    /v1/plugins/{id}/permissions         — permissions déclarées+effectives
 *   GET    /v1/plugins/{id}/capabilities        — capacités + tools résolus
 *   POST   /v1/plugins/install                  — compat {id?|name}
 *   POST   /v1/plugins/{id}/install             — installation catalogue
 *   POST   /v1/plugins/{id}/enable|disable      — activation
 *   PUT    /v1/plugins/{id}/toggle              — compat
 *   POST   /v1/plugins/{id}/connect             — connexion (jamais de secret)
 *   DELETE /v1/plugins/{id}/connection          — déconnexion
 */

import { apiFetch } from "@/lib/api/client";

export interface PluginConfigField {
  key: string;
  label: string;
  type: string;
  required: boolean;
  secret: boolean;
  options: string[];
  description: string;
}

export interface PluginAuthentication {
  type: string;
  scopes: string[];
  env_vars: string[];
  instructions: string;
}

/** Vue fusionnée manifest Core + état (retour GET /v1/plugins et /{id}). */
export interface PluginInfo {
  id: string;
  name: string;
  description: string;
  author: string;
  icon: string;
  version: string;
  categories: string[];
  capabilities: string[];
  tools: string[];
  skills: string[];
  mcp: string[];
  permissions: string[];
  configuration: PluginConfigField[];
  authentication: PluginAuthentication;
  featured: boolean;
  source: string; // "builtin" | "custom"
  // État arbitré par le Core :
  status: string; // "available" | "active" | "inactive"
  installed: boolean;
  connected: boolean;
  connected_at?: string | null;
  installed_at?: string | null;
  last_used_at?: string | null;
}

export interface PluginCategory {
  id: string;
  label: string;
  count: string;
}

export interface PluginPermissions {
  plugin_id: string;
  declared: string[];
  effective_from_tools: string[];
  granted: string[];
  authentication: PluginAuthentication;
}

export interface PluginCapabilities {
  plugin_id: string;
  capabilities: string[];
  tools: { id: string; name: string; available: boolean; risk_level?: string }[];
  skills: string[];
  mcp: string[];
}

export interface PluginConnectResult extends PluginInfo {
  connected: boolean;
  missing_configuration?: string[];
  message?: string;
}

/** Liste des plugins connus du Core (catalogue + custom/legacy). */
export function listPlugins(): Promise<PluginInfo[]> {
  return apiFetch<PluginInfo[]>("/v1/plugins");
}

/** Catégories dynamiques dérivées du catalogue Core. */
export function getPluginCategories(): Promise<{ categories: PluginCategory[] }> {
  return apiFetch<{ categories: PluginCategory[] }>("/v1/plugins/categories");
}

/** Détail à jour d'un plugin. 404 si inconnu. */
export function getPlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}`);
}

/** Permissions : déclarées (manifest) + effectives (ToolRegistry réelle). */
export function getPluginPermissions(pluginId: string): Promise<PluginPermissions> {
  return apiFetch<PluginPermissions>(
    `/v1/plugins/${encodeURIComponent(pluginId)}/permissions`,
  );
}

/** Capacités : capabilities + tools résolus + skills + mcp. */
export function getPluginCapabilities(pluginId: string): Promise<PluginCapabilities> {
  return apiFetch<PluginCapabilities>(
    `/v1/plugins/${encodeURIComponent(pluginId)}/capabilities`,
  );
}

/**
 * Installe un plugin du catalogue. Le Core crée l'enregistrement en statut
 * « inactive » ; l'installation seule n'active rien (principe de moindre
 * privilège). Compat : si `id` est omis, le Core enregistre un custom.
 */
export function installPlugin(data: { id?: string; name?: string }): Promise<PluginInfo> {
  return apiFetch<PluginInfo>("/v1/plugins/install", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Active un plugin installé. */
export function enablePlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}/enable`, {
    method: "POST",
  });
}

/** Désactive un plugin actif. */
export function disablePlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}/disable`, {
    method: "POST",
  });
}

/** Bascule activation/désactivation (arbitrage Core). 404 si inconnu. */
export function togglePlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}/toggle`, {
    method: "PUT",
  });
}

/**
 * Connecte un plugin (état de connexion géré par le Core). Les champs
 * `secret` ne transitent JAMAIS ici : ils vivent dans la couche secret
 * manager (env/Vault). `config` ne contient que des valeurs non secrètes.
 */
export function connectPlugin(
  pluginId: string,
  config?: Record<string, string>,
): Promise<PluginConnectResult> {
  return apiFetch<PluginConnectResult>(
    `/v1/plugins/${encodeURIComponent(pluginId)}/connect`,
    {
      method: "POST",
      body: JSON.stringify({ config: config ?? {} }),
    },
  );
}

/** Déconnecte un plugin (l'installation et la configuration sont conservées). */
export function disconnectPlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(
    `/v1/plugins/${encodeURIComponent(pluginId)}/connection`,
    { method: "DELETE" },
  );
}


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
  /** Version du manifest au moment de l'installation (sync Core). */
  manifest_version?: string | null;
  /** true si le catalogue Core propose une version plus récente. */
  update_available?: boolean;
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

/** Met à jour un plugin installé (synchronisation manifest du catalogue Core). */
export function updatePlugin(pluginId: string): Promise<PluginInfo> {
  return apiFetch<PluginInfo>(`/v1/plugins/${encodeURIComponent(pluginId)}/update`, {
    method: "POST",
  });
}

export interface PluginUninstallResult {
  id: string;
  name: string;
  uninstalled: boolean;
  /** true : la configuration et les permissions accordées ont été supprimées. */
  data_removed: boolean;
  status: string;
  installed: boolean;
  /** Secrets à révoquer manuellement dans le secret manager (jamais touchés ici). */
  secrets_to_revoke: string[];
}

/**
 * Désinstalle un plugin. `removeData=false` conserve la configuration non
 * secrète (réinstallation sans re-saisie) ; `removeData=true` supprime aussi
 * les données du plugin dans le store Core. Les secrets restent dans la
 * couche secret manager — voir `secrets_to_revoke`.
 */
export function uninstallPlugin(
  pluginId: string,
  removeData: boolean,
): Promise<PluginUninstallResult> {
  const qs = removeData ? "?remove_data=true" : "";
  return apiFetch<PluginUninstallResult>(
    `/v1/plugins/${encodeURIComponent(pluginId)}${qs}`,
    { method: "DELETE" },
  );
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

/** État réel du service applicatif Odin (routeur dédié). */
export interface OdinStatus {
  id: string;
  name: string;
  status: "not_installed" | "installed_stopped" | "starting" | "running" | "degraded" | "stopping" | "error" | "unknown";
  port: number;
  host: string;
  url: string;
  container_id?: string | null;
  healthy: boolean;
  mcp_tools_count?: number | null;
  error?: string | null;
  updated_at?: string;
  allowed_actions: string[];
  container_stats?: {
    cpu_percent: number;
    memory_usage: string;
    memory_percent: number;
    network_io: string;
    block_io: string;
  };
  details?: {
    compose_file?: string;
    repo_dir?: string;
    container_info?: Record<string, unknown>;
  };
}

/** GET /v1/plugins/odin/status — état réel vérifié. */
export function getOdinStatus(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/status");
}

/** POST /v1/plugins/odin/start — démarrage confiné. */
export function startOdin(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/start", {
    method: "POST",
  });
}

/** POST /v1/plugins/odin/stop — arrêt sans suppression. */
export function stopOdin(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/stop", {
    method: "POST",
  });
}

/** POST /v1/plugins/odin/restart — redémarrage confiné. */
export function restartOdin(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/restart", {
    method: "POST",
  });
}

/** POST /v1/plugins/odin/install — installation du service Odin. */
export function installOdin(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/install", {
    method: "POST",
  });
}

/** POST /v1/plugins/odin/uninstall — désinstallation du service Odin. */
export function uninstallOdin(): Promise<OdinStatus> {
  return apiFetch<OdinStatus>("/v1/plugins/odin/uninstall", {
    method: "POST",
  });
}

/** Logs récents du service Odin (tail limité, secrets redactés). */
export interface OdinLogs {
  status: string;
  logs: string;
  total_lines: number;
  redacted: boolean;
  fetched_at: string;
  error?: string | null;
}

/** GET /v1/plugins/odin/logs — logs récents du service. */
export function getOdinLogs(tail = 100): Promise<OdinLogs> {
  return apiFetch<OdinLogs>(
    `/v1/plugins/odin/logs?tail=${tail}`,
  );
}

/** Vérification détaillée de santé du service (TCP + conteneur). */
export interface OdinHealth {
  status: string;
  healthy: boolean;
  reachable: boolean;
  tcp_probe: boolean;
  container_state: string;
  container_health?: string;
  port: number;
  host: string;
  url: string;
  last_transition: string;
  checked_at: string;
}

/** GET /v1/plugins/odin/health — vérification détaillée de santé. */
export function getOdinHealth(): Promise<OdinHealth> {
  return apiFetch<OdinHealth>("/v1/plugins/odin/health");
}

/* ── Configuration Odin (persiste via ConfigurationService) ── */

/** Configuration IA Odin (modèle, provider, limites). */
export interface OdinAIConfig {
  default_model: string | null;
  default_provider: string | null;
  context_limit: number;
  timeout_seconds: number;
}

/** Configuration voix Odin (TTS/STT). */
export interface OdinVoiceConfig {
  tts_provider: string;
  tts_voice: string;
  tts_speed: number;
  stt_enabled: boolean;
}

/** Configuration API externe Odin. */
export interface OdinAPIConfig {
  api_base_url: string | null;
  api_timeout_seconds: number;
  api_retry_count: number;
}

/** GET /v1/plugins/odin/ai/config — configuration IA Odin. */
export function getOdinAIConfig(): Promise<{ config: OdinAIConfig; allowed_models: any[]; voice_fallback: string }> {
  return apiFetch("/v1/plugins/odin/ai/config");
}

/** PUT /v1/plugins/odin/ai/config — mettre à jour la config IA Odin. */
export function updateOdinAIConfig(body: Partial<OdinAIConfig>): Promise<{ config: OdinAIConfig }> {
  return apiFetch<{ config: OdinAIConfig }>("/v1/plugins/odin/ai/config", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

/** GET /v1/plugins/odin/ai/voice-config — configuration voix Odin. */
export function getOdinVoiceConfig(): Promise<OdinVoiceConfig> {
  return apiFetch<OdinVoiceConfig>("/v1/plugins/odin/ai/voice-config");
}

/** PUT /v1/plugins/odin/ai/voice-config — mettre à jour la config voix Odin. */
export function updateOdinVoiceConfig(body: Partial<OdinVoiceConfig>): Promise<OdinVoiceConfig> {
  return apiFetch<OdinVoiceConfig>("/v1/plugins/odin/ai/voice-config", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

/** GET /v1/plugins/odin/ai/api-config — configuration API externe Odin. */
export function getOdinAPIConfig(): Promise<OdinAPIConfig> {
  return apiFetch<OdinAPIConfig>("/v1/plugins/odin/ai/api-config");
}

/** PUT /v1/plugins/odin/ai/api-config — mettre à jour la config API Odin. */
export function updateOdinAPIConfig(body: Partial<OdinAPIConfig>): Promise<OdinAPIConfig> {
  return apiFetch<OdinAPIConfig>("/v1/plugins/odin/ai/api-config", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}


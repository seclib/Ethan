"use client";

/**
 * ETHAN WebUI — Préférences utilisateur (client API).
 *
 * La source de vérité est ETHAN Core (domaine `preferences` du schéma de
 * configuration, persisté dans `ethan_config`).  Le `localStorage` du
 * navigateur ne sert plus qu'à **cache** de rendu : sans lui la page
 * clignoterait avant le premier aller-retour réseau, mais il ne décide de
 * rien.
 *
 * Routes : GET/PATCH /config/preferences (interfaces/api/routers/config.py).
 */

import { apiFetch } from "@/lib/api/client";

/** Mode conversationnel — miroir de core/chat/modes.py. */
export type ChatModeValue = "plan" | "act" | "debug";

/** Effort de raisonnement — miroir de core/chat/modes.py ReasoningEffort. */
export type ReasoningEffortValue = "none" | "low" | "medium" | "high" | "xhigh";

/** Forme exacte du domaine Core `preferences` (core/config/schema.py). */
export interface UserPreferences {
  /** Provider LLM choisi ("" = défaut Core). */
  active_provider: string;
  /** Modèle choisi ("" = défaut Core). */
  active_model: string;
  /** Agent choisi ("" = « Sans agent »). */
  active_agent: string;
  /** Derniers agents utilisés (max 3). */
  recent_agents: string[];
  /** Mode conversationnel actif. */
  chat_mode: ChatModeValue;
  /** Effort de raisonnement demandé. */
  reasoning_effort: ReasoningEffortValue;
}

export type PreferencesPatch = Partial<UserPreferences>;

/** Préférences vides — repli quand l'API est injoignable. */
export const EMPTY_PREFERENCES: UserPreferences = {
  active_provider: "",
  active_model: "",
  active_agent: "",
  recent_agents: [],
  chat_mode: "act",
  reasoning_effort: "medium",
};

/**
 * Lit les préférences persistées côté ETHAN.
 *
 * Retourne toujours un objet complet (Core fusionne ses défauts), y compris
 * quand aucune préférence n'a jamais été écrite.
 */
export async function getPreferences(): Promise<UserPreferences> {
  const raw = await apiFetch<Partial<UserPreferences>>("/config/preferences");
  return { ...EMPTY_PREFERENCES, ...raw };
}

/**
 * Persiste un correctif de préférences.
 *
 * Échec explicite (503 si le backend durable refuse l'écriture) : la valeur
 * n'est alors pas annoncée comme enregistrée et l'appelant conserve l'état
 * local comme non synchronisé.
 */
export async function patchPreferences(patch: PreferencesPatch): Promise<UserPreferences> {
  const raw = await apiFetch<Partial<UserPreferences>>("/config/preferences", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  return { ...EMPTY_PREFERENCES, ...raw };
}

/**
 * Indique si le domaine `preferences` a déjà été persisté.
 *
 * Core ne distingue pas « écrit avec la valeur par défaut » de « jamais
 * écrit ».  `GET /config/status` expose les domaines réellement stockés : c'est
 * ce qui permet de trancher entre « le serveur fait autorité » et « on remonte
 * le cache local » (première exécution après migration).
 */
export async function hasPersistedPreferences(): Promise<boolean> {
  try {
    const status = await apiFetch<{ loaded_domains?: string[] }>("/config/status");
    return Array.isArray(status.loaded_domains) &&
      status.loaded_domains.includes("preferences");
  } catch {
    // Endpoint de diagnostic absent (backend plus ancien) : on ne peut pas
    // trancher → on considère que le serveur n'a rien d'écrit.
    return false;
  }
}

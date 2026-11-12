"use client";

/**
 * ETHAN WebUI — Synchronisation des préférences utilisateur avec ETHAN Core.
 *
 * Règle d'architecture (AGENTS.md) : une capacité d'ETHAN appartient à Core,
 * jamais à son interface.  Le modèle actif, l'agent actif et le mode de chat
 * sont donc persistés par Core (domaine `preferences` de
 * `core/config/schema.py`, table `ethan_config`), et non par le navigateur.
 *
 * Le `localStorage` (middleware `persist` de zustand) reste en place
 * uniquement comme **cache de rendu** : il évite un clignotement au premier
 * paint et garde un état affichable hors-ligne.  Il ne décide de rien.
 *
 * Rèconciliation à l'ouverture :
 *   1. `GET /config/status` → le domaine `preferences` est-il persisté ?
 *   2. oui  → le serveur fait autorité, on écrase le cache local ;
 *   3. non  → première exécution : le cache local fait foi et est remonté.
 * Ensuite tout changement local est PATCHé (debounce) et l'état renvoyé par le
 * serveur devient la nouvelle référence de comparaison.
 */

import { useEffect, useRef, type ReactNode } from "react";

import { logger } from "@/lib/logger";
import {
  EMPTY_PREFERENCES,
  getPreferences,
  hasPersistedPreferences,
  patchPreferences,
  type PreferencesPatch,
  type UserPreferences,
} from "@/lib/api/preferences";
import { useAuth } from "@/providers/auth-provider";
import { useAgentStore } from "@/store/agent.store";
import { useChatModeStore } from "@/store/chat-mode.store";
import { useModelStore } from "@/store/model.store";

/** Délai avant écriture serveur : fusionne les rafales de clics. */
const SYNC_DEBOUNCE_MS = 500;

const CHAT_MODES = new Set<string>(["plan", "act", "debug"]);
const REASONING_EFFORTS = new Set<string>(["none", "low", "medium", "high", "xhigh"]);

/** Rejet d'une valeur serveur hors schéma (backend corrompu / ancien). */
function oneOf(value: unknown, allowed: Set<string>, fallback: string): string {
  return typeof value === "string" && allowed.has(value) ? value : fallback;
}

function sanitize(raw: Partial<UserPreferences> | null | undefined): UserPreferences {
  const source = raw ?? EMPTY_PREFERENCES;
  return {
    active_provider: typeof source.active_provider === "string" ? source.active_provider : "",
    active_model: typeof source.active_model === "string" ? source.active_model : "",
    active_agent: typeof source.active_agent === "string" ? source.active_agent : "",
    recent_agents: Array.isArray(source.recent_agents)
      ? source.recent_agents.filter((id): id is string => typeof id === "string").slice(0, 3)
      : [],
    chat_mode: oneOf(source.chat_mode, CHAT_MODES, EMPTY_PREFERENCES.chat_mode) as
      UserPreferences["chat_mode"],
    reasoning_effort: oneOf(
      source.reasoning_effort,
      REASONING_EFFORTS,
      EMPTY_PREFERENCES.reasoning_effort,
    ) as UserPreferences["reasoning_effort"],
  };
}

/** État actuel des trois stores → forme du domaine Core `preferences`. */
function readStores(): UserPreferences {
  const model = useModelStore.getState();
  const agent = useAgentStore.getState();
  const chat = useChatModeStore.getState();
  return sanitize({
    active_provider: model.selectedProviderId,
    active_model: model.selectedModel,
    active_agent: agent.selectedAgentId ?? "",
    recent_agents: agent.recentAgentIds,
    chat_mode: chat.mode,
    reasoning_effort: chat.reasoningEffort,
  });
}

/** Applique l'état serveur dans les stores (le serveur fait autorité). */
function applyServer(prefs: UserPreferences): void {
  useModelStore.setState({
    selectedProviderId: prefs.active_provider,
    selectedModel: prefs.active_model,
  });
  useAgentStore.setState({
    selectedAgentId: prefs.active_agent || null,
    recentAgentIds: prefs.recent_agents.slice(0, 3),
  });
  useChatModeStore.setState({
    mode: prefs.chat_mode,
    reasoningEffort: prefs.reasoning_effort,
  });
}

function toPatch(prefs: UserPreferences): PreferencesPatch {
  return {
    active_provider: prefs.active_provider,
    active_model: prefs.active_model,
    active_agent: prefs.active_agent,
    recent_agents: prefs.recent_agents,
    chat_mode: prefs.chat_mode,
    reasoning_effort: prefs.reasoning_effort,
  };
}


export function PreferencesProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  /** Vrai une fois la rèconciliation serveur terminée (ou abandonnée). */
  const hydratedRef = useRef(false);
  /** Dernier état connu du serveur — détecte un vrai changement. */
  const syncedRef = useRef<string>("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** Bloque les écritures serveur pendant l'application de l'état distant. */
  const applyingRef = useRef(false);

  // ── 1. Rèconciliation au démarrage ──────────────────────────────────────
  useEffect(() => {
    if (isLoading || !isAuthenticated) return;

    let cancelled = false;
    hydratedRef.current = false;

    (async () => {
      try {
        const [persisted, serverRaw] = await Promise.all([
          hasPersistedPreferences(),
          getPreferences(),
        ]);
        if (cancelled) return;

        const server = sanitize(serverRaw);
        syncedRef.current = JSON.stringify(server);

        if (persisted) {
          // Le serveur a déjà une valeur : elle gagne sur le cache local.
          applyingRef.current = true;
          applyServer(server);
          applyingRef.current = false;
        } else {
          // Première exécution (rien d'écrit) : le cache local fait foi et
          // devient l'état initial du serveur.
          const seed = readStores();
          try {
            const saved = await patchPreferences(toPatch(seed));
            if (!cancelled) syncedRef.current = JSON.stringify(sanitize(saved));
          } catch (error) {
            // Backend durable indisponible : le cache local reste affiché,
            // la prochaine ouverture retentera la remontée.
            logger.warn("Preferences seed failed (kept local):", error);
          }
        }
      } catch (error) {
        // API injoignable / non authentifié : on garde le cache local tel quel.
        logger.warn("Preferences reconciliation skipped:", error);
      } finally {
        if (!cancelled) hydratedRef.current = true;
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLoading, isAuthenticated]);

  // ── 2. Écriture des changements locaux ──────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated) return;

    const schedule = () => {
      if (!hydratedRef.current || applyingRef.current) return;
      const next = readStores();
      const serialized = JSON.stringify(next);
      if (serialized === syncedRef.current) return;

      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        void (async () => {
          try {
            const saved = await patchPreferences(toPatch(next));
            syncedRef.current = JSON.stringify(sanitize(saved));
          } catch (error) {
            // 503 = non persisté : on ne met PAS à jour la référence, la
            // prochaine mutation retentera.  L'UI ne ment jamais sur un
            // enregistrement qui n'a pas eu lieu.
            logger.warn("Preferences not persisted:", error);
          }
        })();
      }, SYNC_DEBOUNCE_MS);
    };

    const unsubscribes = [
      useModelStore.subscribe(schedule),
      useAgentStore.subscribe(schedule),
      useChatModeStore.subscribe(schedule),
    ];

    return () => {
      unsubscribes.forEach((unsubscribe) => unsubscribe());
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isAuthenticated]);

  return <>{children}</>;
}


"use client";

/**
 * use-external-service — health-check léger des services d'observabilité
 * externes (Grafana) référencés dans la navigation.
 *
 * Correctif audit UX (P2-2) : les liens Grafana en dur (localhost:3002)
 * menaient à une erreur navigateur si le service était arrêté, sans feedback.
 * Le hook tente une requête `no-cors` sur `/api/health` (résultat opaque mais
 * rejeté en cas d'échec réseau) et expose l'état : null = inconnu (test en
 * cours), true = joignable, false = injoignable. Le résultat est caché au
 * niveau module pour ne sonder qu'une fois par session.
 *
 * AGENTS.md : pure UX (affichage d'état) — aucune logique métier.
 */

import * as React from "react";

const cache = new Map<string, boolean>();

export function useExternalServiceHealth(
  baseUrl: string,
  timeoutMs = 3000,
): boolean | null {
  const [reachable, setReachable] = React.useState<boolean | null>(
    () => cache.get(baseUrl) ?? null,
  );

  React.useEffect(() => {
    const cached = cache.get(baseUrl);
    if (cached !== undefined) {
      setReachable(cached);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    fetch(`${baseUrl}/api/health`, { mode: "no-cors", signal: controller.signal })
      .then(() => {
        if (!cancelled) {
          cache.set(baseUrl, true);
          setReachable(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          cache.set(baseUrl, false);
          setReachable(false);
        }
      })
      .finally(() => clearTimeout(timer));

    return () => {
      cancelled = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [baseUrl, timeoutMs]);

  return reachable;
}
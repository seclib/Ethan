"use client";

/**
 * ETHAN WebUI — Valeurs temporelles déterministes (compatibles SSR/hydratation).
 *
 * Problème résolu — React #418 (« server rendered text didn't match the
 * client ») :
 *
 *   Un composant qui calcule `new Date()` pendant le rendu produit un contenu
 *   différent au serveur et au client. Sur une page **prérendue statiquement**
 *   (le cas de `/login` et de `/calendar`), le serveur fige la date **au
 *   moment du build** dans le HTML, alors que le client recalcule la date
 *   **à l'hydratation** : les deux rendus divergent et React signale un
 *   mismatch d'hydratation, puis régénère l'arbre côté client.
 *
 * Correction — le premier rendu client doit être identique au HTML serveur :
 *
 *   1. L'état initial est **stable**, identique côté serveur et côté client →
 *      aucune divergence au premier rendu.
 *   2. La valeur réelle n'est lue qu'**après le montage** (effet), donc après
 *      l'hydratation : elle apparaît sans jamais contredire le HTML statique.
 *   3. Les mises à jour périodiques ne concernent que le contenu, jamais la
 *      structure du DOM.
 *
 * Ce module ne désactive ni l'hydratation ni le prérendu : le SSR et le
 * prérendu statique restent intacts, et les valeurs réelles s'affichent une
 * fois la page montée.
 *
 * Point d'entrée centralisé de la WebUI pour toute valeur dépendante du
 * temps : y verser les autres horloges/calendriers plutôt que de dupliquer
 * le mécanisme.
 */

import { useEffect, useState } from "react";

/** Placeholder rendu au premier passage (serveur + client) — largeur stable. */
export const UTC_CLOCK_PLACEHOLDER = "--:--:-- UTC";

/** Formate une date en horodatage UTC lisible (identique serveur/client). */
export function formatUTC(date: Date): string {
  return date
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z/, " UTC");
}

/**
 * Horloge UTC qui ne diverge jamais entre le rendu serveur et le premier
 * rendu client.
 *
 * @returns l'horodatage UTC courant, ou `UTC_CLOCK_PLACEHOLDER` tant que le
 *          composant n'est pas monté (c'est-à-dire au premier rendu serveur
 *          et au premier rendu client — identiques par construction).
 */
export function useUtcClock(intervalMs = 1000): string {
  const [utcTime, setUtcTime] = useState<string>(UTC_CLOCK_PLACEHOLDER);

  useEffect(() => {
    // L'heure réelle n'est lue qu'après l'hydratation : le HTML prérendu
    // (figé au build) n'est jamais contredit.
    const tick = () => setUtcTime(formatUTC(new Date()));
    tick();
    const interval = setInterval(tick, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs]);

  return utcTime;
}

/**
 * Date du jour, déterministe entre le rendu serveur et le premier rendu
 * client.
 *
 * Même mécanique que {@link useUtcClock} : la date réelle n'est lue qu'après
 * le montage. Un calendrier prérendu statiquement affiche donc un mois
 * « neutre » côté serveur, puis le mois courant après l'hydratation — au lieu
 * de figer le mois du build dans le HTML et de le contredire au client.
 *
 * @returns la date du jour, ou `null` tant que le composant n'est pas monté.
 */
export function useHydrationSafeToday(): Date | null {
  const [today, setToday] = useState<Date | null>(null);

  useEffect(() => {
    // `setState` dans un effet est ici VOLONTAIRE : c'est le mécanisme React
    // documenté pour lire une valeur non déterministe (l'heure du navigateur)
    // sans contredire le HTML prérendu. La valeur n'est lue qu'après
    // l'hydratation, donc le premier rendu client reste identique au rendu
    // serveur — condition nécessaire pour éviter React #418.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setToday(new Date());
  }, []);

  return today;
}

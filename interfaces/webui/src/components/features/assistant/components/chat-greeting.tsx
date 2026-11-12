"use client";

/**
 * ETHAN WebUI — ChatGreeting : en-tête de l'ÉTAT VIDE du Chat.
 *
 * Inspiration Claude Code / Claude Chat : la marque + une salutation horaire
 * + l'invite contextuelle de la section active, centrées au-dessus du
 * composer (voir AssistantChat : état vide = hero centré).
 *
 * UI-ONLY : purement présentationnel. Aucune logique métier, aucun appel
 * Core. Le nom affiché vient de la session (AuthProvider — déjà en place) ;
 * la salutation est dérivée de l'heure locale et `suppressHydrationWarning`
 * couvre le seul écart d'hydratation possible (fusion au changement de fuseau,
 * au chargement de la session).
 */

import { LogoSquare } from "@/components/shared/logo";
import { useAuth } from "@/providers/auth-provider";

/** Invite par défaut quand aucune section n'est active. */
const DEFAULT_HINT = "Posez une question, demandez une analyse, ou lancez une tâche.";

/**
 * Prénom affichable à partir du nom de session : premier segment, sans
 * domaine email, capitalisé. `null` si rien d'exploitable.
 */
export function displayName(name?: string | null): string | null {
  const raw = (name ?? "").trim();
  if (!raw) return null;
  const first = raw.split(/[\s@]+/)[0];
  if (!first) return null;
  return first.charAt(0).toUpperCase() + first.slice(1);
}

/**
 * Salutation horaire : « Bonne nuit / Bonjour / Bon après-midi / Bonsoir »,
 * suffixée du prénom réel s'il existe.
 */
export function greetingFor(date: Date, name?: string | null): string {
  const hour = date.getHours();
  const moment =
    hour < 6 ? "Bonne nuit" : hour < 12 ? "Bonjour" : hour < 18 ? "Bon après-midi" : "Bonsoir";
  const who = displayName(name);
  return who ? `${moment}, ${who}` : moment;
}

interface ChatGreetingProps {
  /** Invite contextuelle (reflet de la section active) — présentation pure. */
  hint?: string;
  className?: string;
}

export function ChatGreeting({ hint, className }: ChatGreetingProps) {
  const { user } = useAuth();

  /**
   * Calcul DIRECT (aucun état, aucun effet) : `suppressHydrationWarning`
   * absorbe le seul écart possible serveur/client — l'horloge (fuseau) — sans
   * provoquer de render supplémentaire ni de warning react-hooks.
   */
  const greeting = greetingFor(new Date(), user?.name);

  return (
    <div className={`flex flex-col items-center gap-2 px-4 text-center ${className ?? ""}`}>
      <div className="flex items-center gap-2.5">
        <LogoSquare size={30} className="rounded-lg" />
        <h1
          suppressHydrationWarning
          className="text-2xl font-medium tracking-tight text-foreground"
        >
          {greeting}
        </h1>
      </div>
      <p className="max-w-md text-sm text-muted-foreground">{hint ?? DEFAULT_HINT}</p>
    </div>
  );
}
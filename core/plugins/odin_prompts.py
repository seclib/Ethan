"""Prompts Odin — source unique (Core).

AGENTS.md : les prompts sont des *business records*. Ils vivent dans le Core,
jamais dans une interface. Odin (examples/odin) consomme ce module ;
il ne redéfinit plus ses instructions.

Ce module ne contient QUE la definition des prompts. Il n'appelie aucun
provider, ne lit aucun secret, ne fait aucun appel reseau : c'est une
constante metier partagee.

Regles :
- Un prompt existe a un seul endroit dans tout ETHAN.
- Les textes sont stables : ils font partie du contrat de sortie (le HUD
  attend exactement cinq mots).
- Toute evolution du texte doit mettre a jour les tests de contrat.
"""

from __future__ import annotations

HUD_SYSTEM_PROMPT = (
    "Write one concise intelligence-HUD summary for Odin. "
    "Use only supplied labels and feedProvenance. "
    "If any enabled layer is not nominal, include that feedState token "
    "(STALE, DEGRADED, FALLBACK, LOADING, UNAVAILABLE). "
    "Output exactly five words, no punctuation or markdown."
)

# Version longue, alignee sur l'instruction d'origine de Odin
# (src/hudSummaryResponse.js -> HUD_SUMMARY_INSTRUCTIONS). Elle precise
# l'interdiction d'inventer un lieu ou un etat de flux, que la version
# courte laissait implicite.
HUD_SUMMARY_INSTRUCTIONS = (
    "Write one concise intelligence-HUD summary for Odin. "
    "Use only the supplied place, street, nearby-place, enabled-layer labels, "
    "and feedProvenance. "
    "Prefer the clearest named place and include a relevant enabled layer "
    "only when useful. "
    "If any enabled layer is not nominal, the five words MUST include that "
    "feedState token (STALE, DEGRADED, FALLBACK, LOADING, or UNAVAILABLE) "
    "and must not present the view as live. "
    "Do not infer from coordinates or invent a place or feed state. "
    "Output exactly five words with no title, punctuation, markdown, or "
    "introductory phrase."
)

# Nombre de mots imposes dans la reponse du HUD.
HUD_SUMMARY_WORD_COUNT = 5

# Jetons d'etat de flux qu'un resume doit porter quand une couche active
# n'est pas nominale. Source unique partagee avec le client GEV.
HUD_FEED_STATE_TOKENS = (
    "STALE",
    "DEGRADED",
    "FALLBACK",
    "LOADING",
    "UNAVAILABLE",
)


def truncate_to_words(text: str, count: int = HUD_SUMMARY_WORD_COUNT) -> str:
    """Normalise une sortie de modele en ligne de ``count`` mots.

    Utilise par l'interface ETHAN (routeur plugin) comme garde-fou serveur :
    meme si le modele deborde, le HUD recoit une ligne de longueur bornee.

    :param text: texte brut produit par le provider.
    :param count: nombre de mots maximum (defaut : 5).
    :return: ligne normalisee, sans ponctuation, sans markdown.
    """
    cleaned = "".join(
        ch if (ch.isalnum() or ch.isspace() or ch == "-") else " "
        for ch in str(text or "")
    )
    words = [w for w in cleaned.split() if w]
    return " ".join(words[: max(1, int(count))])


__all__ = [
    "HUD_SYSTEM_PROMPT",
    "HUD_SUMMARY_INSTRUCTIONS",
    "HUD_SUMMARY_WORD_COUNT",
    "HUD_FEED_STATE_TOKENS",
    "truncate_to_words",
]

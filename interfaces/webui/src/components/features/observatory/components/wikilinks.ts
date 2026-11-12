/**
 * Réécriture des wikiliens [[cible]] ou [[cible|alias]] en liens internes
 * « observatory-wikilink:<cible encodée> », que le composant de rendu
 * intercepte pour résoudre la cible via GET /v1/memory/vault/resolve.
 *
 * Module pur, sans dépendance, pour rester testable côté jest sans l'ESM de
 * la chaîne react-markdown. Les zones de code (bloc et inline) sont
 * préservées telles quelles.
 */

const WIKILINK_RE = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
const CODE_FENCE_RE = /(```[\s\S]*?```)/g;
const INLINE_CODE_RE = /(`[^`\n]*`)/g;

export function rewriteWikilinks(markdown: string): string {
  // Les wikiliens ne sont réécrits que hors des zones de code (bloc et inline) —
  // le code reste littéral pour les lecteurs.
  const segments = markdown.split(CODE_FENCE_RE);
  return segments
    .map((segment, fenceIndex) => {
      if (fenceIndex % 2 === 1) return segment; // bloc de code intégral
      return segment
        .split(INLINE_CODE_RE)
        .map((part, codeIndex) => {
          if (codeIndex % 2 === 1) return part; // code inline intégral
          return part.replace(WIKILINK_RE, (_m, target: string, alias?: string) => {
            const name = alias ? alias.trim() : target.trim();
            return `[${name}](observatory-wikilink:${encodeURIComponent(target.trim())})`;
          });
        })
        .join("");
    })
    .join("");
}

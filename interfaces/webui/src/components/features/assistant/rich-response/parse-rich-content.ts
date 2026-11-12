import type { RichBlock, RichSegment } from "./types";
import { isRichBlockKind, validateRichBlock } from "./types";

/**
 * Découpe un contenu Markdown en segments standards et composants enrichis.
 *
 * Les blocs enrichis sont des blocs de code fermés dont l'infostring est l'un
 * des types pris en charge (chart, callout, kpi, status, details, diagram, ...).
 * Tout bloc de code restant est présenté normalement comme code.
 *
 * Le texte entre blocs est conservé tel quel pour le rendu Markdown standard.
 */
export function parseRichContent(content: string): RichSegment[] {
  const segments: RichSegment[] = [];
  const fenceRegex = /```([^\n`]*)\n([\s\S]*?)```/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let index = 0;

  while ((match = fenceRegex.exec(content)) !== null) {
    const before = content.slice(lastIndex, match.index);
    if (before.trim()) {
      segments.push({ id: `md-${index}`, type: "markdown", value: before });
      index += 1;
    }

    const language = match[1].trim().toLowerCase();
    const raw = match[2].replace(/\n$/, "");
    const baseLanguage = language.split(/\s+/)[0];

    if (isRichBlockKind(baseLanguage)) {
      let block: RichBlock | null = null;
      let fallback = raw;
      try {
        block = validateRichBlock(baseLanguage, raw);
      } catch {
        block = null;
      }

      if (block) {
        segments.push({ id: `rich-${index}`, type: "rich", block });
      } else {
        segments.push({
          id: `code-${index}`,
          type: "code",
          language: baseLanguage,
          code: raw,
        });
      }
    } else {
      segments.push({
        id: `code-${index}`,
        type: "code",
        language: baseLanguage || "text",
        code: raw,
      });
    }

    lastIndex = match.index + match[0].length;
    index += 1;
  }

  const tail = content.slice(lastIndex);
  if (tail.trim()) {
    segments.push({ id: `md-tail-${index}`, type: "markdown", value: tail });
  }

  if (segments.length === 0 && content.trim()) {
    segments.push({ id: "md-0", type: "markdown", value: content });
  }

  return segments;
}

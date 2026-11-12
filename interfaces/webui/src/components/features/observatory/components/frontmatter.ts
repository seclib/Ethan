/**
 * Minimal YAML-frontmatter parser for the Observatory document view.
 *
 * Display-only subset (flat keys, scalar values, simple lists). Anything
 * richer is shown raw. No parser dependency is added — the canonical source
 * stays the file itself, never a re-serialized copy.
 */

export interface Frontmatter {
  values: Array<{ key: string; value: string }>;
}

const FRONTMATTER_RE = /^---\s*\r?\n([\s\S]*?)\r?\n---\s*(\r?\n|$)/;

export function parseFrontmatter(markdown: string): Frontmatter {
  const match = markdown.match(FRONTMATTER_RE);
  if (!match) return { values: [] };
  const body = match[1];
  const values: Array<{ key: string; value: string }> = [];
  let currentKey: string | null = null;
  let listItems: string[] = [];

  const flushList = () => {
    if (currentKey !== null) {
      values.push({ key: currentKey, value: listItems.length ? listItems.join(", ") : "" });
    }
    currentKey = null;
    listItems = [];
  };

  for (const rawLine of body.split(/\r?\n/)) {
    const line = rawLine.trimEnd();
    const listItem = line.match(/^\s*-\s+(.*)$/);
    if (listItem && currentKey !== null) {
      listItems.push(stripQuotes(listItem[1].trim()));
      continue;
    }
    const kv = line.match(/^([A-Za-z0-9_.-]+):\s*(.*)$/);
    if (kv) {
      flushList();
      const key = kv[1];
      const value = stripQuotes(kv[2].trim());
      if (value === "") {
        // Might be a list following on next lines.
        currentKey = key;
        listItems = [];
      } else {
        values.push({ key, value });
      }
      continue;
    }
    // Unrecognized line: attach as continuation note of the previous key if any.
    if (currentKey !== null && line.trim()) {
      listItems.push(line.trim());
    }
  }
  flushList();
  return { values };
}

function stripQuotes(value: string): string {
  const v = value.trim();
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  return v;
}

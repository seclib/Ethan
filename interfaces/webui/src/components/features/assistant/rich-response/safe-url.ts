const SAFE_PROTOCOLS = ["http:", "https:", "mailto:", "tel:"];

/**
 * Filtre les URL non sûres provenant du contenu généré par un modèle.
 * Seuls les protocoles publics, les ancres et les chemins relatifs sont acceptés.
 */
export function isSafeUrl(href?: string): boolean {
  if (!href) return false;
  if (href.startsWith("#") || href.startsWith("/") || href.startsWith("?")) return true;
  try {
    const parsed = new URL(href, "http://localhost");
    return SAFE_PROTOCOLS.includes(parsed.protocol);
  } catch {
    return false;
  }
}

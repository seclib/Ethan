import { redirect } from "next/navigation";

/**
 * /mcp — lien profond conservé, page dédupliquée (30/09/2026).
 *
 * Les serveurs MCP sont un onglet de la surface unique des outils : les deux
 * écrans interrogeaient la MÊME ressource Core (`/v1/tools/servers`), donc
 * deux menus pour un seul jeu de données. On garde l'URL (aucun lien externe
 * ni signet ne casse) et on redirige vers l'onglet qui expose la source.
 */
export default function McpPage() {
  redirect("/tools?view=mcp");
}
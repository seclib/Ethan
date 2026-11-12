import { redirect } from "next/navigation";

/**
 * /mcp — lien profond conservé, redirection vers /workspaces/mcp.
 *
 * Les serveurs MCP sont désormais une section indépendante de Workspaces.
 * L'ancienne URL redirige vers la nouvelle route sans boucle.
 */
export default function McpPage() {
  redirect("/workspaces/mcp");
}
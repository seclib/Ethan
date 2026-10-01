import { redirect } from "next/navigation";

/**
 * /library — lien profond conservé, page dédupliquée (30/09/2026).
 *
 * La Library est devenue un onglet de /knowledge : les deux workspaces
 * interrogeaient les MÊMES endpoints Core (/v1/knowledge,
 * /v1/knowledge/collections, /v1/rag/documents, /v1/projects/{id}/documents,
 * /files), donc deux surfaces pour un seul jeu de données. L'URL reste
 * valide — elle ouvre directement l'onglet Library.
 */
export default function LibraryPage() {
  redirect("/knowledge?view=library");
}

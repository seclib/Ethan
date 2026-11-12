import { LibraryWorkspace } from "@/components/features/library/library-workspace";

/**
 * /library — bibliothèque unifiée d'ETHAN (capacité de premier niveau).
 *
 * La page ne porte aucune logique : elle monte `LibraryWorkspace`, qui agrège
 * en lecture les ressources exposées par ETHAN Core et gère ses propres états
 * (chargement, erreur, vide). Aucun stockage parallèle, aucune réimplémentation.
 */
export default function LibraryPage() {
  return <LibraryWorkspace />;
}

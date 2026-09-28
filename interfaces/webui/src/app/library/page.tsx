"use client";

/**
 * Page Library — vue unifiée des ressources exposées par ETHAN Core :
 * documents RAG (/v1/rag/documents), Knowledge et collections
 * (/v1/knowledge[/collections]), fichiers et images (/files).
 *
 * Interface = présentation seule (règle AGENTS.md) : LibraryWorkspace agrège
 * les APIs Core existantes, sans stockage ni registre parallèle.
 * Accessible par la taxinomie Knowledge, la séquence « G L » et Ctrl+K.
 */

import { LibraryWorkspace } from "@/components/features/library/library-workspace";

export default function LibraryPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <LibraryWorkspace />
    </div>
  );
}

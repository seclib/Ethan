"use client";

/**
 * Page Prompts — prompts prédéfinis persistés par ETHAN Core
 * (PromptManager, core/config/prompts.py ; /v1/prompts).
 *
 * Interface = présentation seule : les prompts restent la propriété du Core et
 * sont réutilisables par le chat, la CLI, le Cookbook et les autres interfaces.
 */

import { PromptsWorkspace } from "@/components/features/prompts/prompts-workspace";

export default function PromptsPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <PromptsWorkspace />
    </div>
  );
}

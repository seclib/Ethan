"use client";

/**
 * Page Skill Lab (/skills/lab) — test du code candidat dans la sandbox Docker
 * du Core (POST /v1/skills/lab/test) et historique réel des exécutions
 * (GET /v1/skills/lab/results).
 *
 * Aucune exécution côté interface : sans Docker, le Core répond 503 et
 * l'interface l'affiche tel quel.
 */

import { SkillsLabWorkspace } from "@/components/features/skills/components/skills-lab-workspace";

export default function SkillsLabPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <SkillsLabWorkspace />
    </div>
  );
}

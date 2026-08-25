"use client";

/**
 * SkillDialog — Dialog d'édition/création d'un skill.
 * ExecuteSkillDialog — Dialog d'exécution d'un skill (SkillManager Core).
 */

import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2, Play } from "lucide-react";
import type { Skill } from "@/lib/api/skills";

interface SkillDialogProps {
  open: boolean;
  editingSkill: Skill | null;
  isCreating: boolean;
  formName: string;
  formDescription: string;
  formContent: string;
  formTags: string;
  setFormName: (v: string) => void;
  setFormDescription: (v: string) => void;
  setFormContent: (v: string) => void;
  setFormTags: (v: string) => void;
  onClose: () => void;
  onSave: () => void;
}

export function SkillDialog({
  open,
  editingSkill,
  isCreating,
  formName,
  formDescription,
  formContent,
  formTags,
  setFormName,
  setFormDescription,
  setFormContent,
  setFormTags,
  onClose,
  onSave,
}: SkillDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={editingSkill ? "Modifier le skill" : "Nouveau skill"} size="lg">
      <div className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Nom</label>
          <Input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="ex: résumé-de-doc" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <Input value={formDescription} onChange={(e) => setFormDescription(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Tags (séparés par des virgules)</label>
          <Input value={formTags} onChange={(e) => setFormTags(e.target.value)} placeholder="doc, résumé" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Contenu / instructions</label>
          <Textarea value={formContent} onChange={(e) => setFormContent(e.target.value)} rows={10} className="w-full font-mono text-xs" />
        </div>
        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          <Button onClick={onSave} disabled={!formName.trim() || isCreating}>
            {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {editingSkill ? "Enregistrer" : "Créer"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

interface ExecuteSkillDialogProps {
  open: boolean;
  skill: Skill | null;
  isExecuting: boolean;
  error: string | null;
  result: string;
  onClose: () => void;
  onExecute: () => void;
}

export function ExecuteSkillDialog({ open, skill, isExecuting, error, result, onClose, onExecute }: ExecuteSkillDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={`Exécuter — ${skill?.name ?? ""}`} size="md">
      <div className="flex flex-col gap-4">
        {error && (
          <div className="rounded-lg border border-red-soft bg-red-soft px-3 py-2 text-sm text-red">{error}</div>
        )}
        {isExecuting && (
          <div className="flex items-center gap-2 text-sm text-foreground-tertiary">
            <Loader2 className="h-4 w-4 animate-spin" /> Exécution en cours…
          </div>
        )}
        {result && (
          <pre className="whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-sm text-foreground-secondary">{result}</pre>
        )}
        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
          <Button onClick={onExecute} disabled={isExecuting}>
            <Play className="h-4 w-4" /> Lancer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
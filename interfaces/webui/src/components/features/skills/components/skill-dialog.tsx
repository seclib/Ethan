"use client";

/**
 * SkillDialog — Dialog d'édition/création d'un skill (modèle unifié Core).
 * ExecuteSkillDialog — Dialog d'exécution d'un skill (SkillManager Core).
 * SkillLabDialog — Test sandbox Docker du contenu candidat (Skill Lab Core).
 */

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Play, FlaskConical } from "lucide-react";
import { testSkillCode, type SkillLabResult } from "@/lib/api/skills";
import type { Skill } from "@/lib/api/skills";

interface SkillDialogProps {
  open: boolean;
  editingSkill: Skill | null;
  isCreating: boolean;
  formName: string;
  formDescription: string;
  formContent: string;
  formTags: string;
  formKind: "prompt" | "pipeline";
  formRequiredTools: string;
  formValves: string;
  setFormName: (v: string) => void;
  setFormDescription: (v: string) => void;
  setFormContent: (v: string) => void;
  setFormTags: (v: string) => void;
  setFormKind: (v: "prompt" | "pipeline") => void;
  setFormRequiredTools: (v: string) => void;
  setFormValves: (v: string) => void;
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
  formKind,
  formRequiredTools,
  formValves,
  setFormName,
  setFormDescription,
  setFormContent,
  setFormTags,
  setFormKind,
  setFormRequiredTools,
  setFormValves,
  onClose,
  onSave,
}: SkillDialogProps) {
  const [labOpen, setLabOpen] = React.useState(false);
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
          <label className="mb-1 block text-sm font-medium">Type</label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setFormKind("prompt")}
              className={`flex-1 rounded-lg border px-3 py-2 text-left text-sm ${formKind === "prompt" ? "border-accent/60 bg-accent/10" : "border-line-2 bg-bg-1"}`}
            >
              <div className="font-medium text-foreground">{formKind === "prompt" ? "●" : "○"} Prompt</div>
              <div className="mt-0.5 text-xs text-foreground-tertiary">Instructions injectées au modèle (ChatPipeline).</div>
            </button>
            <button
              type="button"
              onClick={() => setFormKind("pipeline")}
              className={`flex-1 rounded-lg border px-3 py-2 text-left text-sm ${formKind === "pipeline" ? "border-accent/60 bg-accent/10" : "border-line-2 bg-bg-1"}`}
            >
              <div className="font-medium text-foreground">{formKind === "pipeline" ? "●" : "○"} Pipeline</div>
              <div className="mt-0.5 text-xs text-foreground-tertiary">Étapes orchestrant des outils (SkillExecutor).</div>
            </button>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Tags (séparés par des virgules)</label>
          <Input value={formTags} onChange={(e) => setFormTags(e.target.value)} placeholder="doc, résumé" />
        </div>
        {formKind === "prompt" && (
          <div>
            <label className="mb-1 block text-sm font-medium">Contenu / instructions</label>
            <Textarea value={formContent} onChange={(e) => setFormContent(e.target.value)} rows={10} className="w-full font-mono text-xs" />
          </div>
        )}
        {formKind === "pipeline" && (
          <div className="flex flex-col gap-3 rounded-lg border border-line-1 bg-bg-1/60 p-3">
            <p className="text-xs text-foreground-tertiary">
              Un skill <Badge variant="accent" size="sm">Pipeline</Badge> déclare les outils qu&apos;il orchestre
              (stockés côté Core comme <code>steps</code>). Les autres propriétés s&apos;éditent côté
              Agent / code. Chaque outil déclaré est validé par le Core à l&apos;enregistrement.
            </p>
            <div>
              <label className="mb-1 block text-xs font-medium text-foreground-secondary">
                Outils requis (séparés par des virgules)
              </label>
              <Input
                value={formRequiredTools}
                onChange={(e) => setFormRequiredTools(e.target.value)}
                placeholder="web_search, writer"
                onKeyDown={(ev) => {
                  if (ev.key === "Enter") ev.preventDefault();
                }}
              />
            </div>
          </div>
        )}
        <div>
          <label className="mb-1 block text-xs font-medium text-foreground-secondary">Valves (JSON, optionnel)</label>
          <Input
            value={formValves}
            onChange={(e) => setFormValves(e.target.value)}
            placeholder='{"temperature": 0.2}'
            onKeyDown={(ev) => {
              if (ev.key === "Enter") ev.preventDefault();
            }}
          />
        </div>
        <div className="rounded-lg border border-line-1 bg-bg-1/40 px-3 py-2">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="flex items-center gap-1.5 text-xs font-medium text-foreground-secondary">
                <FlaskConical className="h-3.5 w-3.5" /> Sandbox Skill Lab
              </p>
              <p className="mt-0.5 text-xs text-foreground-tertiary">
                Exécute le contenu comme du code Python dans la sandbox Docker du Core
                (aucune exécution locale).
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setLabOpen(true)}
              disabled={!formContent.trim()}
            >
              Tester
            </Button>
          </div>
        </div>
        <SkillLabDialog open={labOpen} code={formContent} onClose={() => setLabOpen(false)} />
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
  input: string;
  setInput: (v: string) => void;
  error: string | null;
  result: string;
  onClose: () => void;
  onExecute: () => void;
}

export function ExecuteSkillDialog({
  open,
  skill,
  isExecuting,
  input,
  setInput,
  error,
  result,
  onClose,
  onExecute,
}: ExecuteSkillDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={`Exécuter — ${skill?.name ?? ""}`} size="md">
      <div className="flex flex-col gap-4">
        {error && (
          <div className="rounded-lg border border-red-soft bg-red-soft px-3 py-2 text-sm text-red">{error}</div>
        )}
        <div>
          <label className="mb-1 block text-sm font-medium">
            Message d&apos;entrée
          </label>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={3}
            placeholder="Que doit faire la skill ? (ex: résume ce passage, génère une idée…)"
            className="w-full text-sm"
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Le contenu de la skill est injecté comme instructions par ETHAN Core, puis la
            réponse est générée par le modèle actif.
          </p>
        </div>
        {isExecuting && (
          <div className="flex items-center gap-2 text-sm text-foreground-tertiary">
            <Loader2 className="h-4 w-4 animate-spin" /> Exécution en cours…
          </div>
        )}
        {result && (
          <div>
            <p className="mb-1 text-sm font-medium text-foreground-secondary">Résultat</p>
            <pre className="whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-sm text-foreground-secondary">{result}</pre>
          </div>
        )}
        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
          <Button onClick={onExecute} disabled={isExecuting || !input.trim()}>
            <Play className="h-4 w-4" /> Lancer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

interface SkillLabDialogProps {
  open: boolean;
  code: string;
  onClose: () => void;
}

/**
 * Test du contenu candidat dans la sandbox Docker du Core (Skill Lab).
 * Appel SYNCHRONE — la réponse est le résultat complet (aucun polling).
 * Sans Docker, le Core renvoie 503 : le message est affiché tel quel.
 */
export function SkillLabDialog({ open, code, onClose }: SkillLabDialogProps) {
  const [testing, setTesting] = React.useState(false);
  const [result, setResult] = React.useState<SkillLabResult | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) {
      setResult(null);
      setErrorMessage(null);
      setTesting(false);
    }
  }, [open]);

  const handleTest = async () => {
    setTesting(true);
    setErrorMessage(null);
    setResult(null);
    try {
      const res = await testSkillCode(code, { name: "skill_dialog_candidate" });
      setResult(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(
        msg.includes("503") || msg.toLowerCase().includes("docker")
          ? "Skill Lab indisponible : Docker est requis sur le serveur (sandbox obligatoire)."
          : msg
      );
    } finally {
      setTesting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="Sandbox Skill Lab (Docker)" size="md">
      <div className="flex flex-col gap-4">
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-xs text-foreground-secondary">
          {code || "—"}
        </pre>

        {errorMessage && (
          <div className="rounded-lg border border-red-soft bg-red-soft px-3 py-2 text-sm text-red">
            {errorMessage}
          </div>
        )}

        {result && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Badge variant={result.passed ? "success" : "error"}>
                {result.passed ? "Réussi" : "Échec"}
              </Badge>
              <span className="text-xs text-foreground-tertiary">
                statut : {result.status} · {Math.round(result.duration_ms)} ms
              </span>
            </div>
            {result.output && (
              <div>
                <p className="mb-1 text-xs font-medium text-foreground-secondary">Sortie</p>
                <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-line-1 bg-bg-1 p-3 text-xs text-foreground-secondary">
                  {result.output}
                </pre>
              </div>
            )}
            {result.error && (
              <div>
                <p className="mb-1 text-xs font-medium text-red">Erreur</p>
                <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-red-soft bg-red-soft p-3 text-xs text-red">
                  {result.error}
                </pre>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
          <Button onClick={handleTest} disabled={testing || !code.trim()}>
            {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
            {testing ? "Test en cours…" : "Lancer le test"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
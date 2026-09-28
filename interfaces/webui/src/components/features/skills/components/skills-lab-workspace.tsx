"use client";

/**
 * SkillsLabWorkspace — page /skills/lab.
 *
 * Test du code candidat dans la SANDBOX Docker du Core
 * (POST /v1/skills/lab/test, SkillLab core/skills/lab.py) et historique des
 * exécutions (GET /v1/skills/lab/results). Le Core refuse de tester sans
 * Docker (503) : l'interface relaie le message tel quel — le code candidat
 * n'est jamais exécuté dans le process ETHAN ni dans le navigateur.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  testSkillCode,
  listSkillLabResults,
  type SkillLabResult,
} from "@/lib/api/skills";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Clock, FlaskConical, Loader2, Play, RefreshCw } from "lucide-react";

const DEFAULT_CODE = `def run(input: str) -> str:
    return f"echo: {input}"
`;

export function SkillsLabWorkspace() {
  const [name, setName] = React.useState("test_skill");
  const [code, setCode] = React.useState(DEFAULT_CODE);
  const [testInput, setTestInput] = React.useState("");
  const [requirements, setRequirements] = React.useState("");
  const [running, setRunning] = React.useState(false);
  const [result, setResult] = React.useState<SkillLabResult | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // Historique réel : résultats conservés par le SkillLab du Core.
  const history = useQuery({
    queryKey: ["skill-lab-results"],
    queryFn: () => listSkillLabResults(),
    retry: false,
  });
  const results = history.data ?? [];

  const handleRun = async () => {
    setRunning(true);
    setErrorMessage(null);
    setResult(null);
    try {
      const res = await testSkillCode(code, {
        name: name.trim() || "test_skill",
        input: testInput,
        requirements: requirements
          .split(",")
          .map((r) => r.trim())
          .filter(Boolean),
      });
      setResult(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(
        msg.includes("503") || msg.toLowerCase().includes("docker")
          ? "Skill Lab indisponible : Docker est requis sur le serveur (sandbox obligatoire)."
          : msg,
      );
    } finally {
      setRunning(false);
      // Le Core enregistre chaque test : l'historique est rafraîchi après coup.
      await history.refetch();
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        className="flex items-center gap-2 border-b border-line-1 px-4 py-3"
        style={{ background: "var(--panel)" }}
      >
        <FlaskConical className="h-4 w-4 text-muted-foreground" />
        <div>
          <h1 className="text-sm font-semibold text-foreground">Skill Lab</h1>
          <p className="text-xs text-muted-foreground">
            Exécution sandboxée par ETHAN Core (Docker) — le code candidat n&apos;est jamais
            exécuté dans le process ETHAN.
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border border-line-1 p-4">
            <h2 className="text-sm font-medium text-foreground">Candidat</h2>
            <div className="mt-3 flex flex-col gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Nom du skill</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Code Python</label>
                <Textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  rows={10}
                  className="font-mono text-xs"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Entrée de test</label>
                <Input value={testInput} onChange={(e) => setTestInput(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">
                  Dépendances pip (séparées par des virgules)
                </label>
                <Input
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  placeholder="ex: requests, pandas"
                />
              </div>
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-muted-foreground">
                  Sans Docker, le Core répond 503 — aucun repli local.
                </p>
                <Button onClick={handleRun} disabled={running || !code.trim()}>
                  {running ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  {running ? "Test en cours…" : "Lancer le test"}
                </Button>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-line-1 p-4">
            <h2 className="text-sm font-medium text-foreground">Résultat du dernier test</h2>

            {errorMessage && (
              <div className="mt-3 rounded-lg border border-red-soft bg-red-soft p-3 text-sm text-red">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  {errorMessage}
                </div>
              </div>
            )}

            {!errorMessage && !result && (
              <p className="mt-3 text-sm text-muted-foreground">
                Aucun test lancé dans cette session — l&apos;historique ci-dessous conserve les
                exécutions enregistrées par le Core.
              </p>
            )}

            {result && (
              <div className="mt-3 flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <Badge variant={result.passed ? "success" : "error"}>
                    {result.passed ? "Réussi" : "Échec"}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    statut : {result.status} · {Math.round(result.duration_ms)} ms
                  </span>
                </div>
                {result.output && (
                  <div>
                    <p className="mb-1 text-xs font-medium text-foreground-secondary">Sortie</p>
                    <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-line-1 bg-[var(--background)] p-3 text-xs text-foreground-secondary">
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
          </div>
        </div>

        <div className="mt-4 rounded-lg border border-line-1">
          <div className="flex items-center justify-between border-b border-line-1 px-4 py-2">
            <h2 className="text-sm font-medium text-foreground">Historique des tests</h2>
            <Button size="sm" variant="ghost" onClick={() => history.refetch()}>
              <RefreshCw className="h-4 w-4" /> Rafraîchir
            </Button>
          </div>
          <div className="p-4">
            {history.isLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Chargement de l&apos;historique…
              </div>
            )}

            {history.error && (
              <div className="rounded-lg border border-red-soft bg-red-soft p-3 text-sm text-red">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Impossible de charger l&apos;historique
                </div>
                <p className="mt-1 text-xs">
                  {history.error instanceof Error ? history.error.message : "Core indisponible"}
                </p>
                <Button size="sm" variant="outline" className="mt-2" onClick={() => history.refetch()}>
                  Réessayer
                </Button>
              </div>
            )}

            {!history.isLoading && !history.error && results.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Aucun test enregistré — lancez un premier test dans la sandbox.
              </p>
            )}

            <div className="space-y-2">
              {results.map((item, index) => (
                <div
                  key={item.id ?? `${item.skill_name}-${index}`}
                  className="flex items-center justify-between gap-3 rounded-md border border-line-1 px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm text-foreground">{item.skill_name}</p>
                    {item.timestamp && (
                      <p className="text-xs text-muted-foreground">
                        {new Date(item.timestamp).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {Math.round(item.duration_ms)} ms
                    <Badge variant={item.passed ? "success" : "error"}>
                      {item.passed ? "Réussi" : "Échec"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

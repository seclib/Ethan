"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, Database, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/shared/page-header";
import {
  createCtiObject,
  getCtiManifest,
  getCtiStatus,
  listCtiObjects,
  type CtiRecord,
} from "@/lib/api/cti";

const DEFAULT_OBJECT = JSON.stringify(
  {
    type: "indicator",
    spec_version: "2.1",
    name: "Example CTI indicator",
    pattern: "[ipv4-addr:value = '192.0.2.1']",
    pattern_type: "stix",
    valid_from: new Date().toISOString(),
  },
  null,
  2,
);

export function CtiWorkspace() {
  const queryClient = useQueryClient();
  const ctiQuery = useQuery({
    queryKey: ["cti"],
    queryFn: async () => {
      const [manifest, status, result] = await Promise.all([
        getCtiManifest(),
        getCtiStatus(),
        listCtiObjects(),
      ]);
      return { manifest, status, records: result.items };
    },
  });
  const [jsonInput, setJsonInput] = React.useState(DEFAULT_OBJECT);
  const [inputError, setInputError] = React.useState<string | null>(null);
  const createMutation = useMutation({
    mutationFn: createCtiObject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cti"] }),
  });
  const manifest = ctiQuery.data?.manifest ?? null;
  const status = ctiQuery.data?.status ?? null;
  const records: CtiRecord[] = ctiQuery.data?.records ?? [];
  const error = inputError ?? (ctiQuery.error instanceof Error
    ? ctiQuery.error.message
    : createMutation.error instanceof Error
      ? createMutation.error.message
      : null);
  const loading = ctiQuery.isPending;

  const submitObject = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    let parsed: Record<string, unknown>;
    try {
      const value: unknown = JSON.parse(jsonInput);
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        throw new Error("Le document STIX doit être un objet JSON.");
      }
      parsed = value as Record<string, unknown>;
    } catch (cause) {
      // JSON input errors are shown in the shared error area.
      createMutation.reset();
      setInputError(cause instanceof Error ? cause.message : "JSON invalide.");
      return;
    }
    setInputError(null);
    createMutation.mutate(parsed);
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-y-auto">
      <PageHeader
        title={manifest?.name ?? "ETHAN-CTI"}
        description={manifest?.description ?? "Application CTI Core, modèle STIX 2.1"}
        icon={<ShieldCheck className="h-5 w-5" />}
        actions={
          <>
            <Link href="/tools" className="inline-flex h-8 items-center justify-center gap-2 rounded-md border border-line-2 bg-background px-3 text-xs font-medium text-foreground hover:bg-surface">
              <ArrowLeft className="h-4 w-4" /> Tools
            </Link>
            <Button variant="secondary" size="sm" onClick={() => void ctiQuery.refetch()} disabled={ctiQuery.isFetching}>
              <RefreshCw className="h-4 w-4" /> Actualiser
            </Button>
          </>
        }
      />

      <main className="mx-auto grid w-full max-w-6xl gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        {error && (
          <div role="alert" className="flex items-center gap-2 rounded-lg border border-red-soft bg-red-soft/30 p-3 text-sm text-red lg:col-span-2">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Database className="h-4 w-4" /> État du domaine</CardTitle>
            <CardDescription>ETHAN Core fournit l’API, l’authentification et la persistance.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Service : <strong>{status?.status ?? (loading ? "vérification…" : "indisponible")}</strong></p>
            <p>Modèle : <strong>{status?.model ?? manifest?.model ?? "STIX 2.1"}</strong></p>
            <p>Objets visibles : <strong>{status?.object_count ?? records.length}</strong></p>
            <p className="text-foreground-tertiary">Accès isolé par utilisateur ETHAN. Le socle ne crée ni moteur graph ni stockage CTI distinct.</p>
          </CardContent>
        </Card>

        <Card className="gap-3">
          <CardHeader>
            <CardTitle>Ajouter un objet STIX 2.1</CardTitle>
            <CardDescription>Le Core valide l’enveloppe STIX, l’identité et les permissions.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={submitObject}>
              <label htmlFor="cti-stix-json" className="sr-only">Objet STIX au format JSON</label>
              <textarea
                id="cti-stix-json"
                aria-label="Objet STIX au format JSON"
                value={jsonInput}
                onChange={(event) => setJsonInput(event.target.value)}
                spellCheck={false}
                className="min-h-56 w-full rounded-lg border border-line-2 bg-background p-3 font-mono text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
              />
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Enregistrement…" : "Enregistrer dans ETHAN Core"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="gap-3 lg:col-span-2">
          <CardHeader>
            <CardTitle>Objets CTI</CardTitle>
            <CardDescription>Les enregistrements affichés sont ceux de l’utilisateur authentifié.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <p role="status" className="text-sm text-foreground-tertiary">Chargement…</p>}
            {!loading && records.length === 0 && <p className="text-sm text-foreground-tertiary">Aucun objet CTI. Ajoutez un objet STIX 2.1 pour commencer.</p>}
            <ul className="divide-y divide-line-1">
              {records.map((record) => (
                <li key={record.id} className="flex flex-wrap items-center gap-2 py-3 text-sm">
                  <span className="rounded bg-bg-3 px-2 py-1 font-mono text-xs">{String(record.stix_object.type ?? "STIX")}</span>
                  <span className="font-medium">{String(record.stix_object.name ?? record.id)}</span>
                  <code className="ml-auto text-xs text-foreground-tertiary">{record.id}</code>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

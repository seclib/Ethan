'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';

import {
  getApplication,
  getApplicationRuntime,
  startApplicationRuntime,
  stopApplicationRuntime,
  type ApplicationCatalogEntry,
  type ApplicationRuntimeStatus,
} from '@/lib/api/applications';

export default function ApplicationDetailPage() {
  const params = useParams();
  const appId = Array.isArray(params?.app_id) ? params.app_id[0] : params?.app_id;
  const decodedAppId = appId ? decodeURIComponent(String(appId)) : '';

  const { data, isLoading, error } = useQuery({
    queryKey: ['application', decodedAppId],
    queryFn: () => getApplication(decodedAppId),
    enabled: decodedAppId.length > 0,
  });

  const runtime = useQuery({
    queryKey: ['application-runtime', decodedAppId],
    queryFn: () => getApplicationRuntime(decodedAppId),
    enabled: decodedAppId.length > 0,
    retry: 0,
  });

  if (!decodedAppId) {
    return <main className="p-4"><p>Application manquante.</p><Link href="/applications" className="underline text-sm">Retour</Link></main>;
  }

  if (isLoading) {
    return <main className="p-4"><p>Chargement de l&#39;application…</p></main>;
  }

  if (error || !data) {
    return (
      <main className="p-4">
        <p className="text-red-500">Application introuvable ou erreur API.</p>
        <Link href="/applications" className="underline text-sm">Retour</Link>
      </main>
    );
  }

  const entry = data as ApplicationCatalogEntry;
  const identity = (entry.manifest as any)?.identity;
  const runtimeStatus = runtime.data as ApplicationRuntimeStatus | undefined;
  const canStart = runtimeStatus?.supported_operations?.includes('start') ?? false;
  const canStop = runtimeStatus?.supported_operations?.includes('stop') ?? false;

  async function perform(action: 'start' | 'stop') {
    if (!window.confirm(`Confirmer l'action ${action} pour ${decodedAppId} ?`)) return;
    try {
      if (action === 'start') await startApplicationRuntime(decodedAppId);
      else await stopApplicationRuntime(decodedAppId);
      await runtime.refetch();
    } catch (runError) {
      console.error(runError);
    }
  }

  return (
    <main className="flex h-full flex-col gap-4 p-4">
      <Link href="/applications" className="text-sm underline">← Retour au catalogue</Link>
      <h1 className="text-xl font-semibold">{identity?.name ?? entry.app_id}</h1>
      <p className="text-sm text-muted-foreground">
        ID : {entry.app_id} · source : {entry.source} · {entry.validated ? 'validée' : 'non validée'} · runtime : {runtime.isLoading ? 'chargement' : runtimeStatus?.state ?? 'inconnu'}
      </p>
      <section className="space-y-1">
        <h2 className="text-lg font-semibold">Métadonnées</h2>
        <div className="text-sm">Instance : {entry.instance_id}</div>
        <div className="text-sm">Emplacement : {entry.location || 'n/a'}</div>
        <div className="text-sm break-all">Manifest digest : {entry.manifest_digest}</div>
      </section>
      {entry.manifest && (
        <section className="space-y-1">
          <h2 className="text-lg font-semibold">Manifest</h2>
          <pre className="whitespace-pre-wrap rounded border p-3 text-xs">
            {JSON.stringify(entry.manifest, null, 2)}
          </pre>
        </section>
      )}
      <section className="space-y-1">
        <h2 className="text-lg font-semibold">Runtime</h2>
        <div className="text-sm">État : {runtimeStatus?.state ?? 'inconnu'}{runtimeStatus?.state === 'unknown' ? '' : ''}</div>
        <div className="text-sm">Santé : {runtimeStatus?.healthy === null ? 'non vérifiée' : String(runtimeStatus?.healthy)}</div>
        <div className="text-sm">Conteneur : {runtimeStatus?.container_id ?? 'n/a'}</div>
        <div className="flex gap-2 pt-2">
          {canStart && <button className="rounded border px-3 py-1 text-sm" onClick={() => perform('start')}>Start</button>}
          {canStop && <button className="rounded border px-3 py-1 text-sm" onClick={() => perform('stop')}>Stop</button>}
        </div>
      </section>
    </main>
  );
}

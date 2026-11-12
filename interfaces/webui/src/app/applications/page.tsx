'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { listLocalRepositories } from '@/lib/api/local-repositories';
import { discoverGitHubOrganization, type GitHubRepositoryRecord } from '@/lib/api/github-discovery';
import { listApplications, type ApplicationCatalogEntry } from '@/lib/api/applications';

function GitHubRepositoryList() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['github-org', 'seclib'],
    queryFn: () => discoverGitHubOrganization('seclib'),
    retry: 0,
  });

  if (isLoading) return <p>Interrogation GitHub…</p>;
  if (error) return <p className="text-amber-500">Découverte GitHub indisponible (organisation absente, réseau ou limite de débit).</p>;
  if (data.length === 0) return <p>Aucun dépôt GitHub découvrable.</p>;

  return (
    <ul className="space-y-2">
      {data.map((repo: GitHubRepositoryRecord) => (
        <li key={repo.full_name} className="rounded border p-3 text-sm">
          <div className="font-medium">{repo.full_name}</div>
          <div className="text-muted-foreground">{repo.description ?? 'Sans description'}</div>
        </li>
      ))}
    </ul>
  );
}

function LocalRepositoryList() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['local-repositories'],
    queryFn: listLocalRepositories,
  });

  if (isLoading) return <p>Discovering local repositories…</p>;
  if (error) return <p className="text-amber-500">Local repository discovery unavailable.</p>;
  if (data.length === 0) return <p>No local Git repositories discovered.</p>;

  return (
    <ul className="space-y-2">
      {data.map((repo) => (
        <li key={repo.path} className="rounded border p-3 text-sm">
          <div className="font-medium">{repo.name}</div>
          <div className="text-muted-foreground">{repo.path} · {repo.classification}</div>
          <div className="text-xs">
            {repo.branch ?? 'unknown branch'} · {repo.working_tree_status}
            {repo.remote ? ` · ${repo.remote}` : ''}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function ApplicationsPage() {
  const { data = [], error, isLoading, refetch } = useQuery({
    queryKey: ['applications'],
    queryFn: listApplications,
  });

  return (
    <main className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Applications</h1>
        <button className="rounded border px-3 py-1 text-sm" onClick={() => refetch()}>
          Actualiser
        </button>
      </div>
      {isLoading && <p>Chargement…</p>}
      {error && <p className="text-red-500">Erreur de chargement du catalogue applicatif.</p>}
      {!isLoading && data.length === 0 && <p>Aucune application découverte.</p>}
      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Local repository discovery</h2>
        <LocalRepositoryList />
      </section>

      <ul className="space-y-2">
        {data.map((entry: ApplicationCatalogEntry) => (
          <li key={`${entry.app_id}-${entry.instance_id}`} className="rounded border p-3">
            <Link href={`/applications/${encodeURIComponent(entry.app_id)}`} className="font-medium underline">
              {entry.app_id}
            </Link>
            <div className="text-sm text-muted-foreground">
              {entry.source} · {entry.validated ? 'validé' : 'non validé'}
            </div>
            {entry.manifest && (
              <div className="text-xs">
                {(entry.manifest as any)?.identity?.name ?? entry.manifest_digest}
              </div>
            )}
          </li>
        ))}
      </ul>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">GitHub organization discovery</h2>
        <GitHubRepositoryList />
      </section>
    </main>
  );
}

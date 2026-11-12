/**
 * ETHAN WebUI — Frame service API (application independante via backend).
 *
 * Meme contrat de cycle de vie qu'Odin : aucune commande Docker n'est construite
 * cote frontend; toutes les operations passent par /v1/plugins/frame.
 */

import { apiFetch } from '@/lib/api/client';

export type FrameStatus = {
  id: string;
  name: string;
  status: 'not_installed' | 'installed_stopped' | 'starting' | 'running' | 'degraded' | 'stopping' | 'error' | 'unknown';
  port: number;
  host: string;
  url: string;
  container_id?: string | null;
  healthy: boolean;
  error?: string | null;
  updated_at?: string;
  allowed_actions: string[];
};

export type FrameLogs = {
  ok: boolean;
  logs: string;
  error?: string | null;
};

export type FrameHealth = {
  status?: string;
  healthy?: boolean;
  reachable?: boolean;
  tcp_probe?: boolean;
  container_state?: string;
  port?: number;
  host?: string;
  url?: string;
  checked_at?: string;
};

export function getFrameStatus(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/status');
}

export function startFrame(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/start', { method: 'POST' });
}

export function stopFrame(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/stop', { method: 'POST' });
}

export function restartFrame(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/restart', { method: 'POST' });
}

export function installFrame(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/install', { method: 'POST' });
}

export function uninstallFrame(): Promise<FrameStatus> {
  return apiFetch<FrameStatus>('/v1/plugins/frame/uninstall', { method: 'POST' });
}

export function getFrameLogs(tail = 100): Promise<FrameLogs> {
  return apiFetch<FrameLogs>(`/v1/plugins/frame/logs?tail=${encodeURIComponent(String(tail))}`);
}

export function getFrameHealth(): Promise<FrameHealth> {
  return apiFetch<FrameHealth>('/v1/plugins/frame/health');
}

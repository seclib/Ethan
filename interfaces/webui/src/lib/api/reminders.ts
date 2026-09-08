/**
 * ETHAN WebUI — Reminders API service
 *
 * Maps to ETHAN API endpoints:
 *   GET    /v1/reminders                     → listReminders
 *   GET    /v1/reminders/{id}                → getReminder
 *   POST   /v1/reminders                     → createReminder
 *   PUT    /v1/reminders/{id}                → updateReminder
 *   DELETE /v1/reminders/{id}                → deleteReminder
 *   POST   /v1/reminders/{id}/enable         → enableReminder
 *   POST   /v1/reminders/{id}/disable        → disableReminder
 *   POST   /v1/reminders/{id}/fire           → fireReminder
 */

import { apiFetch } from '@/lib/api/client';

export interface Reminder {
  id: string;
  title: string;
  message: string;
  schedule: string | null;
  fire_at: string | null;
  timezone: string;
  enabled: boolean;
  last_fired_at: string | null;
  fire_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreate {
  title: string;
  schedule?: string;
  fire_at?: string;
  timezone?: string;
  message?: string;
  enabled?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ReminderUpdate {
  title?: string;
  message?: string;
  schedule?: string;
  fire_at?: string;
  timezone?: string;
  enabled?: boolean;
  metadata?: Record<string, unknown>;
}

export async function listReminders(enabled?: boolean): Promise<Reminder[]> {
  const qs = enabled !== undefined ? `?enabled=${enabled}` : '';
  return apiFetch<Reminder[]>(`/v1/reminders${qs}`);
}

export async function getReminder(id: string): Promise<Reminder> {
  return apiFetch<Reminder>(`/v1/reminders/${id}`);
}

export async function createReminder(data: ReminderCreate): Promise<Reminder> {
  return apiFetch<Reminder>('/v1/reminders', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateReminder(id: string, data: ReminderUpdate): Promise<Reminder> {
  return apiFetch<Reminder>(`/v1/reminders/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteReminder(id: string): Promise<{ status: string; reminder_id: string }> {
  return apiFetch<{ status: string; reminder_id: string }>(`/v1/reminders/${id}`, {
    method: 'DELETE',
  });
}

export async function enableReminder(id: string): Promise<Reminder> {
  return apiFetch<Reminder>(`/v1/reminders/${id}/enable`, { method: 'POST' });
}

export async function disableReminder(id: string): Promise<Reminder> {
  return apiFetch<Reminder>(`/v1/reminders/${id}/disable`, { method: 'POST' });
}

export async function fireReminder(id: string): Promise<Reminder> {
  return apiFetch<Reminder>(`/v1/reminders/${id}/fire`, { method: 'POST' });
}

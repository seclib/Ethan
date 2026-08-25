"use client";

/**
 * ETHAN WebUI — Calendar & Notes clients.
 * Business logic lives in ETHAN Core (CalendarManager, NoteManager);
 * these clients only serialise requests over /v1 capabilities.
 */

import { apiFetch } from "@/lib/api/client";

// ── Calendar ────────────────────────────────────────────────────────────

export interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time?: string | null;
  description?: string;
  all_day?: boolean;
  created_at?: string;
}

export async function listCalendarEvents(): Promise<CalendarEvent[]> {
  return apiFetch<CalendarEvent[]>("/v1/calendar");
}

export async function createCalendarEvent(data: {
  title: string;
  start_time: string;
  end_time?: string;
  description?: string;
  all_day?: boolean;
}): Promise<CalendarEvent> {
  return apiFetch<CalendarEvent>("/v1/calendar", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteCalendarEvent(id: string): Promise<{ status: string }> {
  return apiFetch(`/v1/calendar/${id}`, { method: "DELETE" });
}

// ── Notes ───────────────────────────────────────────────────────────────

export interface Note {
  id: string;
  title: string;
  content: string;
  pinned?: boolean;
  tags?: string[];
  user_id?: string;
  updated_at?: string;
}

export async function listNotes(): Promise<Note[]> {
  return apiFetch<Note[]>("/v1/notes");
}

export async function searchNotes(q: string): Promise<Note[]> {
  return apiFetch<Note[]>(`/v1/notes/search?q=${encodeURIComponent(q)}`);
}

export async function createNote(data: {
  title: string;
  content: string;
  pinned?: boolean;
}): Promise<Note> {
  return apiFetch<Note>("/v1/notes", {
    method: "POST",
    body: JSON.stringify({ ...data, user_id: "anonymous" }),
  });
}

export async function updateNote(
  id: string,
  data: { title?: string; content?: string; pinned?: boolean },
): Promise<Note> {
  return apiFetch<Note>(`/v1/notes/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteNote(id: string): Promise<{ status: string }> {
  return apiFetch(`/v1/notes/${id}`, { method: "DELETE" });
}

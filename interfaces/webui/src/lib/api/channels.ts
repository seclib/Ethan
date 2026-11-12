"use client";

/**
 * ETHAN WebUI — Channels client (canaux de discussion Core).
 *
 * La persistance vit dans ETHAN Core (ChannelStore, core/state/channels.py) ;
 * ce client ne fait que sérialiser les requêtes sur /v1/channels
 * (routers/capabilities.py) :
 *   GET    /v1/channels
 *   POST   /v1/channels
 *   PUT    /v1/channels/{id}
 *   DELETE /v1/channels/{id}
 *   GET    /v1/channels/{id}/messages
 *   POST   /v1/channels/{id}/messages
 *
 * Chaque écriture publie un événement sur le bus (`channel.created`,
 * `channel.message`…) : l'interface ne fait que révéler ces capacités.
 */

import { apiFetch } from "@/lib/api/client";

export interface Channel {
  id: string;
  name: string;
  description: string;
  user_id: string;
  members: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ChannelMessage {
  id: string;
  channel_id: string;
  role: string;
  content: string;
  user_id: string;
  created_at: string;
}

/** Rôles reconnus par le Core (`role` libre côté ChannelStore). */
export type ChannelMessageRole = "user" | "assistant" | "system" | "agent";

export async function listChannels(): Promise<Channel[]> {
  return apiFetch<Channel[]>("/v1/channels");
}

export async function createChannel(data: {
  name: string;
  description?: string;
  metadata?: Record<string, unknown>;
}): Promise<Channel> {
  // `user_id`/`members` sont déduits de l'identité JWT par le Core :
  // l'interface ne les déclare jamais.
  return apiFetch<Channel>("/v1/channels", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateChannel(
  id: string,
  data: { name?: string; description?: string; metadata?: Record<string, unknown> },
): Promise<Channel> {
  return apiFetch<Channel>(`/v1/channels/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteChannel(id: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/v1/channels/${id}`, { method: "DELETE" });
}

export async function listChannelMessages(channelId: string): Promise<ChannelMessage[]> {
  return apiFetch<ChannelMessage[]>(`/v1/channels/${channelId}/messages`);
}

export async function addChannelMessage(
  channelId: string,
  data: { content: string; role?: ChannelMessageRole },
): Promise<ChannelMessage> {
  return apiFetch<ChannelMessage>(`/v1/channels/${channelId}/messages`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

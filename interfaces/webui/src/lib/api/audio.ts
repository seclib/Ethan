"use client";

/**
 * ETHAN WebUI — Audio (TTS) client.
 * Synthesis logic lives in ETHAN Core (core/llm/tts.py); this client
 * only sends text and plays the returned WAV.
 */

import { apiFetch } from "@/lib/api/client";

export interface AudioConfig {
  provider: string;
  voice?: string;
  speed?: number;
  enabled?: boolean;
}

export async function getAudioConfig(): Promise<AudioConfig | null> {
  return apiFetch<AudioConfig | null>("/v1/audio/config");
}

export async function configureAudio(config: {
  provider: string;
  voice?: string;
  speed?: number;
}): Promise<AudioConfig> {
  return apiFetch<AudioConfig>("/v1/audio/config", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

/**
 * Synthesize text and play the returned WAV in the browser.
 * Auto-configures the offline "builtin-tone" engine on first use so the
 * pipeline is exercisable without external TTS services.
 */
export async function speakText(text: string): Promise<void> {
  let config = await getAudioConfig();
  if (!config || !config.provider) {
    config = await configureAudio({ provider: "builtin-tone", voice: "default", speed: 1 });
  }

  const res = await apiFetch<{ format: string; content_base64: string }>(
    "/v1/audio/synthesize",
    { method: "POST", body: JSON.stringify({ text }) },
  );

  const bytes = Uint8Array.from(atob(res.content_base64), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: `audio/${res.format}` });
  const url = URL.createObjectURL(blob);
  const player = new Audio(url);
  player.onended = () => URL.revokeObjectURL(url);
  await player.play();
}

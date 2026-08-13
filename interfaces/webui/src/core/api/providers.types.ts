/**
 * Types for the LLM Provider Manager API.
 *
 * Mirrors the Pydantic schemas defined in
 * interfaces/api/models/provider_schemas.py.  Kept in a dedicated file so
 * the Settings page, the global selector and the chat indicator can all
 * import the same contracts without duplicating logic.
 */

export type ProviderType =
  | "ollama"
  | "openai"
  | "anthropic"
  | "vllm"
  | "llamacpp"
  | "lmstudio"
  | "gemini"
  | "openai-compatible"
  | "custom";

export type ProviderStatus = "connected" | "disconnected" | "error" | "unknown";

export interface Provider {
  id: string;
  name: string;
  type: ProviderType | string;
  enabled: boolean;
  status: ProviderStatus;
  default_model: string;
  is_default: boolean;
  base_url: string;
  models: string[];
}

export interface ProviderCreate {
  name: string;
  type: ProviderType | string;
  base_url?: string;
  api_key?: string | null;
  default_model?: string;
  display_name?: string;
  enabled?: boolean;
  options?: Record<string, unknown>;
}

export interface ProviderUpdate {
  base_url?: string;
  api_key?: string | null;
  default_model?: string;
  display_name?: string;
  enabled?: boolean;
  options?: Record<string, unknown>;
}

export interface ProviderModel {
  id: string;
  name: string;
  context_length: number;
  is_local: boolean;
  is_private: boolean;
  quality_score: number;
  capabilities: string[];
}

export interface TestConnectionResult {
  provider_id: string;
  connected: boolean;
  status: "connected" | "error";
  message: string;
}
/**
 * ETHAN WebUI — Identity providers API service (SCIM / LDAP / OAuth)
 *
 * Maps to the ETHAN API capability routes:
 *   SCIM : GET/POST /v1/scim/config · GET /v1/scim/status
 *   LDAP : GET/POST /v1/ldap/config · GET /v1/ldap/status
 *   OAuth: GET/POST /v1/oauth/providers · POST /v1/oauth/providers/{name}/disable
 *
 * Secrets policy: the API never returns secrets — GETs expose a
 * `<field>_set` boolean instead. Secret fields are write-only: sending an
 * empty value preserves the Core-stored secret. This client mirrors that
 * contract and the WebUI never displays secret values.
 *
 * Core-owned logic: core/auth/scim.py · core/auth/ldap.py · core/auth/oauth.py
 */

import { apiFetch } from '@/lib/api/client';

export interface IdentityConfig {
  enabled: boolean;
  /** Secret redacted server-side — always "" in responses. */
  bearer_token?: string;
  bearer_token_set?: boolean;
  server_url?: string;
  bind_dn?: string;
  bind_password?: string;
  bind_password_set?: boolean;
  user_search_base?: string;
  user_search_filter?: string;
  tls_enabled?: boolean;
  base_url?: string;
  metadata?: Record<string, unknown>;
}

export interface OAuthProvider {
  id: string;
  name: string;
  client_id: string;
  /** Secret redacted server-side — always "" in responses. */
  client_secret?: string;
  client_secret_set?: boolean;
  authorize_url: string;
  token_url: string;
  userinfo_url: string;
  scopes: string[];
  enabled: boolean;
}

// ── SCIM ────────────────────────────────────────────────────────────────────

export async function getScimConfig(): Promise<IdentityConfig> {
  return apiFetch<IdentityConfig>('/v1/scim/config');
}

export async function configureScim(data: {
  enabled: boolean;
  base_url: string;
  /** Leave empty to keep the token currently stored by the Core. */
  bearer_token?: string;
}): Promise<IdentityConfig> {
  return apiFetch<IdentityConfig>('/v1/scim/config', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getScimStatus(): Promise<{ enabled: boolean }> {
  return apiFetch<{ enabled: boolean }>('/v1/scim/status');
}

// ── LDAP ────────────────────────────────────────────────────────────────────

export async function getLdapConfig(): Promise<IdentityConfig> {
  return apiFetch<IdentityConfig>('/v1/ldap/config');
}

export async function configureLdap(data: {
  server_url: string;
  bind_dn: string;
  /** Leave empty to keep the password currently stored by the Core. */
  bind_password?: string;
  user_search_base: string;
  user_search_filter?: string;
  tls_enabled: boolean;
}): Promise<IdentityConfig> {
  return apiFetch<IdentityConfig>('/v1/ldap/config', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getLdapStatus(): Promise<{ enabled: boolean }> {
  return apiFetch<{ enabled: boolean }>('/v1/ldap/status');
}

// ── OAuth ───────────────────────────────────────────────────────────────────

export async function listOAuthProviders(): Promise<OAuthProvider[]> {
  return apiFetch<OAuthProvider[]>('/v1/oauth/providers');
}

export async function registerOAuthProvider(data: {
  name: string;
  client_id: string;
  client_secret: string;
  authorize_url: string;
  token_url: string;
  userinfo_url: string;
  scopes?: string[];
}): Promise<OAuthProvider> {
  return apiFetch<OAuthProvider>('/v1/oauth/providers', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function disableOAuthProvider(name: string): Promise<OAuthProvider> {
  return apiFetch<OAuthProvider>(`/v1/oauth/providers/${encodeURIComponent(name)}/disable`, {
    method: 'POST',
  });
}
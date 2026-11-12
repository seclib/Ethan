export const REALTIME_WEB_SOCKET_PATH = "/v1/ws";
export const TERMINAL_WEB_SOCKET_PATH = "/v1/terminal/ws";
export const DEVELOPMENT_WEB_SOCKET_URL = "ws://localhost:8000/v1/ws";
export const DEVELOPMENT_TERMINAL_WEB_SOCKET_URL = "ws://localhost:8000/v1/terminal/ws";

export class WebSocketConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebSocketConfigurationError";
  }
}

function isProductionEnvironment(isProduction?: boolean): boolean {
  if (isProduction !== undefined) return isProduction;
  return process.env.NODE_ENV === "production";
}

function isSecureBrowser(browserProtocol?: string): boolean {
  if (browserProtocol) return browserProtocol === "https:";
  return typeof window !== "undefined" && window.location.protocol === "https:";
}

export type ResolvedWebSocketUrl = string;

interface ResolveWebSocketOptions {
  expectedPath: string;
  rawUrl?: string | null;
  fallbackUrl?: string;
  isProduction?: boolean;
  isSecurePage?: boolean;
}

function normalizeWebSocketUrl({
  expectedPath,
  rawUrl,
  fallbackUrl,
  isProduction,
  isSecurePage,
}: ResolveWebSocketOptions): ResolvedWebSocketUrl {
  const production = isProductionEnvironment(isProduction);
  const securePage = isSecurePage ?? isSecureBrowser();
  const definedUrl = rawUrl && rawUrl.trim() !== "" ? rawUrl.trim() : undefined;

  if (!definedUrl && !fallbackUrl) {
    throw new WebSocketConfigurationError(
      "NEXT_PUBLIC_WS_URL must be configured in production.",
    );
  }

  const candidate = definedUrl ?? fallbackUrl!;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new WebSocketConfigurationError(
      `Invalid WebSocket URL: ${candidate}`,
    );
  }

  // Local-only destination policy. This intentionally excludes public domains
  // and remote IP addresses, while accepting the loopback hosts used by ETHAN.
  const normalizedHostname = parsed.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  const allowedHostnames = new Set(["localhost", "127.0.0.1", "::1"]);
  if (!allowedHostnames.has(normalizedHostname)) {
    throw new WebSocketConfigurationError(
      `WebSocket host must be a local loopback address: ${candidate}`,
    );
  }

  if (parsed.username || parsed.password) {
    throw new WebSocketConfigurationError(
      "WebSocket URL must not contain credentials.",
    );
  }

  if (!/^wss?:$/i.test(parsed.protocol)) {
    throw new WebSocketConfigurationError(
      `WebSocket URL must use ws:// or wss://: ${candidate}`,
    );
  }

  // Prevent accidental JWT passing, including mixed-case query parameters.
  for (const key of parsed.searchParams.keys()) {
    if (key.toLowerCase() === "token") {
      throw new WebSocketConfigurationError(
        "WebSocket URL must not contain a JWT.",
      );
    }
  }

  // Seul le contexte navigateur HTTPS impose WSS. Un NODE_ENV=production
  // local sur HTTP ne doit pas interdire ws://localhost.
  const secureContext = securePage;
  if (secureContext && parsed.protocol.toLowerCase() === "ws:") {
    throw new WebSocketConfigurationError(
      `WebSocket URL must use wss:// in production or over HTTPS: ${candidate}`,
    );
  }

  if (parsed.pathname !== expectedPath) {
    throw new WebSocketConfigurationError(
      `WebSocket URL must target ${expectedPath}, received ${parsed.pathname}`,
    );
  }

  return parsed.toString();
}

export function resolveRealtimeWebSocketUrl(
  rawUrl?: string | null,
  isProduction?: boolean,
  isSecurePage?: boolean,
): ResolvedWebSocketUrl {
  const resolvedRawUrl = rawUrl ?? process.env.NEXT_PUBLIC_WS_URL;
  const explicitlySecure = isSecurePage ??
    (typeof window !== "undefined" &&
      window.location.protocol === "https:");
  return normalizeWebSocketUrl({
    expectedPath: REALTIME_WEB_SOCKET_PATH,
    rawUrl: resolvedRawUrl,
    fallbackUrl: !isProductionEnvironment(isProduction)
      ? DEVELOPMENT_WEB_SOCKET_URL
      : undefined,
    isProduction,
    isSecurePage: explicitlySecure,
  });
}

export function resolveTerminalWebSocketUrl(
  rawUrl: string | null | undefined = process.env.NEXT_PUBLIC_WS_URL,
  isProduction?: boolean,
): ResolvedWebSocketUrl {
  return normalizeWebSocketUrl({
    expectedPath: TERMINAL_WEB_SOCKET_PATH,
    rawUrl,
    fallbackUrl: !isProductionEnvironment(isProduction)
      ? DEVELOPMENT_TERMINAL_WEB_SOCKET_URL
      : undefined,
    isProduction,
    isSecurePage: undefined,
  });
}

import { buildWebSocketUrl } from "@/providers/websocket-provider";
import { WebSocketConfigurationError } from "@/lib/websocket-url";
import { terminalSocketUrl } from "@/lib/api/terminal";

const originalEnv = { ...process.env };

afterEach(() => {
  process.env = { ...originalEnv };
});

describe("WebSocket URL construction", () => {
  it("uses the FastAPI realtime endpoint in development", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    process.env.NODE_ENV = "development";

    expect(buildWebSocketUrl()).toBe("ws://localhost:8000/v1/ws");
    expect(buildWebSocketUrl().includes("token=")).toBe(false);
  });

  it("honours an explicit realtime WebSocket URL", () => {
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:9000/v1/ws";

    expect(buildWebSocketUrl(process.env.NEXT_PUBLIC_WS_URL)).toBe(
      "ws://localhost:9000/v1/ws",
    );
  });

  it("accepts local ws:// on an HTTP page even in production", () => {
    process.env.NODE_ENV = "production";
    delete process.env.NEXT_PUBLIC_WS_URL;

    expect(buildWebSocketUrl("ws://localhost:8000/v1/ws", true)).toBe(
      "ws://localhost:8000/v1/ws",
    );
  });

  it("rejects ws:// when the page is served over HTTPS", () => {
    process.env.NODE_ENV = "production";
    delete process.env.NEXT_PUBLIC_WS_URL;

    expect(() => buildWebSocketUrl("ws://localhost:8000/v1/ws", true, true)).toThrow(
      /wss:\/\//,
    );
  });

  it("accepts an explicit wss:// localhost realtime endpoint", () => {
    process.env.NODE_ENV = "production";

    expect(buildWebSocketUrl("wss://localhost:9000/v1/ws", true)).toBe(
      "wss://localhost:9000/v1/ws",
    );
  });

  it("rejects production configuration without a URL", () => {
    process.env.NODE_ENV = "production";
    delete process.env.NEXT_PUBLIC_WS_URL;

    expect(() => buildWebSocketUrl(undefined, true)).toThrow(
      "NEXT_PUBLIC_WS_URL must be configured in production.",
    );
  });

  it("rejects an invalid realtime path", () => {
    process.env.NODE_ENV = "development";

    expect(() => buildWebSocketUrl("ws://localhost:8000/private", false)).toThrow(
      /target \/v1\/ws/,
    );
  });

  it("rejects a non-WebSocket scheme", () => {
    process.env.NODE_ENV = "development";

    expect(() =>
      buildWebSocketUrl("http://localhost:8000/v1/ws", false),
    ).toThrow(/ws:\/\/ or wss:\/\//);
  });

  it("rejects a relative realtime URL", () => {
    process.env.NODE_ENV = "development";

    expect(() => buildWebSocketUrl("/v1/ws", false)).toThrow(
      /Invalid WebSocket URL/,
    );
  });

  it("never contains a JWT token", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    process.env.NODE_ENV = "development";

    expect(buildWebSocketUrl()).not.toMatch(/token=/);
  });
});

describe("Terminal WebSocket URL", () => {
  it("targets FastAPI without putting JWT in the URL", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    delete process.env.NEXT_PUBLIC_ETHAN_API_URL;
    process.env.NODE_ENV = "development";

    const url = terminalSocketUrl("session-1");

    expect(url).not.toMatch(/token=/);
    expect(new URL(url).pathname).toBe("/v1/terminal/ws");
    expect(new URL(url).searchParams.get("session_id")).toBe("session-1");
  });

  it("uses an explicit frontend WebSocket URL", () => {
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:9000/v1/ws";
    process.env.NODE_ENV = "development";

    expect(terminalSocketUrl()).toBe("ws://localhost:9000/v1/terminal/ws");
  });

  it("derives the backend origin from a direct HTTPS localhost API URL in development", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    process.env.NEXT_PUBLIC_ETHAN_API_URL = "https://localhost";
    process.env.NODE_ENV = "development";

    expect(terminalSocketUrl()).toBe("wss://localhost/v1/terminal/ws");
  });

  it("rejects production configuration without an explicit origin", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    delete process.env.NEXT_PUBLIC_ETHAN_API_URL;
    process.env.NODE_ENV = "production";

    expect(() => terminalSocketUrl()).toThrow(
      "NEXT_PUBLIC_WS_URL (or NEXT_PUBLIC_ETHAN_API_URL) must be configured in production.",
    );
  });

  it("accepts an explicit ws:// terminal origin on an HTTP page even in production", () => {
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:9000/v1/ws";
    process.env.NODE_ENV = "production";

    expect(terminalSocketUrl()).toBe("ws://localhost:9000/v1/terminal/ws");
  });

  it("rejects ws:// terminal origin when the page is served over HTTPS", () => {
    process.env.NODE_ENV = "production";
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:9000/v1/ws";
    const previousLocation = global.window.location;
    Object.defineProperty(global.window, "location", {
      configurable: true,
      value: { protocol: "https:" },
    });
    try {
      expect(() => terminalSocketUrl()).toThrow("wss://");
    } finally {
      Object.defineProperty(global.window, "location", {
        configurable: true,
        value: previousLocation,
      });
    }
  });

  it("rejects a relative terminal WebSocket URL in production", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    process.env.NEXT_PUBLIC_ETHAN_API_URL = "/api";
    process.env.NODE_ENV = "production";

    expect(() => terminalSocketUrl()).toThrow(
      "NEXT_PUBLIC_WS_URL (or NEXT_PUBLIC_ETHAN_API_URL) must be configured in production.",
    );
  });
});

describe("Local-only WebSocket destinations", () => {
  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("rejects a remote hostname in development", () => {
    process.env.NODE_ENV = "development";
    expect(() =>
      buildWebSocketUrl("ws://evil.example/v1/ws", false),
    ).toThrow(/must be a local loopback address/);
  });

  it("rejects a non-loopback IPv4 address", () => {
    process.env.NODE_ENV = "development";
    expect(() =>
      buildWebSocketUrl("ws://192.168.1.12/v1/ws", false),
    ).toThrow(/local loopback address/);
  });

  it("accepts IPv6 loopback on a custom port", () => {
    process.env.NODE_ENV = "development";
    expect(buildWebSocketUrl("ws://[::1]:9000/v1/ws", false)).toBe(
      "ws://[::1]:9000/v1/ws",
    );
  });

  it("accepts IPv4 loopback on a custom port", () => {
    process.env.NODE_ENV = "development";
    expect(buildWebSocketUrl("ws://127.0.0.1:9000/v1/ws", false)).toBe(
      "ws://127.0.0.1:9000/v1/ws",
    );
  });

  it("accepts localhost regardless of the port", () => {
    process.env.NODE_ENV = "development";
    expect(buildWebSocketUrl("ws://localhost:8080/v1/ws", false)).toBe(
      "ws://localhost:8080/v1/ws",
    );
  });

  it("rejects a relative URL", () => {
    process.env.NODE_ENV = "development";
    expect(() => buildWebSocketUrl("/v1/ws", false)).toThrow(
      /Invalid WebSocket URL/,
    );
  });

  it("rejects a URL with embedded credentials", () => {
    process.env.NODE_ENV = "development";
    expect(() =>
      buildWebSocketUrl("ws://user:password@localhost/v1/ws", false),
    ).toThrow(/credentials/);
  });

  it("rejects a URL containing a token query parameter", () => {
    process.env.NODE_ENV = "development";
    expect(() =>
      buildWebSocketUrl("ws://localhost:8000/v1/ws?token=secret", false),
    ).toThrow(/JWT/);
  });

  it("rejects an unexpected path", () => {
    process.env.NODE_ENV = "development";
    expect(() => buildWebSocketUrl("ws://localhost:8000/private", false)).toThrow(
      /target \/v1\/ws/,
    );
  });

  it("rejects ws:// from an HTTPS page even in development", () => {
    const previousLocation = global.window.location;
    process.env.NODE_ENV = "development";
    Object.defineProperty(global.window, "location", {
      configurable: true,
      value: { protocol: "https:" },
    });
    try {
      expect(() =>
        buildWebSocketUrl("ws://localhost:8000/v1/ws", false),
      ).toThrow(/wss:\/\//);
    } finally {
      Object.defineProperty(global.window, "location", {
        configurable: true,
        value: previousLocation,
      });
    }
  });

  it("accepts wss:// from an HTTP-loaded page in production", () => {
    process.env.NODE_ENV = "production";
    expect(buildWebSocketUrl("wss://localhost:8080/v1/ws", true)).toBe(
      "wss://localhost:8080/v1/ws",
    );
  });

  it("keeps a valid terminal session_id parameter", () => {
    process.env.NODE_ENV = "development";
    const url = terminalSocketUrl("audit-session");
    expect(new URL(url).searchParams.get("session_id")).toBe("audit-session");
    expect(url).not.toMatch(/token=/);
  });
});

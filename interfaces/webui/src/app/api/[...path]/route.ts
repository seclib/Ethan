import { NextRequest, NextResponse } from "next/server";

async function proxyRequest(request: NextRequest) {
  // pathname will be /api/auth/login, /api/auth/me, etc.
  const pathname = request.nextUrl.pathname;
  // Remove /api prefix to match backend routes (/auth/login, etc.)
  const targetPath = pathname.replace(/^\/api/, "");
  
  const backendUrl = process.env.ETHAN_API_URL || "http://localhost:8000";
  const url = `${backendUrl}${targetPath}${request.nextUrl.search}`;

  const headers = new Headers(request.headers);
  headers.delete("host"); // Let fetch set the correct host

  // ── JWT Cookie → Authorization header ─────────────────────────────────
  // The browser stores the JWT in an HttpOnly cookie (ethan_token), but the
  // backend API expects it in the Authorization: Bearer header.  Convert
  // the cookie to a header so authenticated requests reach the backend.
  const authToken = request.cookies.get("ethan_token")?.value;
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  try {
    let body: BodyInit | null = null;
    if (request.method !== "GET" && request.method !== "HEAD") {
      const contentType = request.headers.get("content-type") || "";
      if (contentType.includes("multipart/form-data") || contentType.includes("application/octet-stream")) {
        // Preserve binary payloads for file uploads.
        body = await request.arrayBuffer();
      } else {
        body = await request.text();
      }
    }

    const response = await fetch(url, {
      method: request.method,
      headers,
      body,
      ...(body instanceof ArrayBuffer ? { duplex: "half" } : {}),
    } as RequestInit);

    // Preserve binary responses (file downloads) by using arrayBuffer.
    const responseContentType = response.headers.get("content-type") || "";
    const isBinary =
      responseContentType.includes("application/octet-stream") ||
      responseContentType.includes("application/pdf") ||
      responseContentType.includes("image/") ||
      responseContentType.includes("font/");

        // ── Handle Server-Sent Events (SSE) streaming ─────────────────────
    // For chat completion streams (content-type: text/event-stream), we MUST
    // pipe the body chunks directly so the browser receives each token in real
    // time. We never buffer the full response.
    const isStreaming =
      responseContentType.includes("text/event-stream") ||
      responseContentType.includes("text/stream");

    if (isStreaming && typeof response.body?.getReader === "function") {
      // Build headers excluding hop-by-hop fields
      const responseHeaders = new Headers();
      response.headers.forEach((value, key) => {
        const lowerKey = key.toLowerCase();
        if (
          lowerKey !== "content-encoding" &&
          lowerKey !== "transfer-encoding" &&
          lowerKey !== "content-length" &&
          lowerKey !== "set-cookie"
        ) {
          responseHeaders.set(key, value);
        }
      });
      // Force connection upgrade headers for SSE
      responseHeaders.set("Cache-Control", "no-cache, no-transform, permanent-store");
      responseHeaders.set("Connection", "keep-alive");

      // Pipe the raw stream through the proxy
      const proxyStream = response.body.pipeThrough(
        new TransformStream({
          transform(chunk, controller) {
            controller.enqueue(chunk);
          },
        }),
      ) as ReadableStream;

      return new NextResponse(proxyStream, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    }

    // ── Non-streaming responses ──────────────────────────────────────────
    // Read the body ONCE — binary → ArrayBuffer, text → string.
    let responseText = "";
    let responseBuffer: ArrayBuffer | null = null;
    if (isBinary) {
      responseBuffer = await response.arrayBuffer();
    } else {
      responseText = await response.text();
    }

    let nextResponse: NextResponse;
    if (isBinary) {
      nextResponse = new NextResponse(responseBuffer, {
        status: response.status,
        statusText: response.statusText,
      });
    } else {
      nextResponse = new NextResponse(responseText, {
        status: response.status,
        statusText: response.statusText,
      });
    }

    // Copy all headers
    response.headers.forEach((value, key) => {
      const lowerKey = key.toLowerCase();
      if (
        lowerKey !== "content-encoding" &&
        lowerKey !== "transfer-encoding" &&
        lowerKey !== "content-length" &&
        lowerKey !== "set-cookie"
      ) {
        nextResponse.headers.set(key, value);
      }
    });

    // Ensure content-type is correctly set
    const contentType = response.headers.get("content-type");
    if (contentType) {
      nextResponse.headers.set("content-type", contentType);
    }

    // ── Cookie management ─────────────────────────────────────────────
    // The backend sets HttpOnly cookies via response.set_cookie(), but
    // this route handler proxies via server-side fetch(). The Set-Cookie
    // from the backend is bound to the backend origin (e.g. :8000), NOT
    // the browser origin (:3001). We read the token from the JSON body
    // and set the cookie directly on the NextResponse.
    const cookieOpts = {
      httpOnly: true,
      sameSite: "lax" as const,
      maxAge: 86400,
      path: "/",
      secure: process.env.NODE_ENV === "production",
    };

    if ((targetPath === "/auth/login" || targetPath === "/auth/refresh") && response.ok) {
      try {
        const data = JSON.parse(responseText);
        const token = data.access_token || data.token;
        if (token) {
          nextResponse.cookies.set("ethan_token", token, cookieOpts);
        }
      } catch { /* JSON parse failed — skip cookie */ }
    } else if (targetPath === "/auth/logout") {
      nextResponse.cookies.delete("ethan_token");
    }

    return nextResponse;
  } catch (error) {
    console.error(`Auth proxy error for ${pathname}:`, error);
    return NextResponse.json({ detail: "Internal Proxy Error" }, { status: 500 });
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;

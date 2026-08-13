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
    let body;
    if (request.method !== "GET" && request.method !== "HEAD") {
      body = await request.text();
    }

    const response = await fetch(url, {
      method: request.method,
      headers,
      body,
    });

    const responseText = await response.text();
    const nextResponse = new NextResponse(responseText, {
      status: response.status,
      statusText: response.statusText,
    });

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
    // the browser origin (:3000). We read the token from the JSON body
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

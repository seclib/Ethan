module.exports = [
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/action-async-storage.external.js [external] (next/dist/server/app-render/action-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/action-async-storage.external.js", () => require("next/dist/server/app-render/action-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/runtime-reacts.external.js [external] (next/dist/server/runtime-reacts.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/server/runtime-reacts.external.js", () => require("next/dist/server/runtime-reacts.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/node:stream [external] (node:stream, cjs)", ((__turbopack_context__, module, exports) => {

var mod = __turbopack_context__.x("node:stream", () => require("node:stream"));

module.exports = mod;
}),
"[project]/src/app/api/[...path]/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "DELETE",
    ()=>DELETE,
    "GET",
    ()=>GET,
    "PATCH",
    ()=>PATCH,
    "POST",
    ()=>POST,
    "PUT",
    ()=>PUT
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
async function proxyRequest(request) {
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
        let body = null;
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
            ...body instanceof ArrayBuffer ? {
                duplex: "half"
            } : {}
        });
        // Preserve binary responses (file downloads) by using arrayBuffer.
        const responseContentType = response.headers.get("content-type") || "";
        const isBinary = responseContentType.includes("application/octet-stream") || responseContentType.includes("application/pdf") || responseContentType.includes("image/") || responseContentType.includes("font/");
        // ── Handle Server-Sent Events (SSE) streaming ─────────────────────
        // For chat completion streams (content-type: text/event-stream), we MUST
        // pipe the body chunks directly so the browser receives each token in real
        // time. We never buffer the full response.
        const isStreaming = responseContentType.includes("text/event-stream") || responseContentType.includes("text/stream");
        if (isStreaming && typeof response.body?.getReader === "function") {
            // Build headers excluding hop-by-hop fields
            const responseHeaders = new Headers();
            response.headers.forEach((value, key)=>{
                const lowerKey = key.toLowerCase();
                if (lowerKey !== "content-encoding" && lowerKey !== "transfer-encoding" && lowerKey !== "content-length" && lowerKey !== "set-cookie") {
                    responseHeaders.set(key, value);
                }
            });
            // Force connection upgrade headers for SSE
            responseHeaders.set("Cache-Control", "no-cache, no-transform, permanent-store");
            responseHeaders.set("Connection", "keep-alive");
            // Pipe the raw stream through the proxy
            const proxyStream = response.body.pipeThrough(new TransformStream({
                transform (chunk, controller) {
                    controller.enqueue(chunk);
                }
            }));
            return new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"](proxyStream, {
                status: response.status,
                statusText: response.statusText,
                headers: responseHeaders
            });
        }
        // ── Non-streaming responses ──────────────────────────────────────────
        // Read the body ONCE — binary → ArrayBuffer, text → string.
        let responseText = "";
        let responseBuffer = null;
        if (isBinary) {
            responseBuffer = await response.arrayBuffer();
        } else {
            responseText = await response.text();
        }
        let nextResponse;
        if (isBinary) {
            nextResponse = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"](responseBuffer, {
                status: response.status,
                statusText: response.statusText
            });
        } else {
            nextResponse = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"](responseText, {
                status: response.status,
                statusText: response.statusText
            });
        }
        // Copy all headers
        response.headers.forEach((value, key)=>{
            const lowerKey = key.toLowerCase();
            if (lowerKey !== "content-encoding" && lowerKey !== "transfer-encoding" && lowerKey !== "content-length" && lowerKey !== "set-cookie") {
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
            sameSite: "lax",
            maxAge: 86400,
            path: "/",
            secure: ("TURBOPACK compile-time value", "development") === "production"
        };
        if ((targetPath === "/auth/login" || targetPath === "/auth/refresh") && response.ok) {
            try {
                const data = JSON.parse(responseText);
                const token = data.access_token || data.token;
                if (token) {
                    nextResponse.cookies.set("ethan_token", token, cookieOpts);
                }
            } catch  {}
        } else if (targetPath === "/auth/logout") {
            nextResponse.cookies.delete("ethan_token");
        }
        return nextResponse;
    } catch (error) {
        console.error(`Auth proxy error for ${pathname}:`, error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            detail: "Internal Proxy Error"
        }, {
            status: 500
        });
    }
}
const GET = proxyRequest;
const POST = proxyRequest;
const PUT = proxyRequest;
const DELETE = proxyRequest;
const PATCH = proxyRequest;
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__211qyrs._.js.map
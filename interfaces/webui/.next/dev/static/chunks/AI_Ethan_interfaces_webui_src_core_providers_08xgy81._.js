(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/AI/Ethan/interfaces/webui/src/core/providers/theme-provider.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ThemeProvider",
    ()=>ThemeProvider,
    "useTheme",
    ()=>useTheme
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
"use client";
;
const ThemeContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])(undefined);
function ThemeProvider({ children }) {
    _s();
    const [theme, setTheme] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("dark");
    const [resolvedTheme, setResolvedTheme] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("dark");
    // Load theme from localStorage on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ThemeProvider.useEffect": ()=>{
            const stored = localStorage.getItem("ethan_theme");
            if (stored) {
                setTheme(stored);
            }
        }
    }["ThemeProvider.useEffect"], []);
    // Resolve system theme
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ThemeProvider.useEffect": ()=>{
            const resolveTheme = {
                "ThemeProvider.useEffect.resolveTheme": ()=>{
                    if (theme === "system") {
                        const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
                        setResolvedTheme(systemTheme);
                    } else {
                        setResolvedTheme(theme);
                    }
                }
            }["ThemeProvider.useEffect.resolveTheme"];
            resolveTheme();
            // Listen for system theme changes
            const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
            const handler = {
                "ThemeProvider.useEffect.handler": ()=>{
                    if (theme === "system") {
                        resolveTheme();
                    }
                }
            }["ThemeProvider.useEffect.handler"];
            mediaQuery.addEventListener("change", handler);
            return ({
                "ThemeProvider.useEffect": ()=>mediaQuery.removeEventListener("change", handler)
            })["ThemeProvider.useEffect"];
        }
    }["ThemeProvider.useEffect"], [
        theme
    ]);
    // Detect high contrast preference
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ThemeProvider.useEffect": ()=>{
            const mediaQuery = window.matchMedia("(prefers-contrast: high)");
            const handler = {
                "ThemeProvider.useEffect.handler": (e)=>{
                    if (e.matches && theme === "system") {
                        setResolvedTheme("high-contrast");
                    }
                }
            }["ThemeProvider.useEffect.handler"];
            mediaQuery.addEventListener("change", handler);
            return ({
                "ThemeProvider.useEffect": ()=>mediaQuery.removeEventListener("change", handler)
            })["ThemeProvider.useEffect"];
        }
    }["ThemeProvider.useEffect"], [
        theme
    ]);
    // Apply theme to document
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "ThemeProvider.useEffect": ()=>{
            const root = document.documentElement;
            root.classList.remove("light", "dark", "high-contrast", "oled");
            root.setAttribute("data-theme", resolvedTheme);
        }
    }["ThemeProvider.useEffect"], [
        resolvedTheme
    ]);
    const value = {
        theme,
        setTheme: (newTheme)=>{
            localStorage.setItem("ethan_theme", newTheme);
            setTheme(newTheme);
        },
        resolvedTheme,
        isDark: resolvedTheme === "dark",
        isLight: resolvedTheme === "light",
        isHighContrast: resolvedTheme === "high-contrast",
        isOLED: resolvedTheme === "oled"
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ThemeContext.Provider, {
        value: value,
        children: children
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/core/providers/theme-provider.tsx",
        lineNumber: 87,
        columnNumber: 5
    }, this);
}
_s(ThemeProvider, "QxeWmcxF4PMGqQ177N80Lud+ZP4=");
_c = ThemeProvider;
function useTheme() {
    _s1();
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useContext"])(ThemeContext);
    if (context === undefined) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
}
_s1(useTheme, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var _c;
__turbopack_context__.k.register(_c, "ThemeProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/AI/Ethan/interfaces/webui/src/core/providers/query-provider.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "QueryProvider",
    ()=>QueryProvider
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$query$2d$core$2f$build$2f$modern$2f$queryClient$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/query-core/build/modern/queryClient.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
function QueryProvider({ children }) {
    _s();
    const [queryClient] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        "QueryProvider.useState": ()=>new __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$query$2d$core$2f$build$2f$modern$2f$queryClient$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["QueryClient"]({
                defaultOptions: {
                    queries: {
                        staleTime: 5 * 60 * 1000,
                        gcTime: 10 * 60 * 1000,
                        retry: 1,
                        refetchOnWindowFocus: false,
                        throwOnError: false
                    },
                    mutations: {
                        retry: 0
                    }
                }
            })
    }["QueryProvider.useState"]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["QueryClientProvider"], {
        client: queryClient,
        children: children
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/core/providers/query-provider.tsx",
        lineNumber: 26,
        columnNumber: 5
    }, this);
}
_s(QueryProvider, "3fFUUYM+R6bRNcrSSzo/0Co/yYM=");
_c = QueryProvider;
var _c;
__turbopack_context__.k.register(_c, "QueryProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/AI/Ethan/interfaces/webui/src/core/providers/websocket-provider.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "WebSocketProvider",
    ()=>WebSocketProvider,
    "useWebSocket",
    ()=>useWebSocket
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
"use client";
;
const WebSocketContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])(undefined);
const WS_URL = __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";
function WebSocketProvider({ children }) {
    _s();
    const [status, setStatus] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("disconnected");
    const [lastEvent, setLastEvent] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const wsRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const reconnectTimeoutRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const subscriptionsRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(new Set());
    const connect = ()=>{
        if (wsRef.current?.readyState === WebSocket.OPEN) return;
        setStatus("connecting");
        try {
            const token = localStorage.getItem("ethan_token");
            const url = token ? `${WS_URL}?token=${token}` : WS_URL;
            const ws = new WebSocket(url);
            ws.onopen = ()=>{
                setStatus("connected");
                // Resubscribe to all channels
                subscriptionsRef.current.forEach((channel)=>{
                    ws.send(JSON.stringify({
                        type: "subscribe",
                        channel
                    }));
                });
            };
            ws.onmessage = (event)=>{
                try {
                    const data = JSON.parse(event.data);
                    setLastEvent(data);
                } catch  {
                // Ignore malformed messages
                }
            };
            ws.onclose = ()=>{
                setStatus("disconnected");
                wsRef.current = null;
                // Auto-reconnect after 5 seconds
                reconnectTimeoutRef.current = setTimeout(connect, 5000);
            };
            ws.onerror = ()=>{
                setStatus("error");
                ws.close();
            };
            wsRef.current = ws;
        } catch  {
            setStatus("error");
            // Retry connection after 10 seconds
            reconnectTimeoutRef.current = setTimeout(connect, 10000);
        }
    };
    const disconnect = ()=>{
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        subscriptionsRef.current.clear();
        wsRef.current?.close();
        wsRef.current = null;
        setStatus("disconnected");
    };
    const subscribe = (channel)=>{
        subscriptionsRef.current.add(channel);
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: "subscribe",
                channel
            }));
        }
    };
    const unsubscribe = (channel)=>{
        subscriptionsRef.current.delete(channel);
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: "unsubscribe",
                channel
            }));
        }
    };
    // Connect on mount, disconnect on unmount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "WebSocketProvider.useEffect": ()=>{
            connect();
            return ({
                "WebSocketProvider.useEffect": ()=>disconnect()
            })["WebSocketProvider.useEffect"];
        // eslint-disable-next-line react-hooks/exhaustive-deps
        }
    }["WebSocketProvider.useEffect"], []);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(WebSocketContext.Provider, {
        value: {
            status,
            subscribe,
            unsubscribe,
            lastEvent
        },
        children: children
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/core/providers/websocket-provider.tsx",
        lineNumber: 105,
        columnNumber: 5
    }, this);
}
_s(WebSocketProvider, "DxEqGaN8Lw6/x93Pm7E8BJnnuCw=");
_c = WebSocketProvider;
function useWebSocket() {
    _s1();
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useContext"])(WebSocketContext);
    if (context === undefined) {
        throw new Error("useWebSocket must be used within a WebSocketProvider");
    }
    return context;
}
_s1(useWebSocket, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var _c;
__turbopack_context__.k.register(_c, "WebSocketProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/AI/Ethan/interfaces/webui/src/core/providers/auth-provider.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AuthProvider",
    ()=>AuthProvider,
    "useAuth",
    ()=>useAuth
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
"use client";
;
const AuthContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])(undefined);
function AuthProvider({ children }) {
    _s();
    const [user, setUser] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [isLoading, setIsLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const isAuthenticated = !!user;
    // Check authentication on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AuthProvider.useEffect": ()=>{
            const checkAuth = {
                "AuthProvider.useEffect.checkAuth": async ()=>{
                    try {
                        const token = localStorage.getItem("ethan_token");
                        if (!token) {
                            setIsLoading(false);
                            return;
                        }
                        // Verify token with API
                        const response = await fetch("/api/v1/auth/me", {
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        });
                        if (response.ok) {
                            const data = await response.json();
                            setUser(data.user);
                        } else {
                            localStorage.removeItem("ethan_token");
                        }
                    } catch (error) {
                        console.error("Auth check failed:", error);
                        localStorage.removeItem("ethan_token");
                    } finally{
                        setIsLoading(false);
                    }
                }
            }["AuthProvider.useEffect.checkAuth"];
            checkAuth();
        }
    }["AuthProvider.useEffect"], []);
    const login = async (email, password, operatorId)=>{
        try {
            const response = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password,
                    operator_id: operatorId
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || "Authentication failed");
            }
            const data = await response.json();
            localStorage.setItem("ethan_token", data.token);
            if (operatorId) {
                localStorage.setItem("ethan_operator_id", operatorId);
            }
            setUser(data.user);
        } catch (error) {
            throw error;
        }
    };
    const logout = async ()=>{
        try {
            const token = localStorage.getItem("ethan_token");
            if (token) {
                await fetch("/api/v1/auth/logout", {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
            }
        } catch (error) {
            console.error("Logout error:", error);
        } finally{
            localStorage.removeItem("ethan_token");
            setUser(null);
        }
    };
    const refreshToken = async ()=>{
        try {
            const token = localStorage.getItem("ethan_token");
            if (!token) return;
            const response = await fetch("/api/v1/auth/refresh", {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem("ethan_token", data.token);
            } else {
                localStorage.removeItem("ethan_token");
                setUser(null);
            }
        } catch (error) {
            console.error("Token refresh failed:", error);
            localStorage.removeItem("ethan_token");
            setUser(null);
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(AuthContext.Provider, {
        value: {
            user,
            isLoading,
            isAuthenticated,
            login,
            logout,
            refreshToken
        },
        children: children
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/core/providers/auth-provider.tsx",
        lineNumber: 129,
        columnNumber: 5
    }, this);
}
_s(AuthProvider, "YajQB7LURzRD+QP5gw0+K2TZIWA=");
_c = AuthProvider;
function useAuth() {
    _s1();
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useContext"])(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
_s1(useAuth, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var _c;
__turbopack_context__.k.register(_c, "AuthProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=AI_Ethan_interfaces_webui_src_core_providers_08xgy81._.js.map
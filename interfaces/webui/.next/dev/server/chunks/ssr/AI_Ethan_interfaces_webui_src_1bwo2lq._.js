module.exports = [
"[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Card",
    ()=>Card,
    "CardAction",
    ()=>CardAction,
    "CardContent",
    ()=>CardContent,
    "CardDescription",
    ()=>CardDescription,
    "CardFooter",
    ()=>CardFooter,
    "CardHeader",
    ()=>CardHeader,
    "CardTitle",
    ()=>CardTitle
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
"use client";
;
;
function Card({ className, variant = "default", hoverable = false, ...props }) {
    const variantClasses = {
        default: "bg-background",
        elevated: "bg-background shadow-md",
        outlined: "bg-background border border-line-2"
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("flex flex-col gap-6 rounded-xl border py-5 transition-all duration-100", variantClasses[variant], hoverable && "cursor-pointer hover:border-line-3 hover:shadow-lg hover:glow-sm", variant === "default" && "border-line-1", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 19,
        columnNumber: 5
    }, this);
}
function CardHeader({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-header",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("flex flex-col gap-1.5 px-5 has-[data-slot=card-action]:flex-row has-[data-slot=card-action]:items-center has-[data-slot=card-action]:justify-between", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 35,
        columnNumber: 5
    }, this);
}
function CardTitle({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-title",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("leading-none font-semibold text-foreground", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 48,
        columnNumber: 5
    }, this);
}
function CardDescription({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-description",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("text-sm text-foreground-secondary", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 58,
        columnNumber: 5
    }, this);
}
function CardAction({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-action",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("flex self-start items-center gap-1.5", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 68,
        columnNumber: 5
    }, this);
}
function CardContent({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-content",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("px-5", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 78,
        columnNumber: 5
    }, this);
}
function CardFooter({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        "data-slot": "card-footer",
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("flex items-center px-5", className),
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx",
        lineNumber: 84,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/badge.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Badge",
    ()=>Badge
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
;
function Badge({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
        className: `inline-flex items-center rounded-md border border-line-2 bg-bg-2 px-2 py-0.5 text-xs font-medium text-foreground ${className ?? ""}`,
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/badge.tsx",
        lineNumber: 5,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Button",
    ()=>Button,
    "buttonVariants",
    ()=>buttonVariants
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$class$2d$variance$2d$authority$2f$dist$2f$index$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/class-variance-authority/dist/index.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
"use client";
;
;
;
const buttonVariants = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$class$2d$variance$2d$authority$2f$dist$2f$index$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cva"])("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-100 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent-400 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", {
    variants: {
        variant: {
            // "default" is the primary action — aligns with Tailwind/shadcn convention
            default: "bg-accent-600 text-white shadow-sm hover:bg-accent-500 active:scale-[0.98]",
            // alias kept for backward compatibility with existing call-sites
            primary: "bg-accent-600 text-white shadow-sm hover:bg-accent-500 active:scale-[0.98]",
            secondary: "bg-background border border-line-2 text-foreground shadow-sm hover:bg-elevated hover:border-line-3",
            outline: "border border-line-2 bg-background text-foreground shadow-sm hover:bg-elevated hover:border-line-3",
            ghost: "text-foreground-secondary hover:bg-elevated hover:text-foreground",
            destructive: "bg-error-600 text-white shadow-sm hover:bg-error-500 active:scale-[0.98]"
        },
        size: {
            sm: "h-8 px-3 text-xs",
            md: "h-10 px-4 text-sm",
            lg: "h-12 px-6 text-base",
            icon: "h-10 w-10"
        }
    },
    defaultVariants: {
        variant: "default",
        size: "md"
    }
});
function Button({ className, variant, size, loading = false, icon, iconRight, children, disabled, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])(buttonVariants({
            variant,
            size,
            className
        })),
        disabled: disabled || loading,
        "aria-busy": loading,
        "aria-disabled": disabled || loading,
        ...props,
        children: [
            loading && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: "animate-spin h-4 w-4",
                xmlns: "http://www.w3.org/2000/svg",
                fill: "none",
                viewBox: "0 0 24 24",
                "aria-hidden": "true",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                        className: "opacity-25",
                        cx: "12",
                        cy: "12",
                        r: "10",
                        stroke: "currentColor",
                        strokeWidth: "4"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
                        lineNumber: 78,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                        className: "opacity-75",
                        fill: "currentColor",
                        d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
                        lineNumber: 86,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
                lineNumber: 71,
                columnNumber: 9
            }, this),
            !loading && icon && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "shrink-0",
                children: icon
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
                lineNumber: 93,
                columnNumber: 28
            }, this),
            children,
            !loading && iconRight && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "shrink-0",
                children: iconRight
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
                lineNumber: 95,
                columnNumber: 33
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx",
        lineNumber: 63,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Skeleton",
    ()=>Skeleton
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
"use client";
;
;
function Skeleton({ className, variant = "text", lines = 1, ...props }) {
    if (variant === "text") {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "flex flex-col gap-2",
            ...props,
            children: Array.from({
                length: lines
            }).map((_, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("h-4 rounded-md bg-line-1 animate-shimmer", i === lines - 1 && lines > 1 && "w-3/4", className),
                    style: {
                        background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
                        backgroundSize: "200% 100%",
                        animation: "shimmer 1.5s infinite"
                    }
                }, i, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx",
                    lineNumber: 16,
                    columnNumber: 11
                }, this))
        }, void 0, false, {
            fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx",
            lineNumber: 14,
            columnNumber: 7
        }, this);
    }
    if (variant === "circle") {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("rounded-full bg-line-1 animate-shimmer", className),
            style: {
                background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
                backgroundSize: "200% 100%",
                animation: "shimmer 1.5s infinite"
            },
            ...props
        }, void 0, false, {
            fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx",
            lineNumber: 36,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("rounded-lg bg-line-1 animate-shimmer", className),
        style: {
            background: "linear-gradient(90deg, var(--line-1) 25%, var(--line-2) 50%, var(--line-1) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s infinite"
        },
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx",
        lineNumber: 49,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Progress",
    ()=>Progress
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
"use client";
;
;
function Progress({ value = 0, max = 100, size = "md", variant = "default", showLabel = false, className, ...props }) {
    const percentage = Math.min(Math.max(value / max * 100, 0), 100);
    const sizeClasses = {
        sm: "h-1.5",
        md: "h-2.5",
        lg: "h-4"
    };
    const variantClasses = {
        default: "bg-accent-600",
        success: "bg-success",
        warning: "bg-warning",
        error: "bg-error"
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "w-full",
        role: "progressbar",
        "aria-valuenow": value,
        "aria-valuemin": 0,
        "aria-valuemax": max,
        ...props,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("w-full bg-elevated rounded-full overflow-hidden", sizeClasses[size]),
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("h-full rounded-full transition-all duration-300", variantClasses[variant]),
                    style: {
                        width: `${percentage}%`
                    }
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
                    lineNumber: 41,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
                lineNumber: 40,
                columnNumber: 7
            }, this),
            showLabel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex justify-between mt-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-foreground-tertiary",
                        children: value
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
                        lineNumber: 48,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-xs text-foreground-tertiary",
                        children: max
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
                        lineNumber: 49,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
                lineNumber: 47,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx",
        lineNumber: 39,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/separator.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Separator",
    ()=>Separator
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
;
function Separator({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        role: "separator",
        className: `shrink-0 bg-line-2 h-[1px] w-full ${className ?? ""}`,
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/separator.tsx",
        lineNumber: 5,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/ui/spinner.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Spinner",
    ()=>Spinner
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
;
function Spinner({ className, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        role: "status",
        "aria-label": "Chargement",
        className: `inline-flex h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent ${className ?? ""}`,
        ...props
    }, void 0, false, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/ui/spinner.tsx",
        lineNumber: 5,
        columnNumber: 5
    }, this);
}
;
}),
"[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "MetricCard",
    ()=>MetricCard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/badge.tsx [app-ssr] (ecmascript)");
"use client";
;
;
;
const statusToBadge = {
    normal: "success",
    warning: "warning",
    critical: "error",
    loading: "info",
    error: "error",
    na: "dim"
};
function MetricCard({ title, value, unit, status = "normal", icon, sparkline, progress, href, onClick, className = "", dragHandleProps }) {
    const handleClick = ()=>{
        if (href) {
            window.location.href = href;
        } else if (onClick) {
            onClick();
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("relative rounded-xl border border-line-2 bg-background p-4 transition-all duration-100", "hover:border-line-3 hover:shadow-md cursor-pointer", className),
        onClick: handleClick,
        role: href ? "link" : "button",
        tabIndex: 0,
        onKeyDown: (e)=>{
            if (e.key === "Enter" || e.key === " ") handleClick();
        },
        "data-testid": "metric-card",
        "data-status": status,
        ...dragHandleProps,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-start justify-between mb-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-sm text-foreground-secondary mb-1",
                                children: title
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                                lineNumber: 70,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-baseline gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-2xl font-bold text-foreground",
                                        children: value
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                                        lineNumber: 72,
                                        columnNumber: 13
                                    }, this),
                                    unit && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-sm text-foreground-tertiary",
                                        children: unit
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                                        lineNumber: 73,
                                        columnNumber: 22
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                                lineNumber: 71,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                        lineNumber: 69,
                        columnNumber: 9
                    }, this),
                    icon && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-2xl ml-2",
                        children: icon
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                        lineNumber: 76,
                        columnNumber: 18
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                lineNumber: 68,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "absolute top-3 right-3",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                    variant: statusToBadge[status] || "dim",
                    size: "sm",
                    dot: true,
                    children: status
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                    lineNumber: 80,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                lineNumber: 79,
                columnNumber: 7
            }, this),
            sparkline && sparkline.length > 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-3 h-8",
                "data-testid": "sparkline-wrapper",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "w-full h-full relative overflow-hidden",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                        viewBox: `0 0 ${sparkline.length - 1} 100`,
                        className: "w-full h-full",
                        preserveAspectRatio: "none",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("polyline", {
                            fill: "none",
                            stroke: "var(--accent-400)",
                            strokeWidth: "2",
                            points: sparkline.map((val, i)=>`${i},${100 - val}`).join(" ")
                        }, void 0, false, {
                            fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                            lineNumber: 94,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                        lineNumber: 89,
                        columnNumber: 13
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                    lineNumber: 88,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                lineNumber: 86,
                columnNumber: 9
            }, this),
            progress !== undefined && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-3 h-2 bg-line-1 rounded-full overflow-hidden",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "h-full bg-accent-500 transition-all duration-500 rounded-full",
                    style: {
                        width: `${Math.min(100, Math.max(0, progress))}%`
                    }
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                    lineNumber: 109,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
                lineNumber: 108,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx",
        lineNumber: 52,
        columnNumber: 5
    }, this);
}
}),
"[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "EventStream",
    ()=>EventStream
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/badge.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/lib/utils.ts [app-ssr] (ecmascript)");
"use client";
;
;
;
;
;
function EventStream({ events, maxHeight = 400, showFilters = true, onPause, onResume, onExport, className }) {
    const [filter, setFilter] = __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"]("all");
    const [isPaused, setIsPaused] = __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"](false);
    const [searchQuery, setSearchQuery] = __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"]("");
    const filteredEvents = events.filter((event)=>{
        const matchesFilter = filter === "all" || event.type === filter;
        const matchesSearch = !searchQuery || event.type.toLowerCase().includes(searchQuery.toLowerCase()) || event.source.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });
    const eventTypes = Array.from(new Set(events.map((e)=>e.type)));
    const getSeverityColor = (type)=>{
        if (type.includes("error") || type.includes("failed")) return "error";
        if (type.includes("warning") || type.includes("pending")) return "warning";
        if (type.includes("success") || type.includes("completed")) return "success";
        return "info";
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"], {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$lib$2f$utils$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["cn"])("p-6", className),
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                className: "text-lg font-semibold",
                                children: "Event Stream"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 54,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-sm text-muted-foreground",
                                children: [
                                    filteredEvents.length,
                                    " events ",
                                    isPaused && "(paused)"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 55,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                        lineNumber: 53,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>{
                                    const nextPaused = !isPaused;
                                    setIsPaused(nextPaused);
                                    if (nextPaused && onResume) onResume();
                                    if (!nextPaused && onPause) onPause();
                                },
                                className: "rounded-md border px-3 py-1.5 text-sm hover:bg-accent/10 transition-colors",
                                children: isPaused ? "▶ Resume" : "⏸ Pause"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 60,
                                columnNumber: 11
                            }, this),
                            onExport && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: onExport,
                                className: "rounded-md border px-3 py-1.5 text-sm hover:bg-accent/10 transition-colors",
                                children: "📥 Export"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 72,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                        lineNumber: 59,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                lineNumber: 52,
                columnNumber: 7
            }, this),
            showFilters && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-2 mb-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        type: "text",
                        placeholder: "Search events...",
                        value: searchQuery,
                        onChange: (e)=>setSearchQuery(e.target.value),
                        className: "flex-1 rounded-md border bg-background px-3 py-1.5 text-sm"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                        lineNumber: 85,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                        value: filter,
                        onChange: (e)=>setFilter(e.target.value),
                        className: "rounded-md border bg-background px-3 py-1.5 text-sm",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                value: "all",
                                children: "All Types"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 97,
                                columnNumber: 13
                            }, this),
                            eventTypes.map((type)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                    value: type,
                                    children: type
                                }, type, false, {
                                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                    lineNumber: 99,
                                    columnNumber: 15
                                }, this))
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                        lineNumber: 92,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                lineNumber: 84,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-2 overflow-y-auto",
                style: {
                    maxHeight: `${maxHeight}px`
                },
                children: filteredEvents.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-sm text-muted-foreground py-8",
                    children: "No events to display"
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                    lineNumber: 113,
                    columnNumber: 11
                }, this) : filteredEvents.map((event)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-start gap-3 p-3 rounded-lg border hover:bg-accent/5 transition-colors",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "h-2 w-2 rounded-full mt-1.5 flex-shrink-0",
                                style: {
                                    backgroundColor: event.type.includes("error") ? "#ef4444" : event.type.includes("warning") ? "#f59e0b" : event.type.includes("success") ? "#10b981" : "#3b82f6"
                                }
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 123,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex-1 min-w-0",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-2 mb-1",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-mono text-xs text-muted-foreground",
                                                children: new Date(event.timestamp).toLocaleTimeString()
                                            }, void 0, false, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                                lineNumber: 132,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                                                variant: getSeverityColor(event.type),
                                                className: "text-xs",
                                                children: event.type
                                            }, void 0, false, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                                lineNumber: 135,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                        lineNumber: 131,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-sm",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "font-medium",
                                            children: [
                                                "from ",
                                                event.source
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                            lineNumber: 140,
                                            columnNumber: 19
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                        lineNumber: 139,
                                        columnNumber: 17
                                    }, this),
                                    event.payload && Object.keys(event.payload).length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("details", {
                                        className: "mt-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("summary", {
                                                className: "text-xs text-muted-foreground cursor-pointer hover:text-foreground",
                                                children: "View payload"
                                            }, void 0, false, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                                lineNumber: 144,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("pre", {
                                                className: "mt-2 text-xs bg-muted p-2 rounded overflow-x-auto",
                                                children: JSON.stringify(event.payload, null, 2)
                                            }, void 0, false, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                                lineNumber: 147,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                        lineNumber: 143,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                                lineNumber: 130,
                                columnNumber: 15
                            }, this)
                        ]
                    }, event.id, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                        lineNumber: 118,
                        columnNumber: 13
                    }, this))
            }, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
                lineNumber: 108,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx",
        lineNumber: 50,
        columnNumber: 5
    }, this);
}
}),
"[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "agentsService",
    ()=>agentsService,
    "apiClient",
    ()=>apiClient,
    "authService",
    ()=>authService,
    "fluxService",
    ()=>fluxService,
    "goalsService",
    ()=>goalsService,
    "memoryService",
    ()=>memoryService,
    "settingsService",
    ()=>settingsService,
    "skillsService",
    ()=>skillsService
]);
/**
 * Centralized API client with interceptors
 */ const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
class ApiClient {
    baseURL;
    token = null;
    constructor(baseURL){
        this.baseURL = baseURL;
        this.loadToken();
    }
    loadToken() {
        if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
        ;
    }
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            "Content-Type": "application/json",
            ...options.headers
        };
        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }
        const config = {
            ...options,
            headers
        };
        try {
            const response = await fetch(url, config);
            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.token = null;
                if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
                ;
                throw new Error("Unauthorized");
            }
            if (!response.ok) {
                const error = await response.json().catch(()=>({
                        message: `HTTP ${response.status}: ${response.statusText}`
                    }));
                throw new Error(error.message || error.error || "Request failed");
            }
            // Handle 204 No Content
            if (response.status === 204) {
                return {};
            }
            return await response.json();
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error("Unknown error occurred");
        }
    }
    // Auth endpoints
    async login(email, password) {
        return this.request("/api/v1/auth/login", {
            method: "POST",
            body: JSON.stringify({
                email,
                password
            })
        });
    }
    async logout() {
        return this.request("/api/v1/auth/logout", {
            method: "POST"
        });
    }
    async refreshToken() {
        return this.request("/api/v1/auth/refresh", {
            method: "POST"
        });
    }
    async getCurrentUser() {
        return this.request("/api/v1/auth/me");
    }
    // Agents endpoints
    async getAgents() {
        return this.request("/api/v1/agents");
    }
    async getAgent(id) {
        return this.request(`/api/v1/agents/${id}`);
    }
    async createAgent(data) {
        return this.request("/api/v1/agents", {
            method: "POST",
            body: JSON.stringify(data)
        });
    }
    async updateAgent(id, data) {
        return this.request(`/api/v1/agents/${id}`, {
            method: "PUT",
            body: JSON.stringify(data)
        });
    }
    async deleteAgent(id) {
        return this.request(`/api/v1/agents/${id}`, {
            method: "DELETE"
        });
    }
    // Goals endpoints
    async getGoals() {
        return this.request("/api/v1/goals");
    }
    async getGoal(id) {
        return this.request(`/api/v1/goals/${id}`);
    }
    async createGoal(data) {
        return this.request("/api/v1/goals", {
            method: "POST",
            body: JSON.stringify(data)
        });
    }
    async updateGoal(id, data) {
        return this.request(`/api/v1/goals/${id}`, {
            method: "PUT",
            body: JSON.stringify(data)
        });
    }
    async deleteGoal(id) {
        return this.request(`/api/v1/goals/${id}`, {
            method: "DELETE"
        });
    }
    // Memory endpoints
    async searchMemory(query, filters) {
        const params = new URLSearchParams({
            query,
            ...filters
        });
        return this.request(`/api/v1/memory/search?${params}`);
    }
    async storeMemory(entry) {
        return this.request("/api/v1/memory/store", {
            method: "POST",
            body: JSON.stringify(entry)
        });
    }
    async getMemoryEntry(id) {
        return this.request(`/api/v1/memory/${id}`);
    }
    // Skills endpoints
    async getSkills() {
        return this.request("/api/v1/skills");
    }
    async getSkill(id) {
        return this.request(`/api/v1/skills/${id}`);
    }
    async executeSkill(id, params) {
        return this.request(`/api/v1/skills/${id}/execute`, {
            method: "POST",
            body: JSON.stringify(params)
        });
    }
    // Flux endpoints
    async getFluxEvents(filters) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/v1/flux?${params}`);
    }
    // Settings endpoints
    async getSettings() {
        return this.request("/api/v1/settings");
    }
    async updateSettings(data) {
        return this.request("/api/v1/settings", {
            method: "PUT",
            body: JSON.stringify(data)
        });
    }
}
const apiClient = new ApiClient(API_BASE_URL);
const authService = {
    login: (email, password)=>apiClient.login(email, password),
    logout: ()=>apiClient.logout(),
    refreshToken: ()=>apiClient.refreshToken(),
    getCurrentUser: ()=>apiClient.getCurrentUser()
};
const agentsService = {
    getAll: ()=>apiClient.getAgents(),
    getById: (id)=>apiClient.getAgent(id),
    create: (data)=>apiClient.createAgent(data),
    update: (id, data)=>apiClient.updateAgent(id, data),
    delete: (id)=>apiClient.deleteAgent(id)
};
const goalsService = {
    getAll: ()=>apiClient.getGoals(),
    getById: (id)=>apiClient.getGoal(id),
    create: (data)=>apiClient.createGoal(data),
    update: (id, data)=>apiClient.updateGoal(id, data),
    delete: (id)=>apiClient.deleteGoal(id)
};
const memoryService = {
    search: (query, filters)=>apiClient.searchMemory(query, filters),
    store: (entry)=>apiClient.storeMemory(entry),
    getById: (id)=>apiClient.getMemoryEntry(id)
};
const skillsService = {
    getAll: ()=>apiClient.getSkills(),
    getById: (id)=>apiClient.getSkill(id),
    execute: (id, params)=>apiClient.executeSkill(id, params)
};
const fluxService = {
    getEvents: (filters)=>apiClient.getFluxEvents(filters)
};
const settingsService = {
    get: ()=>apiClient.getSettings(),
    update: (data)=>apiClient.updateSettings(data)
};
}),
"[project]/AI/Ethan/interfaces/webui/src/features/agents/hooks/use-agents.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useAgent",
    ()=>useAgent,
    "useAgents",
    ()=>useAgents,
    "useCreateAgent",
    ()=>useCreateAgent,
    "useDeleteAgent",
    ()=>useDeleteAgent,
    "useUpdateAgent",
    ()=>useUpdateAgent
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useQuery.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useMutation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)");
"use client";
;
;
function useAgents() {
    const { data: agents = [], isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "agents"
        ],
        queryFn: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["agentsService"].getAll()
    });
    return {
        agents,
        isLoading,
        error: error instanceof Error ? error.message : null,
        refetch,
        clearError: ()=>{}
    };
}
function useAgent(id) {
    const { data: agent = null, isLoading, error } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "agents",
            id
        ],
        queryFn: ()=>id ? __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["agentsService"].getById(id) : null,
        enabled: !!id
    });
    return {
        agent,
        isLoading,
        error: error instanceof Error ? error.message : null,
        clearError: ()=>{}
    };
}
function useCreateAgent() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (data)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["agentsService"].create(data),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "agents"
                ]
            });
        }
    });
    return {
        mutate: async (data)=>{
            try {
                const result = await mutation.mutateAsync(data);
                return {
                    data: result,
                    error: null
                };
            } catch (error) {
                return {
                    data: null,
                    error: error instanceof Error ? error.message : "Failed to create agent"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
function useUpdateAgent() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: ({ id, data })=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["agentsService"].update(id, data),
        onSuccess: (_, variables)=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "agents"
                ]
            });
            queryClient.invalidateQueries({
                queryKey: [
                    "agents",
                    variables.id
                ]
            });
        }
    });
    return {
        mutate: async (id, data)=>{
            try {
                const result = await mutation.mutateAsync({
                    id,
                    data
                });
                return {
                    data: result,
                    error: null
                };
            } catch (error) {
                return {
                    data: null,
                    error: error instanceof Error ? error.message : "Failed to update agent"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
function useDeleteAgent() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["agentsService"].delete(id),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "agents"
                ]
            });
        }
    });
    return {
        mutate: async (id)=>{
            try {
                await mutation.mutateAsync(id);
                return {
                    error: null
                };
            } catch (error) {
                return {
                    error: error instanceof Error ? error.message : "Failed to delete agent"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/features/goals/hooks/use-goals.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useCreateGoal",
    ()=>useCreateGoal,
    "useDeleteGoal",
    ()=>useDeleteGoal,
    "useGoal",
    ()=>useGoal,
    "useGoals",
    ()=>useGoals,
    "useUpdateGoal",
    ()=>useUpdateGoal
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useQuery.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useMutation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)");
"use client";
;
;
function useGoals() {
    const { data: goals = [], isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "goals"
        ],
        queryFn: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["goalsService"].getAll()
    });
    return {
        goals,
        isLoading,
        error: error instanceof Error ? error.message : null,
        refetch,
        clearError: ()=>{}
    };
}
function useGoal(id) {
    const { data: goal = null, isLoading, error } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "goals",
            id
        ],
        queryFn: ()=>id ? __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["goalsService"].getById(id) : null,
        enabled: !!id
    });
    return {
        goal,
        isLoading,
        error: error instanceof Error ? error.message : null,
        clearError: ()=>{}
    };
}
function useCreateGoal() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (data)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["goalsService"].create(data),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "goals"
                ]
            });
        }
    });
    return {
        mutate: async (data)=>{
            try {
                const result = await mutation.mutateAsync(data);
                return {
                    data: result,
                    error: null
                };
            } catch (error) {
                return {
                    data: null,
                    error: error instanceof Error ? error.message : "Failed to create goal"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
function useUpdateGoal() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: ({ id, data })=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["goalsService"].update(id, data),
        onSuccess: (_, variables)=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "goals"
                ]
            });
            queryClient.invalidateQueries({
                queryKey: [
                    "goals",
                    variables.id
                ]
            });
        }
    });
    return {
        mutate: async (id, data)=>{
            try {
                const result = await mutation.mutateAsync({
                    id,
                    data
                });
                return {
                    data: result,
                    error: null
                };
            } catch (error) {
                return {
                    data: null,
                    error: error instanceof Error ? error.message : "Failed to update goal"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
function useDeleteGoal() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["goalsService"].delete(id),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "goals"
                ]
            });
        }
    });
    return {
        mutate: async (id)=>{
            try {
                await mutation.mutateAsync(id);
                return {
                    error: null
                };
            } catch (error) {
                return {
                    error: error instanceof Error ? error.message : "Failed to delete goal"
                };
            }
        },
        isLoading: mutation.isPending,
        error: mutation.error instanceof Error ? mutation.error.message : null,
        clearError: mutation.reset
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/features/memory/services/memory.service.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "memoryService",
    ()=>memoryService
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)");
;
const memoryService = {
    getAll: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request("/api/v1/memory/events"),
    getFacts: (filters)=>{
        const params = filters ? new URLSearchParams(filters).toString() : "";
        return __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/memory/facts?${params}`);
    },
    search: (query, filters)=>{
        const params = new URLSearchParams({
            query,
            ...filters
        }).toString();
        return __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/memory/search?${params}`);
    },
    store: (entry)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request("/api/v1/memory/ingest", {
            method: "POST",
            body: JSON.stringify(entry)
        }),
    getById: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/memory/${id}`),
    getFactById: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/memory/facts/${id}`)
};
}),
"[project]/AI/Ethan/interfaces/webui/src/features/memory/hooks/use-memory.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useFacts",
    ()=>useFacts,
    "useMemoryEvents",
    ()=>useMemoryEvents,
    "useStoreMemory",
    ()=>useStoreMemory
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useQuery.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useMutation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$services$2f$memory$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/memory/services/memory.service.ts [app-ssr] (ecmascript)");
"use client";
;
;
function useFacts(filters) {
    const { data, isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "facts",
            filters
        ],
        queryFn: ()=>{
            const query = filters?.query || "";
            if (query) {
                return __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$services$2f$memory$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["memoryService"].search(query, filters);
            }
            return __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$services$2f$memory$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["memoryService"].getFacts(filters);
        }
    });
    return {
        facts: data?.data || [],
        isLoading,
        error: error instanceof Error ? error.message : null,
        fetchFacts: refetch
    };
}
function useMemoryEvents() {
    const { data, isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "memoryEvents"
        ],
        queryFn: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$services$2f$memory$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["memoryService"].getAll()
    });
    return {
        events: data?.data || [],
        isLoading,
        error: error instanceof Error ? error.message : null,
        fetchEvents: refetch
    };
}
function useStoreMemory() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (entry)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$services$2f$memory$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["memoryService"].store(entry),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "memoryEvents"
                ]
            });
            queryClient.invalidateQueries({
                queryKey: [
                    "facts"
                ]
            });
        }
    });
    return {
        mutate: async (entry)=>{
            try {
                const result = await mutation.mutateAsync(entry);
                return {
                    data: result.data,
                    error: null
                };
            } catch (err) {
                return {
                    data: null,
                    error: err instanceof Error ? err.message : "Failed to store memory"
                };
            }
        },
        isLoading: mutation.isPending
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/features/flux/services/flux.service.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "fluxService",
    ()=>fluxService
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)");
;
const fluxService = {
    getEvents: (filters)=>{
        const params = filters ? new URLSearchParams(filters).toString() : "";
        return __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/flux?${params}`);
    },
    getEventById: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/flux/${id}`)
};
}),
"[project]/AI/Ethan/interfaces/webui/src/core/websocket/use-websocket.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useWebSocket",
    ()=>useWebSocket
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
function useWebSocket({ url, onMessage, onOpen, onClose, onError, reconnectInterval = 1000, maxReconnectAttempts = 5 }) {
    const wsRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(null);
    const reconnectCountRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(0);
    const reconnectTimeoutRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(null);
    const [isConnected, setIsConnected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const connect = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])(()=>{
        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;
            ws.onopen = ()=>{
                console.log(`[WebSocket] Connected to ${url}`);
                setIsConnected(true);
                setError(null);
                reconnectCountRef.current = 0;
                onOpen?.();
            };
            ws.onmessage = (event)=>{
                try {
                    const data = JSON.parse(event.data);
                    onMessage?.(data);
                } catch (e) {
                    console.error("[WebSocket] Failed to parse message:", e);
                }
            };
            ws.onerror = (event)=>{
                console.error("[WebSocket] Error:", event);
                setError("WebSocket error occurred");
                onError?.(event);
            };
            ws.onclose = ()=>{
                console.log(`[WebSocket] Disconnected from ${url}`);
                setIsConnected(false);
                onClose?.();
                // Auto-reconnect
                if (reconnectCountRef.current < maxReconnectAttempts) {
                    reconnectCountRef.current++;
                    const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current - 1); // Exponential backoff
                    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current}/${maxReconnectAttempts})`);
                    reconnectTimeoutRef.current = setTimeout(()=>{
                        connect();
                    }, delay);
                } else {
                    setError("Max reconnection attempts reached");
                }
            };
        } catch (e) {
            console.error("[WebSocket] Failed to connect:", e);
            setError("Failed to establish WebSocket connection");
        }
    }, [
        url,
        onMessage,
        onOpen,
        onClose,
        onError,
        reconnectInterval,
        maxReconnectAttempts
    ]);
    const disconnect = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])(()=>{
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
    }, []);
    const send = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])((data)=>{
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        } else {
            console.error("[WebSocket] Cannot send message, connection not open");
        }
    }, []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        connect();
        return ()=>{
            disconnect();
        };
    }, [
        connect,
        disconnect
    ]);
    return {
        isConnected,
        error,
        send,
        disconnect,
        reconnect: connect
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/features/flux/hooks/use-flux.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useFlux",
    ()=>useFlux
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useQuery.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$flux$2f$services$2f$flux$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/flux/services/flux.service.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$websocket$2f$use$2d$websocket$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/websocket/use-websocket.ts [app-ssr] (ecmascript)");
"use client";
;
;
;
;
function useFlux() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const [wsConnected, setWsConnected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const { data, isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "fluxEvents"
        ],
        queryFn: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$flux$2f$services$2f$flux$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["fluxService"].getEvents()
    });
    const events = data?.data || [];
    // WebSocket connection for real-time events
    const handleWebSocketMessage = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])((data)=>{
        if (data.type && data.payload) {
            const newEvent = {
                id: data.payload.id || `event-${Date.now()}`,
                type: data.type,
                source: data.source || "unknown",
                payload: data.payload,
                timestamp: data.timestamp || new Date().toISOString()
            };
            // Push new event into React Query cache (max 500 items)
            queryClient.setQueryData([
                "fluxEvents"
            ], (oldData)=>{
                const oldEvents = oldData?.data || [];
                return {
                    ...oldData,
                    data: [
                        newEvent,
                        ...oldEvents
                    ].slice(0, 500)
                };
            });
        }
    }, [
        queryClient
    ]);
    const { error: wsError } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$websocket$2f$use$2d$websocket$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useWebSocket"])({
        url: ("TURBOPACK compile-time falsy", 0) ? "TURBOPACK unreachable" : "",
        onMessage: handleWebSocketMessage,
        onOpen: ()=>{
            console.log("[useFlux] WebSocket connected");
            setWsConnected(true);
        },
        onClose: ()=>{
            console.log("[useFlux] WebSocket disconnected");
            setWsConnected(false);
        },
        onError: (err)=>console.error("[useFlux] WebSocket error:", err),
        reconnectInterval: 1000,
        maxReconnectAttempts: 5
    });
    return {
        events,
        isLoading,
        error: error instanceof Error ? error.message : wsError || null,
        isConnected: wsConnected,
        refetch
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/features/missions/services/missions.service.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "missionsService",
    ()=>missionsService
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/core/api/api-client.ts [app-ssr] (ecmascript)");
;
const missionsService = {
    getAll: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request("/api/v1/missions"),
    getById: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/missions/${id}`),
    create: (data)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request("/api/v1/missions", {
            method: "POST",
            body: JSON.stringify(data)
        }),
    update: (id, data)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/missions/${id}`, {
            method: "PUT",
            body: JSON.stringify(data)
        }),
    delete: (id)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/missions/${id}`, {
            method: "DELETE"
        }),
    verifyStep: (missionId, stepId)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/missions/${missionId}/steps/${stepId}/verify`, {
            method: "POST"
        }),
    approveStep: (missionId, stepId)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$core$2f$api$2f$api$2d$client$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["apiClient"].request(`/api/v1/missions/${missionId}/steps/${stepId}/approve`, {
            method: "POST"
        })
};
}),
"[project]/AI/Ethan/interfaces/webui/src/features/missions/hooks/use-missions.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useCreateMission",
    ()=>useCreateMission,
    "useMission",
    ()=>useMission,
    "useMissions",
    ()=>useMissions,
    "useVerifyStep",
    ()=>useVerifyStep
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useQuery.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/useMutation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$services$2f$missions$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/missions/services/missions.service.ts [app-ssr] (ecmascript)");
"use client";
;
;
function useMissions() {
    const { data, isLoading, error, refetch } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "missions"
        ],
        queryFn: ()=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$services$2f$missions$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["missionsService"].getAll()
    });
    return {
        missions: data?.data || [],
        isLoading,
        error: error instanceof Error ? error.message : null,
        refetch
    };
}
function useMission(id) {
    const { data, isLoading, error } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useQuery$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQuery"])({
        queryKey: [
            "missions",
            id
        ],
        queryFn: ()=>id ? __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$services$2f$missions$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["missionsService"].getById(id) : null,
        enabled: !!id
    });
    return {
        mission: data?.data || null,
        isLoading,
        error: error instanceof Error ? error.message : null
    };
}
function useCreateMission() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: (data)=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$services$2f$missions$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["missionsService"].create(data),
        onSuccess: ()=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "missions"
                ]
            });
        }
    });
    return {
        mutate: async (data)=>{
            try {
                const result = await mutation.mutateAsync(data);
                return {
                    data: result.data,
                    error: null
                };
            } catch (err) {
                return {
                    data: null,
                    error: err instanceof Error ? err.message : "Failed to create mission"
                };
            }
        },
        isLoading: mutation.isPending
    };
}
function useVerifyStep() {
    const queryClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$QueryClientProvider$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useQueryClient"])();
    const mutation = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f40$tanstack$2f$react$2d$query$2f$build$2f$modern$2f$useMutation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMutation"])({
        mutationFn: ({ missionId, stepId })=>__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$services$2f$missions$2e$service$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["missionsService"].verifyStep(missionId, stepId),
        onSuccess: (_, variables)=>{
            queryClient.invalidateQueries({
                queryKey: [
                    "missions"
                ]
            });
            queryClient.invalidateQueries({
                queryKey: [
                    "missions",
                    variables.missionId
                ]
            });
        }
    });
    return {
        mutate: async (missionId, stepId)=>{
            try {
                const result = await mutation.mutateAsync({
                    missionId,
                    stepId
                });
                return {
                    verified: result.data.verified,
                    error: null
                };
            } catch (err) {
                return {
                    verified: false,
                    error: err instanceof Error ? err.message : "Failed to verify step"
                };
            }
        },
        isLoading: mutation.isPending
    };
}
}),
"[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/card.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/badge.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/button.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$skeleton$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/skeleton.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$progress$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/progress.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$separator$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/separator.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$spinner$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/ui/spinner.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$metric$2d$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/shared/metric-card.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$event$2d$stream$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/components/shared/event-stream.tsx [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$agents$2f$hooks$2f$use$2d$agents$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/agents/hooks/use-agents.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$goals$2f$hooks$2f$use$2d$goals$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/goals/hooks/use-goals.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$hooks$2f$use$2d$memory$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/memory/hooks/use-memory.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$flux$2f$hooks$2f$use$2d$flux$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/flux/hooks/use-flux.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$hooks$2f$use$2d$missions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/src/features/missions/hooks/use-missions.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$play$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Play$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/play.js [app-ssr] (ecmascript) <export default as Play>");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$pause$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Pause$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/pause.js [app-ssr] (ecmascript) <export default as Pause>");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$square$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Square$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/square.js [app-ssr] (ecmascript) <export default as Square>");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$plus$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Plus$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/plus.js [app-ssr] (ecmascript) <export default as Plus>");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/search.js [app-ssr] (ecmascript) <export default as Search>");
var __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$terminal$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Terminal$3e$__ = __turbopack_context__.i("[project]/AI/Ethan/interfaces/webui/node_modules/lucide-react/dist/esm/icons/terminal.js [app-ssr] (ecmascript) <export default as Terminal>");
"use client";
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
function DashboardPage() {
    const { agents, isLoading: agentsLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$agents$2f$hooks$2f$use$2d$agents$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useAgents"])();
    const { goals, isLoading: goalsLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$goals$2f$hooks$2f$use$2d$goals$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useGoals"])();
    const { facts, isLoading: factsLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$memory$2f$hooks$2f$use$2d$memory$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useFacts"])();
    const { events, isLoading: eventsLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$flux$2f$hooks$2f$use$2d$flux$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useFlux"])();
    const { missions, isLoading: missionsLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$features$2f$missions$2f$hooks$2f$use$2d$missions$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMissions"])();
    const isLoading = agentsLoading || goalsLoading || factsLoading || eventsLoading || missionsLoading;
    const activeAgents = agents?.filter((a)=>a.status === "running").length || 0;
    const activeGoals = goals?.filter((g)=>g.status === "active").length || 0;
    const totalFacts = facts?.length || 0;
    const eventsCount = events?.length || 0;
    if (isLoading) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "space-y-6",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center justify-between",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                            className: "text-3xl font-bold tracking-tight text-foreground",
                            children: "Dashboard"
                        }, void 0, false, {
                            fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                            lineNumber: 38,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$spinner$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Spinner"], {}, void 0, false, {
                            fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                            lineNumber: 39,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                    lineNumber: 37,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "grid gap-4 md:grid-cols-2 lg:grid-cols-4",
                    children: [
                        1,
                        2,
                        3,
                        4
                    ].map((i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"], {
                            variant: "outlined",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["CardContent"], {
                                className: "p-6",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$skeleton$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Skeleton"], {
                                    variant: "text",
                                    lines: 3
                                }, void 0, false, {
                                    fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                    lineNumber: 45,
                                    columnNumber: 17
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 44,
                                columnNumber: 15
                            }, this)
                        }, i, false, {
                            fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                            lineNumber: 43,
                            columnNumber: 13
                        }, this))
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                    lineNumber: 41,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"], {
                    variant: "outlined",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["CardContent"], {
                        className: "p-6",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$skeleton$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Skeleton"], {
                            variant: "rectangle",
                            className: "w-full",
                            style: {
                                height: 200
                            }
                        }, void 0, false, {
                            fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                            lineNumber: 52,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 51,
                        columnNumber: 11
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                    lineNumber: 50,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
            lineNumber: 36,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "space-y-8 animate-fade-in pb-8",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                className: "text-3xl font-bold tracking-tight text-foreground",
                                children: "Dashboard"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 63,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-muted-foreground mt-1",
                                children: "System status and active operations"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 64,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 62,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$badge$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                        children: "Live"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 68,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 61,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "grid gap-4 md:grid-cols-2 lg:grid-cols-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$metric$2d$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["MetricCard"], {
                        title: "Active Agents",
                        value: activeAgents,
                        unit: `/ ${agents?.length || 0} total`,
                        status: "normal",
                        sparkline: [
                            5,
                            8,
                            6,
                            9,
                            7,
                            10,
                            12
                        ],
                        href: "/agents"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 73,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$metric$2d$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["MetricCard"], {
                        title: "Active Goals",
                        value: activeGoals,
                        unit: `/ ${goals?.length || 0} total`,
                        status: "normal",
                        sparkline: [
                            3,
                            5,
                            4,
                            7,
                            5,
                            8,
                            8
                        ],
                        href: "/planner"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 81,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$metric$2d$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["MetricCard"], {
                        title: "Memory Facts",
                        value: totalFacts,
                        unit: "entries",
                        status: "normal",
                        sparkline: [
                            100,
                            150,
                            200,
                            180,
                            250,
                            300,
                            320
                        ],
                        href: "/memory"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 89,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$metric$2d$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["MetricCard"], {
                        title: "Events Today",
                        value: eventsCount,
                        unit: "total",
                        status: "normal",
                        sparkline: [
                            10,
                            15,
                            12,
                            18,
                            20,
                            16,
                            22
                        ],
                        href: "/logs"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 97,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 72,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"], {
                variant: "outlined",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["CardHeader"], {
                        className: "flex flex-row items-center justify-between pb-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["CardTitle"], {
                                children: "Recent Missions"
                            }, void 0, false, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 110,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                size: "sm",
                                variant: "outline",
                                className: "gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$plus$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Plus$3e$__["Plus"], {
                                        size: 14
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 112,
                                        columnNumber: 13
                                    }, this),
                                    " New Mission"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 111,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 109,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$card$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["CardContent"], {
                        className: "space-y-4",
                        children: missions?.slice(0, 5).map((mission)=>{
                            const stepsTotal = mission.steps_total || 1;
                            const stepsCompleted = mission.steps_completed || 0;
                            const progress = Math.round(stepsCompleted / stepsTotal * 100);
                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "rounded-lg border bg-card p-4 transition-all hover:bg-accent/5",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between mb-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "font-medium",
                                                children: mission.title
                                            }, void 0, false, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                lineNumber: 123,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-sm font-mono text-muted-foreground",
                                                children: [
                                                    progress,
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                lineNumber: 124,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 122,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$progress$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Progress"], {
                                        value: progress,
                                        className: "h-2 mb-3"
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 126,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between text-sm",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center gap-4 text-muted-foreground",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        children: [
                                                            "Steps: ",
                                                            stepsCompleted,
                                                            "/",
                                                            stepsTotal
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                        lineNumber: 129,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "flex items-center gap-1.5",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                className: "h-2 w-2 rounded-full bg-blue-500 animate-pulse"
                                                            }, void 0, false, {
                                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                                lineNumber: 131,
                                                                columnNumber: 23
                                                            }, this),
                                                            mission.status
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                        lineNumber: 130,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                lineNumber: 128,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "flex items-center gap-2",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                                        size: "sm",
                                                        variant: "ghost",
                                                        className: "h-8 px-2",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$pause$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Pause$3e$__["Pause"], {
                                                                size: 14,
                                                                className: "mr-1"
                                                            }, void 0, false, {
                                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                                lineNumber: 136,
                                                                columnNumber: 76
                                                            }, this),
                                                            " Pause"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                        lineNumber: 136,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                                        size: "sm",
                                                        variant: "ghost",
                                                        className: "h-8 px-2 text-destructive",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$square$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Square$3e$__["Square"], {
                                                                size: 14,
                                                                className: "mr-1"
                                                            }, void 0, false, {
                                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                                lineNumber: 137,
                                                                columnNumber: 93
                                                            }, this),
                                                            " Kill"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                        lineNumber: 137,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                                        size: "sm",
                                                        variant: "outline",
                                                        className: "h-8 px-2",
                                                        children: "View"
                                                    }, void 0, false, {
                                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                        lineNumber: 138,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                                lineNumber: 135,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 127,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, mission.id, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 121,
                                columnNumber: 15
                            }, this);
                        })
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 115,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 108,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$separator$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Separator"], {}, void 0, false, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 147,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-sm font-medium text-muted-foreground uppercase tracking-wider",
                        children: "Quick Actions"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 151,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-wrap gap-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                variant: "secondary",
                                className: "gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$plus$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Plus$3e$__["Plus"], {
                                        size: 16
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 154,
                                        columnNumber: 13
                                    }, this),
                                    " New Mission"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 153,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                variant: "secondary",
                                className: "gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$play$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Play$3e$__["Play"], {
                                        size: 16
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 157,
                                        columnNumber: 13
                                    }, this),
                                    " Start Agent"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 156,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                variant: "secondary",
                                className: "gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__["Search"], {
                                        size: 16
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 160,
                                        columnNumber: 13
                                    }, this),
                                    " Search Memory"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 159,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$ui$2f$button$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                                variant: "secondary",
                                className: "gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$terminal$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Terminal$3e$__["Terminal"], {
                                        size: 16
                                    }, void 0, false, {
                                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                        lineNumber: 163,
                                        columnNumber: 13
                                    }, this),
                                    " Open Terminal"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                                lineNumber: 162,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 152,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 150,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-sm font-medium text-muted-foreground uppercase tracking-wider",
                        children: "Event Stream"
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 170,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$AI$2f$Ethan$2f$interfaces$2f$webui$2f$src$2f$components$2f$shared$2f$event$2d$stream$2e$tsx__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["EventStream"], {
                        events: events?.slice(0, 50) || [],
                        maxHeight: 350,
                        showFilters: false,
                        onPause: ()=>{},
                        onResume: ()=>{}
                    }, void 0, false, {
                        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                        lineNumber: 171,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
                lineNumber: 169,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/AI/Ethan/interfaces/webui/src/app/(dashboard)/page.tsx",
        lineNumber: 60,
        columnNumber: 5
    }, this);
}
}),
];

//# sourceMappingURL=AI_Ethan_interfaces_webui_src_1bwo2lq._.js.map
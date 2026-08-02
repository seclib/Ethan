import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js middleware — protects dashboard routes, allows auth routes.
 *
 * JWT is stored in an HttpOnly cookie (ethan_token) set by the API route
 * handler. This middleware checks for that cookie and redirects
 * unauthenticated users to /login. Full JWT validation happens server-side
 * in the FastAPI auth middleware.
 *
 * This middleware redirects unauthenticated users to /login.
 */

const PUBLIC_ROUTES = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for auth token in cookie
  const token = request.cookies.get("ethan_token")?.value;

  // Allow public auth routes
  if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Allow API proxy routes (handled by Next.js rewrites)
  if (pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // Allow static assets
  if (
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/icons/")
  ) {
    return NextResponse.next();
  }

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
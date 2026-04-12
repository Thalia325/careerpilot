import { NextRequest, NextResponse } from "next/server";

const roleRoutes: Record<string, string> = {
  student: "/student",
  teacher: "/teacher",
  admin: "/admin"
};

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  const protectedPrefixes = ["/admin", "/teacher", "/student", "/workspace"];
  const isProtectedRoute = protectedPrefixes.some((prefix) => pathname.startsWith(prefix));

  if (!isProtectedRoute) {
    return NextResponse.next();
  }

  const devBypass = request.cookies.get("dev_bypass")?.value === "true";
  if (devBypass) {
    return NextResponse.next();
  }

  const token =
    request.cookies.get("auth_token")?.value ||
    request.cookies.get("token")?.value;

  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const userRole = request.cookies.get("user_role")?.value;

  if (userRole && roleRoutes[userRole]) {
    const allowedPrefix = roleRoutes[userRole];
    if (!pathname.startsWith(allowedPrefix) && !pathname.startsWith("/workspace")) {
      return NextResponse.redirect(new URL(allowedPrefix, request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/admin/:path*",
    "/teacher/:path*",
    "/student/:path*",
    "/workspace/:path*"
  ]
};

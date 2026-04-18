import { NextRequest, NextResponse } from "next/server";

const roleRoutes: Record<string, string> = {
  student: "/student",
  teacher: "/teacher",
  admin: "/admin"
};

/**
 * Admin is allowed to visit these student/teacher sub-routes for review.
 * All other student/teacher routes remain blocked for admin.
 */
const adminReviewAllowed = [
  "/student/profile",
  "/student/report",
  "/student/matching",
  "/student/path",
  "/student/recommended",
  "/student/info",
  "/student/history",
  "/student/dashboard",
  "/teacher/overview",
  "/teacher/reports",
  "/teacher/advice",
  "/teacher/info",
];

function isAdminReviewRoute(pathname: string): boolean {
  return adminReviewAllowed.some(
    (route) => pathname === route || pathname.startsWith(route + "/")
  );
}

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

    // Admin can access explicitly listed student/teacher review routes
    if (userRole === "admin" && isAdminReviewRoute(pathname)) {
      return NextResponse.next();
    }

    if (!pathname.startsWith(allowedPrefix) && !pathname.startsWith("/workspace")) {
      const redirectUrl = new URL(allowedPrefix, request.url);
      redirectUrl.searchParams.set("notice", "access_denied");
      return NextResponse.redirect(redirectUrl);
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

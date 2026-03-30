import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = ["/admin", "/teacher", "/student", "/workspace"];

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Check if the route is protected
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  if (isProtectedRoute) {
    // Check for token in cookies or localStorage
    const token =
      request.cookies.get("auth_token")?.value ||
      request.cookies.get("token")?.value;

    if (!token) {
      // Redirect to login if no token found
      return NextResponse.redirect(new URL("/login", request.url));
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

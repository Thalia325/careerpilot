import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "登录 - CareerPilot",
  description: "登录到 CareerPilot 职业规划系统",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

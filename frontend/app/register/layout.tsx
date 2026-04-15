import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "注册 - CareerPilot",
  description: "注册 CareerPilot 职业规划系统",
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

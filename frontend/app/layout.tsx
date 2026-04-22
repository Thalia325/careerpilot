import type { Metadata, Viewport } from "next";
import { ReactNode } from "react";
import fs from "node:fs";
import path from "node:path";

const globalStyles = fs.readFileSync(
  path.join(process.cwd(), "app", "globals.css"),
  "utf8",
);

export const metadata: Metadata = {
  title: {
    default: "CareerPilot - AI职业规划助手",
    template: "%s | CareerPilot"
  },
  description: "基于 AI 的大学生职业规划智能体，提供岗位匹配、职业路径规划、能力评估等一站式服务",
  keywords: ["职业规划", "岗位匹配", "AI", "大学生"],
  authors: [{ name: "CareerPilot Team" }],
  creator: "CareerPilot",
  publisher: "CareerPilot",
  robots: {
    index: true,
    follow: true
  }
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <head>
        <meta charSet="utf-8" />
        <style
          id="careerpilot-globals"
          dangerouslySetInnerHTML={{ __html: globalStyles }}
        />
      </head>
      <body>
        <a href="#main-content" className="skip-to-main">
          跳转至主内容
        </a>
        <main id="main-content">{children}</main>
      </body>
    </html>
  );
}

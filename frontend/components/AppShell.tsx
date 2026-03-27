import Link from "next/link";
import { ReactNode } from "react";

const navGroups = [
  {
    label: "学生端",
    links: [
      { href: "/student/dashboard", label: "学生首页" },
      { href: "/student/upload", label: "材料上传" },
      { href: "/student/profile", label: "学生画像" },
      { href: "/student/jobs", label: "岗位探索" },
      { href: "/student/matching", label: "匹配分析" },
      { href: "/student/path", label: "职业路径" },
      { href: "/student/reports", label: "报告编辑与导出" }
    ]
  },
  {
    label: "教师与管理",
    links: [
      { href: "/teacher", label: "教师工作台" },
      { href: "/admin", label: "管理后台" }
    ]
  }
];

export function AppShell({
  title,
  subtitle,
  children
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span>CareerPilot</span>
          <small>AI 职业规划智能体</small>
        </Link>
        {navGroups.map((group) => (
          <div key={group.label} className="nav-group">
            <p>{group.label}</p>
            {group.links.map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
          </div>
        ))}
      </aside>
      <main className="content">
        <header className="hero-card">
          <div>
            <p className="eyebrow">A13 赛题演示版</p>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="hero-badge">感知 · 认知 · 记忆 · 行动</div>
        </header>
        {children}
      </main>
    </div>
  );
}


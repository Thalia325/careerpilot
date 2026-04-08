"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { SidebarDrawer } from "@/components/SidebarDrawer";

const studentNavItems = [
  { href: "/student", label: "首页", icon: "🏠" },
  { href: "/student/jobs", label: "岗位探索", icon: "🔍" },
  { href: "/student/profile", label: "我的能力分析", icon: "📊" },
  { href: "/student/reports", label: "制定我的职业规划", icon: "📋", subtitle: "含岗位匹配 + 发展路径 + 行动计划" },
  { href: "/student/history", label: "历史记录", icon: "🕐" },
  { href: "/student/recommended", label: "推荐岗位", icon: "💼" },
  { href: "/student/dashboard", label: "个人概览", icon: "👤" }
];

const stages = [
  { title: "材料上传", description: "上传简历、证书等材料供系统分析。", icon: "📄", link: "/student/upload" },
  { title: "能力分析", description: "系统智能识别你的技能、证书和经历。", icon: "⭐", link: "/student/profile" },
  { title: "岗位匹配", description: "与目标岗位进行四维评分和匹配分析。", icon: "🎯", link: "/student/matching" },
  { title: "职业路径", description: "获得个性化的职业发展建议和行动计划。", icon: "🗺️", link: "/student/path" },
  { title: "报告导出", description: "编辑、优化并导出专业的职业规划报告。", icon: "📋", link: "/student/reports" }
];

export default function WorkspacePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const query = searchParams.get("query") || "产品经理";
  const resume = searchParams.get("resume") || "未上传简历";

  const handleNavigationStart = (href: string) => {
    if (isDirty) {
      const confirmed = confirm("你有未保存的内容，确定要离开吗？");
      if (!confirmed) return;
    }
    router.push(href);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  return (
    <div className="workspace-bg">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={studentNavItems}
        label="学生功能"
        footer={
          <button
            className="sidebar-drawer__link"
            onClick={handleLogout}
            style={{ background: "none", border: "none", cursor: "pointer", width: "100%", color: "var(--color-error)" }}
          >
            <span className="sidebar-drawer__link-icon">🚪</span>
            退出登录
          </button>
        }
      />
      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单">☰</button>
          <span className="workspace-topbar__title">任务工作台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">同学</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="workspace-page">
        <div className="workspace-page__container">
          <header className="workspace-hero">
            <span className="section-kicker">任务工作台</span>
            <h1>职业规划分析进行中</h1>
            <p>按照以下步骤完成职业能力分析和规划报告生成。</p>
          </header>

          <section className="workspace-grid">
            <article className="workspace-card">
              <h2>当前任务</h2>
              <ul className="workspace-summary">
                <li><span>目标岗位</span><strong>{query}</strong></li>
                <li><span>简历文件</span><strong>{resume}</strong></li>
                <li><span>当前状态</span><strong style={{ color: "var(--accent)" }}>准备开始</strong></li>
              </ul>
            </article>
            <article className="workspace-card">
              <h2>分析步骤</h2>
              <div className="workspace-stage-list">
                {stages.map((stage) => (
                  <a
                    key={stage.title}
                    href={stage.link}
                    className="workspace-stage-item workspace-stage-link"
                    onClick={(e) => { e.preventDefault(); handleNavigationStart(stage.link); }}
                  >
                    <span>{stage.icon}</span>
                    <div><strong>{stage.title}</strong><p>{stage.description}</p></div>
                  </a>
                ))}
              </div>
            </article>
          </section>

          <section className="workspace-actions">
            <Link href="/student/upload" className="btn-primary" style={{ textDecoration: "none", display: "inline-flex" }}>
              开始上传材料
            </Link>
            <Link href="/student" className="workspace-backlink">返回首页</Link>
          </section>
        </div>
      </div>
    </div>
  );
}

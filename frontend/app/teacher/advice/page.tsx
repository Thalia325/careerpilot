"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: "🏠" },
  { href: "/teacher/reports", label: "学生报告查看", icon: "📋" },
  { href: "/teacher/overview", label: "班级数据概览", icon: "📊" },
  { href: "/teacher/advice", label: "指导建议", icon: "💬" }
];

const adviceItems = [
  { id: 1, student: "陈同学", target: "产品经理", advice: "建议在 2 周内补齐数据分析与技术理解能力。" },
  { id: 2, student: "王同学", target: "UI设计师", advice: "建议增加交互设计作品集的完整度。" },
  { id: 3, student: "李同学", target: "数据分析师", advice: "建议加强大数据场景下的分析项目实践。" },
  { id: 4, student: "张同学", target: "市场营销专员", advice: "建议补充市场调研与品牌策划相关项目经历。" },
  { id: 5, student: "全班", target: "通用", advice: "建议按月复盘成长任务完成率，并同步更新职业目标。" }
];

export default function TeacherAdvicePage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

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
        navItems={teacherNavItems}
        label="教师功能"
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
          <span className="workspace-topbar__title">指导建议</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>指导建议</h1>
        <div className="history-list">
          {adviceItems.map((item) => (
            <div key={item.id} className="history-item">
              <div>
                <p className="history-item__title">{item.student} — {item.target}</p>
                <p className="history-item__desc">{item.advice}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

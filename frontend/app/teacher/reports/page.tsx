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

export default function TeacherReportsPage() {
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
          <span className="workspace-topbar__title">学生报告查看</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>学生报告查看</h1>
        <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 16px" }}>查看和管理学生的职业规划报告</p>
        <div className="history-list">
          {["陈同学 — 产品经理方向报告", "王同学 — UI设计师方向报告", "李同学 — 数据分析师方向报告"].map((item, i) => (
            <div key={i} className="history-item">
              <div>
                <p className="history-item__title">{item}</p>
                <p className="history-item__desc">已生成完整职业规划报告</p>
              </div>
              <span className="history-item__time">{"今天 14:" + (20 + i * 10)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

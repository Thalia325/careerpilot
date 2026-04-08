"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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

const historyItems = [
  { id: "1", title: "分析我的简历 — 产品经理方向", desc: "已完成能力分析和岗位匹配", time: "今天 14:20" },
  { id: "2", title: "数据分析师岗位匹配", desc: "匹配度 89.2，差距项 2 个", time: "昨天 18:40" },
  { id: "3", title: "制定我的职业规划报告", desc: "已生成可导出报告", time: "3 天前" }
];

export default function HistoryPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
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
          <span className="workspace-topbar__title">历史记录</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>历史记录</h1>
        <div className="history-list">
          {historyItems.map((item) => (
            <div key={item.id} className="history-item">
              <div>
                <p className="history-item__title">{item.title}</p>
                <p className="history-item__desc">{item.desc}</p>
              </div>
              <span className="history-item__time">{item.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import Link from "next/link";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: "🏠" },
  { href: "/admin/users", label: "用户管理", icon: "👥" },
  { href: "/admin/stats", label: "数据统计", icon: "📊" },
  { href: "/admin/jobs", label: "岗位管理", icon: "💼" },
  { href: "/admin/system", label: "系统监控", icon: "⚙️" }
];

export default function AdminSystemPage() {
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
        navItems={adminNavItems}
        label="管理功能"
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
          <span className="workspace-topbar__title">系统监控</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>系统监控</h2>
        <div className="admin-dashboard__card">
          <div style={{ padding: 20, textAlign: "center" }}>
            <p style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>系统运行状态：正常</p>
            <p style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>最后更新时间：2026-04-04 23:45:00</p>
            <p style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>API 响应时间：45ms</p>
          </div>
        </div>
      </div>
    </div>
  );
}

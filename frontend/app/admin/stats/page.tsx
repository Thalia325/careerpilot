"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: "🏠" },
  { href: "/admin/users", label: "用户管理", icon: "👥" },
  { href: "/admin/stats", label: "数据统计", icon: "📊" },
  { href: "/admin/jobs", label: "岗位管理", icon: "💼" },
  { href: "/admin/system", label: "系统监控", icon: "⚙️" }
];

const weeklyData = [
  { week: "第1周", reports: 45, matches: 38 },
  { week: "第2周", reports: 52, matches: 44 },
  { week: "第3周", reports: 61, matches: 50 },
  { week: "第4周", reports: 78, matches: 65 },
  { week: "第5周", reports: 85, matches: 72 },
  { week: "第6周", reports: 92, matches: 78 },
  { week: "第7周", reports: 105, matches: 88 },
  { week: "第8周", reports: 118, matches: 96 }
];

export default function AdminStatsPage() {
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
          <span className="workspace-topbar__title">数据统计</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>数据统计看板</h2>
        <div className="admin-dashboard__stats" style={{ marginBottom: 24 }}>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">累计报告</span>
            <div className="admin-stat-card__value">89</div>
            <span className="admin-stat-card__change">↑ 23% 较上月</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">累计匹配</span>
            <div className="admin-stat-card__value">76</div>
            <span className="admin-stat-card__change">↑ 18% 较上月</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">活跃用户</span>
            <div className="admin-stat-card__value">142</div>
            <span className="admin-stat-card__change">↑ 8% 较上月</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">岗位覆盖</span>
            <div className="admin-stat-card__value">100</div>
            <span className="admin-stat-card__change">10000 条数据</span>
          </div>
        </div>

        <div className="admin-dashboard__card">
          <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 16px" }}>周度使用趋势</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="week" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="reports" fill="#173f8a" name="报告数" radius={[4, 4, 0, 0]} />
              <Bar dataKey="matches" fill="#12b3a6" name="匹配数" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

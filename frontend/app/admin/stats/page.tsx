"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import {
  getAdminStatsOverview,
  getAdminStatsWeekly,
  type AdminStatsOverview,
  type WeeklyDataPoint,
} from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

export default function AdminStatsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [stats, setStats] = useState<AdminStatsOverview | null>(null);
  const [weeklyData, setWeeklyData] = useState<WeeklyDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, weeklyRes] = await Promise.all([
          getAdminStatsOverview(),
          getAdminStatsWeekly(8),
        ]);
        setStats(statsRes);
        setWeeklyData(weeklyRes);
      } catch (e) {
        console.error("Failed to load stats:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

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
            <span className="sidebar-drawer__link-icon"><Icon name="logout" size={18} /></span>
            退出登录
          </button>
        }
      />
      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单"><Icon name="menu" size={20} /></button>
          <span className="workspace-topbar__title">数据统计</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>数据统计看板</h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <>
            <div className="admin-dashboard__stats" style={{ marginBottom: 24 }}>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">累计报告</span>
                <div className="admin-stat-card__value">{stats?.total_reports ?? 0}</div>
                <span className="admin-stat-card__change">全部报告</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">累计匹配</span>
                <div className="admin-stat-card__value">{stats?.avg_match_score ?? 0}</div>
                <span className="admin-stat-card__change">平均匹配度</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">注册用户</span>
                <div className="admin-stat-card__value">{stats?.total_users ?? 0}</div>
                <span className="admin-stat-card__change">全部角色</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">岗位数据</span>
                <div className="admin-stat-card__value">{stats?.total_jobs ?? 0}</div>
                <span className="admin-stat-card__change">已入库岗位</span>
              </div>
            </div>

            <div className="admin-dashboard__card">
              <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 16px" }}>周度使用趋势</h2>
              {weeklyData.length > 0 ? (
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
              ) : (
                <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>暂无周度数据</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

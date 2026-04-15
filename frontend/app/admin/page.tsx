"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import {
  getAdminUsers,
  getAdminStatsOverview,
  getAdminStatsTrends,
  type AdminUser,
  type AdminStatsOverview,
  type TrendDataPoint,
} from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

const roleLabels: Record<string, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员"
};

export default function AdminPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [stats, setStats] = useState<AdminStatsOverview | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const [usersRes, statsRes, trendsRes] = await Promise.all([
          getAdminUsers(),
          getAdminStatsOverview(),
          getAdminStatsTrends(14),
        ]);
        setUsers(usersRes.items);
        setStats(statsRes);
        setTrendData(trendsRes);
      } catch (e) {
        console.error("Failed to load admin data:", e);
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

  const formatDate = (iso: string | null) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("zh-CN");
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
          <span className="workspace-topbar__title">管理后台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">管理员</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="admin-dashboard">
        {loading ? (
          <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <>
            <div className="admin-dashboard__stats">
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
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">生成报告</span>
                <div className="admin-stat-card__value">{stats?.total_reports ?? 0}</div>
                <span className="admin-stat-card__change">累计生成</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">平均匹配度</span>
                <div className="admin-stat-card__value">{stats?.avg_match_score ?? 0}</div>
                <span className="admin-stat-card__change">所有匹配结果</span>
              </div>
            </div>

            <div className="admin-dashboard__grid">
              <div className="admin-dashboard__card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 16 }}>
                  <h2 style={{ margin: 0 }}>用户管理</h2>
                  <button type="button" className="admin-action-button" onClick={() => router.push("/admin/users")}>
                    进入增删改查
                  </button>
                </div>
                <table className="admin-user-table">
                  <thead>
                    <tr>
                      <th>用户名</th>
                      <th>角色</th>
                      <th>邮箱</th>
                      <th>注册时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td><strong>{u.full_name || u.username}</strong></td>
                        <td><span className={`role-badge role-badge--${u.role}`}>{roleLabels[u.role] || u.role}</span></td>
                        <td>{u.email || "-"}</td>
                        <td>{formatDate(u.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="admin-dashboard__card">
                <h2>使用趋势</h2>
                {trendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={trendData}>
                      <defs>
                        <linearGradient id="colorReports" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#173f8a" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#173f8a" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="reports" stroke="#173f8a" fill="url(#colorReports)" strokeWidth={2} />
                      <Line type="monotone" dataKey="users" stroke="#12b3a6" strokeWidth={2} dot={{ r: 3 }} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>暂无趋势数据</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

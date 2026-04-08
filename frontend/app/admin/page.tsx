"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: "🏠" },
  { href: "/admin/users", label: "用户管理", icon: "👥" },
  { href: "/admin/stats", label: "数据统计", icon: "📊" },
  { href: "/admin/jobs", label: "岗位管理", icon: "💼" },
  { href: "/admin/system", label: "系统监控", icon: "⚙️" }
];

const users = [
  { id: 1, name: "陈同学", role: "student", status: "活跃", lastLogin: "2026-04-04" },
  { id: 2, name: "王同学", role: "student", status: "活跃", lastLogin: "2026-04-03" },
  { id: 3, name: "李老师", role: "teacher", status: "活跃", lastLogin: "2026-04-04" },
  { id: 4, name: "张同学", role: "student", status: "活跃", lastLogin: "2026-04-02" },
  { id: 5, name: "赵同学", role: "student", status: "活跃", lastLogin: "2026-04-01" },
  { id: 6, name: "管理员", role: "admin", status: "活跃", lastLogin: "2026-04-04" }
];

const trendData = [
  { date: "03-28", reports: 12, users: 5 },
  { date: "03-29", reports: 18, users: 8 },
  { date: "03-30", reports: 15, users: 6 },
  { date: "03-31", reports: 22, users: 10 },
  { date: "04-01", reports: 28, users: 12 },
  { date: "04-02", reports: 25, users: 9 },
  { date: "04-03", reports: 30, users: 14 },
  { date: "04-04", reports: 35, users: 16 }
];

const roleLabels: Record<string, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员"
};

export default function AdminPage() {
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
          <span className="workspace-topbar__title">管理后台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">管理员</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="admin-dashboard">
        <div className="admin-dashboard__stats">
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">注册用户</span>
            <div className="admin-stat-card__value">156</div>
            <span className="admin-stat-card__change">↑ 12% 较上月</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">岗位数据</span>
            <div className="admin-stat-card__value">10,000</div>
            <span className="admin-stat-card__change">100 个岗位类型</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">生成报告</span>
            <div className="admin-stat-card__value">89</div>
            <span className="admin-stat-card__change">↑ 23% 较上月</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-card__label">平均匹配度</span>
            <div className="admin-stat-card__value">82.4</div>
            <span className="admin-stat-card__change">↑ 3.2 较上月</span>
          </div>
        </div>

        <div className="admin-dashboard__grid">
          <div className="admin-dashboard__card">
            <h2>用户管理</h2>
            <table className="admin-user-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>最后登录</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td><strong>{u.name}</strong></td>
                    <td><span className={`role-badge role-badge--${u.role}`}>{roleLabels[u.role]}</span></td>
                    <td><span className="status-dot">{u.status}</span></td>
                    <td>{u.lastLogin}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="admin-dashboard__card">
            <h2>使用趋势</h2>
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
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: "🏠" },
  { href: "/admin/users", label: "用户管理", icon: "👥" },
  { href: "/admin/stats", label: "数据统计", icon: "📊" },
  { href: "/admin/jobs", label: "岗位管理", icon: "💼" },
  { href: "/admin/system", label: "系统监控", icon: "⚙️" }
];

const users = [
  { id: 1, name: "陈同学", role: "student" as const, lastLogin: "2026-04-04" },
  { id: 2, name: "王同学", role: "student" as const, lastLogin: "2026-04-03" },
  { id: 3, name: "李老师", role: "teacher" as const, lastLogin: "2026-04-04" },
  { id: 4, name: "张同学", role: "student" as const, lastLogin: "2026-04-02" },
  { id: 5, name: "赵同学", role: "student" as const, lastLogin: "2026-04-01" },
  { id: 6, name: "管理员", role: "admin" as const, lastLogin: "2026-04-04" }
];

const roleLabels: Record<string, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员"
};

export default function AdminUsersPage() {
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
          <span className="workspace-topbar__title">用户管理</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>用户管理</h2>
        <div className="admin-dashboard__card">
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
                  <td><span className="status-dot">活跃</span></td>
                  <td>{u.lastLogin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

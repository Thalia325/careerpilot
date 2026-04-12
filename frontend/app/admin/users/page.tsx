"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getAdminUsers, type AdminUser } from "@/lib/api";

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

export default function AdminUsersPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getAdminUsers()
      .then((res) => setUsers(res.items))
      .catch((e) => console.error("Failed to load users:", e))
      .finally(() => setLoading(false));
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
          <span className="workspace-topbar__title">用户管理</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>用户管理</h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="admin-dashboard__card">
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
        )}
      </div>
    </div>
  );
}

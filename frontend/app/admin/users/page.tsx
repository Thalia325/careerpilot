"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import {
  createAdminUser,
  deleteAdminUser,
  getAdminUser,
  getAdminUsers,
  updateAdminUser,
  type AdminUser,
  type AdminUserInput,
} from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

const roleLabels: Record<AdminUserInput["role"], string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员",
};

const emptyForm: AdminUserInput = {
  username: "",
  password: "",
  full_name: "",
  role: "student",
  email: "",
};

export default function AdminUsersPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<AdminUserInput>(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getAdminUsers();
      setUsers(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载用户失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

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

  const resetForm = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setMessage("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      if (editingId) {
        const payload: Partial<AdminUserInput> = { ...form };
        if (!payload.password) delete payload.password;
        const updated = await updateAdminUser(editingId, payload);
        setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
        setMessage("用户已更新");
      } else {
        if (!form.password) {
          throw new Error("新增用户必须填写初始密码");
        }
        const created = await createAdminUser({ ...form, password: form.password });
        setUsers((prev) => [created, ...prev]);
        setMessage("用户已新增");
      }
      resetForm();
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleView = async (userId: number) => {
    setError("");
    setMessage("");
    try {
      const user = await getAdminUser(userId);
      setMessage(`用户详情：${user.full_name || user.username} / ${roleLabels[user.role as AdminUserInput["role"]] || user.role} / ${user.email || "无邮箱"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查看失败");
    }
  };

  const handleEdit = (user: AdminUser) => {
    setEditingId(user.id);
    setForm({
      username: user.username,
      password: "",
      full_name: user.full_name,
      role: user.role as AdminUserInput["role"],
      email: user.email || "",
    });
    setError("");
    setMessage("正在编辑用户，密码留空则不修改");
  };

  const handleDelete = async (user: AdminUser) => {
    if (!window.confirm(`确定删除用户“${user.full_name || user.username}”吗？存在关联数据的用户将被后端拒绝删除。`)) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await deleteAdminUser(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
      if (editingId === user.id) resetForm();
      setMessage("用户已删除");
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setSaving(false);
    }
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

      <div style={{ maxWidth: 1120, margin: "0 auto", padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 4px" }}>用户管理</h2>
            <p style={{ margin: 0, color: "var(--subtle)", fontSize: "0.875rem" }}>新增、查看、编辑、删除学生、教师和管理员账号。</p>
          </div>
          <button type="button" className="admin-action-button" onClick={loadUsers} disabled={loading || saving}>
            刷新
          </button>
        </div>

        {(message || error) && (
          <div style={{
            marginBottom: 12,
            padding: "10px 14px",
            borderRadius: 8,
            background: error ? "rgba(220, 38, 38, 0.1)" : "rgba(12, 179, 166, 0.12)",
            color: error ? "#dc2626" : "#0b7b72",
            fontSize: "0.875rem",
          }}>
            {error || message}
          </div>
        )}

        <div className="admin-dashboard__card" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 14px" }}>{editingId ? "编辑用户" : "新增用户"}</h3>
          <form onSubmit={handleSubmit} className="admin-user-form">
            <label>
              <span>用户名</span>
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </label>
            <label>
              <span>姓名</span>
              <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
            </label>
            <label>
              <span>角色</span>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as AdminUserInput["role"] })}>
                {Object.entries(roleLabels).map(([role, label]) => (
                  <option key={role} value={role}>{label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>邮箱</span>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </label>
            <label>
              <span>{editingId ? "新密码（可留空）" : "初始密码"}</span>
              <input type="password" value={form.password || ""} onChange={(e) => setForm({ ...form, password: e.target.value })} required={!editingId} />
            </label>
            <div className="admin-user-form__actions">
              <button type="submit" className="admin-action-button admin-action-button--primary" disabled={saving}>
                {saving ? "保存中..." : editingId ? "保存修改" : "新增用户"}
              </button>
              {editingId && (
                <button type="button" className="admin-action-button" onClick={resetForm} disabled={saving}>
                  取消编辑
                </button>
              )}
            </div>
          </form>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="admin-dashboard__card">
            <div style={{ overflowX: "auto" }}>
              <table className="admin-user-table">
                <thead>
                  <tr>
                    <th>用户名</th>
                    <th>登录名</th>
                    <th>角色</th>
                    <th>邮箱</th>
                    <th>注册时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td><strong>{u.full_name || u.username}</strong></td>
                      <td>{u.username}</td>
                      <td><span className={`role-badge role-badge--${u.role}`}>{roleLabels[u.role as AdminUserInput["role"]] || u.role}</span></td>
                      <td>{u.email || "-"}</td>
                      <td>{formatDate(u.created_at)}</td>
                      <td>
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                          <button type="button" className="admin-table-button" onClick={() => handleView(u.id)} disabled={saving}>查看</button>
                          <button type="button" className="admin-table-button" onClick={() => handleEdit(u)} disabled={saving}>编辑</button>
                          <button type="button" className="admin-table-button admin-table-button--danger" onClick={() => handleDelete(u)} disabled={saving}>删除</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

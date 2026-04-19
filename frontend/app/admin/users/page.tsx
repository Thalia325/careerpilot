"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { formatTime } from "@/lib/format";
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

const PAGE_SIZE = 20;

export default function AdminUsersPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<AdminUserInput>(emptyForm);
  const [editUser, setEditUser] = useState<AdminUser | null>(null);
  const [editForm, setEditForm] = useState<AdminUserInput>(emptyForm);
  const [deleteUser, setDeleteUser] = useState<AdminUser | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [keyword, setKeyword] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [page, setPage] = useState(0);
  const [detailUser, setDetailUser] = useState<AdminUser | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showPw, setShowPw] = useState({ create: false, edit: false });
  const [detailError, setDetailError] = useState("");
  const router = useRouter();

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getAdminUsers({
        keyword: keyword || undefined,
        role: roleFilter || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setUsers(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载用户失败");
    } finally {
      setLoading(false);
    }
  }, [keyword, roleFilter, page]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const formatDate = formatTime;

  const resetForm = () => {
    setForm(emptyForm);
    setError("");
    setMessage("");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      if (!form.password) {
        throw new Error("新增用户必须填写初始密码");
      }
      await createAdminUser({ ...form, password: form.password });
      setMessage("用户已新增");
      resetForm();
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload: Partial<AdminUserInput> = { ...editForm };
      if (!payload.password) delete payload.password;
      await updateAdminUser(editUser.id, payload);
      setMessage("用户已更新");
      setEditUser(null);
      setEditForm(emptyForm);
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleView = async (userId: number) => {
    setDetailError("");
    setDetailLoading(true);
    setDetailUser(null);
    setEditUser(null);
    setDeleteUser(null);
    try {
      const user = await getAdminUser(userId);
      setDetailUser(user);
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : "查看失败");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleEdit = (user: AdminUser) => {
    setEditUser(user);
    setEditForm({
      username: user.username,
      password: "",
      full_name: user.full_name,
      role: user.role as AdminUserInput["role"],
      email: user.email || "",
    });
    setError("");
    setMessage("");
    setDetailUser(null);
    setDeleteUser(null);
  };

  const handleDelete = (user: AdminUser) => {
    setDeleteUser(user);
    setDetailUser(null);
    setEditUser(null);
    setError("");
    setMessage("");
  };

  const confirmDelete = async () => {
    if (!deleteUser) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await deleteAdminUser(deleteUser.id);
      setUsers((prev) => prev.filter((u) => u.id !== deleteUser.id));
      setTotal((prev) => prev - 1);
      setDeleteUser(null);
      setDetailUser(null);
      setMessage("用户已删除");
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setSaving(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const modalBackdropStyle = {
    position: "fixed",
    inset: 0,
    zIndex: 50,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    background: "rgba(15, 23, 42, 0.35)",
  } as const;
  const modalPanelStyle = {
    width: "min(720px, 100%)",
    maxHeight: "calc(100vh - 64px)",
    overflowY: "auto",
    borderRadius: 8,
    background: "#fff",
    boxShadow: "0 24px 60px rgba(15, 23, 42, 0.22)",
  } as const;
  const modalHeaderStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: "20px 24px 12px",
    borderBottom: "1px solid var(--border, #e0e0e0)",
  } as const;
  const modalBodyStyle = {
    padding: 24,
  } as const;
  const detailLabelStyle = {
    display: "block",
    fontSize: "0.75rem",
    color: "var(--subtle)",
    marginBottom: 2,
  } as const;
  const closeButtonStyle = {
    width: 32,
    height: 32,
    borderRadius: 8,
    border: "1px solid var(--border, #e0e0e0)",
    background: "#fff",
    cursor: "pointer",
    fontSize: "1.1rem",
    lineHeight: 1,
    color: "var(--subtle)",
  } as const;

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

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 4px" }}>用户管理</h2>
            <p style={{ margin: 0, color: "var(--subtle)", fontSize: "0.875rem" }}>
              新增、查看、编辑、删除学生、教师和管理员账号。共 {total} 位用户。
            </p>
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

        {/* 搜索栏 */}
        <div className="admin-dashboard__card" style={{ marginBottom: 16 }}>
          <form onSubmit={handleSearch} style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <input
              type="text"
              placeholder="搜索用户名、姓名或邮箱..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{
                flex: "1 1 240px",
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid var(--border, #e0e0e0)",
                fontSize: "0.875rem",
                outline: "none",
              }}
            />
            <select
              value={roleFilter}
              onChange={(e) => { setRoleFilter(e.target.value); setPage(0); }}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid var(--border, #e0e0e0)",
                fontSize: "0.875rem",
                outline: "none",
                minWidth: 100,
              }}
            >
              <option value="">全部角色</option>
              {Object.entries(roleLabels).map(([role, label]) => (
                <option key={role} value={role}>{label}</option>
              ))}
            </select>
            <button type="submit" className="admin-action-button admin-action-button--primary" disabled={loading}>
              搜索
            </button>
            {(keyword || roleFilter) && (
              <button
                type="button"
                className="admin-action-button"
                onClick={() => { setKeyword(""); setRoleFilter(""); setPage(0); }}
                disabled={loading}
              >
                清除筛选
              </button>
            )}
          </form>
        </div>

        {/* 新增用户表单 */}
        <div className="admin-dashboard__card" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 14px" }}>新增用户</h3>
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
              <span>初始密码</span>
              <div className="password-field">
                <input type={showPw.create ? "text" : "password"} value={form.password || ""} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                <button type="button" onClick={() => setShowPw(v => ({ ...v, create: !v.create }))} className="password-toggle" tabIndex={-1} aria-label={showPw.create ? "隐藏密码" : "显示密码"}><Icon name={showPw.create ? "eye" : "eye-off"} size={18} /></button>
              </div>
            </label>
            <div className="admin-user-form__actions">
              <button type="submit" className="admin-action-button admin-action-button--primary" disabled={saving}>
                {saving ? "保存中..." : "新增用户"}
              </button>
            </div>
          </form>
        </div>

        {/* 用户列表 */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="admin-dashboard__card">
            <div style={{ overflowX: "auto" }}>
              <table className="admin-user-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>登录名</th>
                    <th>角色</th>
                    <th>邮箱</th>
                    <th>注册时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: "center", padding: 24, color: "var(--subtle)" }}>
                        {keyword || roleFilter ? "没有匹配的用户" : "暂无用户数据"}
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id}>
                        <td style={{ color: "var(--subtle)", fontSize: "0.8rem" }}>{u.id}</td>
                        <td><strong>{u.full_name || u.username}</strong></td>
                        <td>{u.username}</td>
                        <td><span className={`role-badge role-badge--${u.role}`}>{roleLabels[u.role as AdminUserInput["role"]] || u.role}</span></td>
                        <td>{u.email || "-"}</td>
                        <td style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}>{formatDate(u.created_at)}</td>
                        <td>
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            <button type="button" className="admin-table-button" onClick={() => handleView(u.id)} disabled={saving}>查看</button>
                            <button type="button" className="admin-table-button" onClick={() => handleEdit(u)} disabled={saving}>编辑</button>
                            <button type="button" className="admin-table-button admin-table-button--danger" onClick={() => handleDelete(u)} disabled={saving}>删除</button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, padding: "16px 0 4px" }}>
                <button
                  className="admin-action-button"
                  disabled={page === 0 || loading}
                  onClick={() => setPage((p) => p - 1)}
                >
                  上一页
                </button>
                <span style={{ fontSize: "0.875rem", color: "var(--subtle)" }}>
                  第 {page + 1} / {totalPages} 页
                </span>
                <button
                  className="admin-action-button"
                  disabled={page >= totalPages - 1 || loading}
                  onClick={() => setPage((p) => p + 1)}
                >
                  下一页
                </button>
              </div>
            )}
          </div>
        )}

        {detailLoading && (
          <div style={modalBackdropStyle} role="dialog" aria-modal="true" aria-label="加载用户详情">
            <div style={{ ...modalPanelStyle, width: "min(420px, 100%)" }}>
              <div style={modalBodyStyle}>
                <p style={{ margin: 0, color: "var(--subtle)", textAlign: "center" }}>加载用户详情中...</p>
              </div>
            </div>
          </div>
        )}

        {detailError && (
          <div style={modalBackdropStyle} role="dialog" aria-modal="true" aria-label="查看失败">
            <div style={{ ...modalPanelStyle, width: "min(460px, 100%)" }}>
              <div style={modalHeaderStyle}>
                <h3 style={{ fontSize: "1rem", margin: 0 }}>查看失败</h3>
                <button type="button" style={closeButtonStyle} onClick={() => setDetailError("")} aria-label="关闭">&times;</button>
              </div>
              <div style={modalBodyStyle}>
                <p style={{ margin: 0, color: "#dc2626" }}>{detailError}</p>
                <div style={{ marginTop: 18, display: "flex", justifyContent: "flex-end" }}>
                  <button type="button" className="admin-action-button" onClick={() => setDetailError("")}>
                    关闭
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {detailUser && (
          <div style={modalBackdropStyle} role="dialog" aria-modal="true" aria-label="用户详情">
            <div style={modalPanelStyle}>
              <div style={modalHeaderStyle}>
                <div>
                  <h3 style={{ fontSize: "1rem", margin: 0 }}>用户详情</h3>
                  <p style={{ margin: "4px 0 0", color: "var(--subtle)", fontSize: "0.8rem" }}>
                    查看账号基础信息和角色档案
                  </p>
                </div>
                <button type="button" style={closeButtonStyle} onClick={() => setDetailUser(null)} aria-label="关闭">&times;</button>
              </div>
              <div style={modalBodyStyle}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
                  <div>
                    <span style={detailLabelStyle}>ID</span>
                    <span>{detailUser.id}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>用户名</span>
                    <span>{detailUser.username}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>姓名</span>
                    <span>{detailUser.full_name || "-"}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>角色</span>
                    <span className={`role-badge role-badge--${detailUser.role}`}>{roleLabels[detailUser.role as AdminUserInput["role"]] || detailUser.role}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>邮箱</span>
                    <span>{detailUser.email || "-"}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>注册时间</span>
                    <span>{formatDate(detailUser.created_at)}</span>
                  </div>
                  <div>
                    <span style={detailLabelStyle}>更新时间</span>
                    <span>{formatDate(detailUser.updated_at)}</span>
                  </div>
                </div>
                {detailUser.profile && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border, #e0e0e0)" }}>
                    <h4 style={{ fontSize: "0.9rem", margin: "0 0 12px" }}>角色档案</h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
                      {detailUser.profile.student_id !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>学生档案 ID</span>
                          <span>{detailUser.profile.student_id}</span>
                        </div>
                      )}
                      {detailUser.profile.major !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>专业</span>
                          <span>{detailUser.profile.major || "-"}</span>
                        </div>
                      )}
                      {detailUser.profile.grade !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>年级</span>
                          <span>{detailUser.profile.grade || "-"}</span>
                        </div>
                      )}
                      {detailUser.profile.career_goal !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>职业目标</span>
                          <span>{detailUser.profile.career_goal || "-"}</span>
                        </div>
                      )}
                      {detailUser.profile.target_job_code !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>目标岗位</span>
                          <span>{detailUser.profile.target_job_code || "-"}</span>
                        </div>
                      )}
                      {detailUser.profile.teacher_id !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>教师档案 ID</span>
                          <span>{detailUser.profile.teacher_id}</span>
                        </div>
                      )}
                      {detailUser.profile.department !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>院系</span>
                          <span>{detailUser.profile.department || "-"}</span>
                        </div>
                      )}
                      {detailUser.profile.title !== undefined && (
                        <div>
                          <span style={detailLabelStyle}>职称</span>
                          <span>{detailUser.profile.title || "-"}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", gap: 8 }}>
                  <button type="button" className="admin-action-button" onClick={() => setDetailUser(null)} disabled={saving}>
                    关闭
                  </button>
                  <button type="button" className="admin-action-button admin-action-button--primary" onClick={() => handleEdit(detailUser)} disabled={saving}>
                    编辑
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {editUser && (
          <div style={modalBackdropStyle} role="dialog" aria-modal="true" aria-label="编辑用户">
            <div style={modalPanelStyle}>
              <div style={modalHeaderStyle}>
                <div>
                  <h3 style={{ fontSize: "1rem", margin: 0 }}>编辑用户</h3>
                  <p style={{ margin: "4px 0 0", color: "var(--subtle)", fontSize: "0.8rem" }}>
                    修改 {editUser.full_name || editUser.username} 的账号信息
                  </p>
                </div>
                <button type="button" style={closeButtonStyle} onClick={() => setEditUser(null)} aria-label="关闭">&times;</button>
              </div>
              <form onSubmit={handleEditSubmit} style={modalBodyStyle}>
                {error && (
                  <div style={{
                    marginBottom: 12,
                    padding: "10px 14px",
                    borderRadius: 8,
                    background: "rgba(220, 38, 38, 0.1)",
                    color: "#dc2626",
                    fontSize: "0.875rem",
                  }}>
                    {error}
                  </div>
                )}
                <div className="admin-user-form">
                  <label>
                    <span>用户名</span>
                    <input value={editForm.username} onChange={(e) => setEditForm({ ...editForm, username: e.target.value })} required />
                  </label>
                  <label>
                    <span>姓名</span>
                    <input value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} required />
                  </label>
                  <label>
                    <span>角色</span>
                    <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value as AdminUserInput["role"] })}>
                      {Object.entries(roleLabels).map(([role, label]) => (
                        <option key={role} value={role}>{label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>邮箱</span>
                    <input type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} />
                  </label>
                  <label>
                    <span>新密码（可留空）</span>
                    <div className="password-field">
                      <input type={showPw.edit ? "text" : "password"} value={editForm.password || ""} onChange={(e) => setEditForm({ ...editForm, password: e.target.value })} />
                      <button type="button" onClick={() => setShowPw(v => ({ ...v, edit: !v.edit }))} className="password-toggle" tabIndex={-1} aria-label={showPw.edit ? "隐藏密码" : "显示密码"}><Icon name={showPw.edit ? "eye" : "eye-off"} size={18} /></button>
                    </div>
                  </label>
                </div>
                <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", gap: 8 }}>
                  <button type="button" className="admin-action-button" onClick={() => setEditUser(null)} disabled={saving}>
                    取消
                  </button>
                  <button type="submit" className="admin-action-button admin-action-button--primary" disabled={saving}>
                    {saving ? "保存中..." : "保存修改"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {deleteUser && (
          <div style={modalBackdropStyle} role="dialog" aria-modal="true" aria-label="确认删除用户">
            <div style={{ ...modalPanelStyle, width: "min(500px, 100%)" }}>
              <div style={modalHeaderStyle}>
                <div>
                  <h3 style={{ fontSize: "1rem", margin: 0 }}>确认删除用户</h3>
                  <p style={{ margin: "4px 0 0", color: "var(--subtle)", fontSize: "0.8rem" }}>
                    删除后该账号将无法登录
                  </p>
                </div>
                <button type="button" style={closeButtonStyle} onClick={() => setDeleteUser(null)} aria-label="关闭">&times;</button>
              </div>
              <div style={modalBodyStyle}>
                {error && (
                  <div style={{
                    marginBottom: 12,
                    padding: "10px 14px",
                    borderRadius: 8,
                    background: "rgba(220, 38, 38, 0.1)",
                    color: "#dc2626",
                    fontSize: "0.875rem",
                  }}>
                    {error}
                  </div>
                )}
                <div style={{ padding: 14, borderRadius: 8, background: "rgba(220, 38, 38, 0.08)", color: "#991b1b" }}>
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>请确认是否删除以下用户：</p>
                  <p style={{ margin: 0 }}>
                    {deleteUser.full_name || deleteUser.username}（{deleteUser.username}，
                    {roleLabels[deleteUser.role as AdminUserInput["role"]] || deleteUser.role}）
                  </p>
                </div>
                <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", gap: 8 }}>
                  <button type="button" className="admin-action-button" onClick={() => setDeleteUser(null)} disabled={saving}>
                    取消
                  </button>
                  <button type="button" className="admin-table-button admin-table-button--danger" onClick={confirmDelete} disabled={saving}>
                    {saving ? "删除中..." : "确认删除"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

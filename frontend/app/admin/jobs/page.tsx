"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { formatTime } from "@/lib/format";
import { Icon } from "@/components/Icon";
import {
  createAdminPosition,
  deleteAdminPosition,
  getAdminPositions,
  updateAdminPosition,
  type AdminPosition,
  type AdminPositionInput,
} from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

const emptyForm: AdminPositionInput = {
  job_code: "",
  title: "",
  summary: "",
  skill_requirements: [],
  certificate_requirements: [],
  innovation_requirements: "",
  learning_requirements: "",
  resilience_requirements: "",
  communication_requirements: "",
  internship_requirements: "",
};

const PAGE_SIZE = 20;

export default function AdminJobsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [positions, setPositions] = useState<AdminPosition[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<AdminPositionInput>(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const router = useRouter();

  const loadPositions = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getAdminPositions({
        keyword: keyword || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setPositions(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载岗位失败");
    } finally {
      setLoading(false);
    }
  }, [keyword, page]);

  useEffect(() => {
    loadPositions();
  }, [loadPositions]);

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
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setMessage("");
    setShowForm(false);
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
      if (editingId) {
        await updateAdminPosition(editingId, form);
        setMessage("岗位已更新");
      } else {
        await createAdminPosition(form);
        setMessage("岗位已新增");
      }
      resetForm();
      await loadPositions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (pos: AdminPosition) => {
    setEditingId(pos.id);
    setForm({
      job_code: pos.job_code,
      title: pos.title,
      summary: pos.summary || "",
      skill_requirements: pos.skill_requirements || [],
      certificate_requirements: pos.certificate_requirements || [],
      innovation_requirements: pos.innovation_requirements || "",
      learning_requirements: pos.learning_requirements || "",
      resilience_requirements: pos.resilience_requirements || "",
      communication_requirements: pos.communication_requirements || "",
      internship_requirements: pos.internship_requirements || "",
    });
    setError("");
    setMessage("正在编辑岗位");
    setShowForm(true);
  };

  const handleDelete = async (pos: AdminPosition) => {
    if (!window.confirm(`确定删除岗位"${pos.title}"（${pos.job_code}）吗？有关联匹配结果的岗位将被后端拒绝删除。`)) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await deleteAdminPosition(pos.id);
      setPositions((prev) => prev.filter((p) => p.id !== pos.id));
      setTotal((prev) => prev - 1);
      if (editingId === pos.id) resetForm();
      setMessage("岗位已删除");
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setSaving(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

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
          <span className="workspace-topbar__title">岗位管理</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 4px" }}>岗位管理</h2>
            <p style={{ margin: 0, color: "var(--subtle)", fontSize: "0.875rem" }}>
              管理职位画像数据，支持新增、查看、编辑和删除。共 {total} 个岗位画像。
            </p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="admin-action-button" onClick={loadPositions} disabled={loading || saving}>
              刷新
            </button>
            <button
              type="button"
              className="admin-action-button admin-action-button--primary"
              onClick={() => { resetForm(); setShowForm(true); }}
              disabled={saving}
            >
              <Icon name="plus" size={14} /> 新增岗位
            </button>
          </div>
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
              placeholder="搜索岗位编码或岗位名称..."
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
            <button type="submit" className="admin-action-button admin-action-button--primary" disabled={loading}>
              搜索
            </button>
            {keyword && (
              <button
                type="button"
                className="admin-action-button"
                onClick={() => { setKeyword(""); setPage(0); }}
                disabled={loading}
              >
                清除筛选
              </button>
            )}
          </form>
        </div>

        {/* 新增/编辑表单 */}
        {showForm && (
          <div className="admin-dashboard__card" style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <h3 style={{ fontSize: "1rem", margin: 0 }}>{editingId ? "编辑岗位" : "新增岗位"}</h3>
              <button type="button" onClick={resetForm} style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer", color: "var(--subtle)", lineHeight: 1 }}>
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit} className="admin-user-form">
              <label>
                <span>岗位编码 *</span>
                <input
                  value={form.job_code || ""}
                  onChange={(e) => setForm({ ...form, job_code: e.target.value })}
                  placeholder="例如：software-engineer"
                  required
                />
              </label>
              <label>
                <span>岗位名称 *</span>
                <input
                  value={form.title || ""}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="例如：软件工程师"
                  required
                />
              </label>
              <label>
                <span>岗位概述</span>
                <textarea
                  value={form.summary || ""}
                  onChange={(e) => setForm({ ...form, summary: e.target.value })}
                  placeholder="岗位简要描述..."
                  rows={3}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border, #e0e0e0)", fontSize: "0.875rem", outline: "none", resize: "vertical", fontFamily: "inherit" }}
                />
              </label>
              <label>
                <span>技能要求</span>
                <input
                  value={(form.skill_requirements || []).join("、")}
                  onChange={(e) => setForm({ ...form, skill_requirements: e.target.value ? e.target.value.split(/[,，、\n]/).map(s => s.trim()).filter(Boolean) : [] })}
                  placeholder="多项技能用顿号、逗号或换行分隔"
                />
              </label>
              <label>
                <span>证书要求</span>
                <input
                  value={(form.certificate_requirements || []).join("、")}
                  onChange={(e) => setForm({ ...form, certificate_requirements: e.target.value ? e.target.value.split(/[,，、\n]/).map(s => s.trim()).filter(Boolean) : [] })}
                  placeholder="多项证书用顿号、逗号或换行分隔"
                />
              </label>
              <div className="admin-user-form__actions">
                <button type="submit" className="admin-action-button admin-action-button--primary" disabled={saving}>
                  {saving ? "保存中..." : editingId ? "保存修改" : "新增岗位"}
                </button>
                <button type="button" className="admin-action-button" onClick={resetForm} disabled={saving}>
                  取消
                </button>
              </div>
            </form>
          </div>
        )}

        {/* 岗位列表 */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="admin-dashboard__card">
            <div style={{ overflowX: "auto" }}>
              <table className="admin-user-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>岗位编码</th>
                    <th>岗位名称</th>
                    <th>核心技能</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: "center", padding: 24, color: "var(--subtle)" }}>
                        {keyword ? "没有匹配的岗位" : "暂无岗位数据"}
                      </td>
                    </tr>
                  ) : (
                    positions.map((pos) => (
                      <tr key={pos.id}>
                        <td style={{ color: "var(--subtle)", fontSize: "0.8rem" }}>{pos.id}</td>
                        <td><code style={{ fontSize: "0.8125rem" }}>{pos.job_code}</code></td>
                        <td><strong>{pos.title}</strong></td>
                        <td>{(pos.skill_requirements || []).slice(0, 4).join("、")}{(pos.skill_requirements || []).length > 4 ? "..." : ""}</td>
                        <td style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}>{formatDate(pos.created_at)}</td>
                        <td>
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            <button type="button" className="admin-table-button" onClick={() => handleEdit(pos)} disabled={saving}>编辑</button>
                            <button type="button" className="admin-table-button admin-table-button--danger" onClick={() => handleDelete(pos)} disabled={saving}>删除</button>
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
      </div>
    </div>
  );
}

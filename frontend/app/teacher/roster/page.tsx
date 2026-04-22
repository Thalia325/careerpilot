"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import {
  searchRosterCandidates,
  addStudentToRoster,
  removeStudentFromRoster,
  getTeacherStudentReports,
  type RosterCandidate,
} from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "状态跟进", icon: <Icon name="chat" size={18} /> },
  { href: "/teacher/roster", label: "花名册管理", icon: <Icon name="users" size={18} /> },
];

type BoundStudent = {
  student_id: number;
  username: string;
  full_name: string;
  email: string;
  major: string;
  grade: string;
};

export default function TeacherRosterPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

  // Bound students list
  const [boundStudents, setBoundStudents] = useState<BoundStudent[]>([]);
  const [loadingBound, setLoadingBound] = useState(true);

  // Search state
  const [searchKeyword, setSearchKeyword] = useState("");
  const [searchResults, setSearchResults] = useState<RosterCandidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);

  // Action state
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Remove confirmation
  const [confirmRemoveId, setConfirmRemoveId] = useState<number | null>(null);

  // Group name for add
  const [groupName, setGroupName] = useState("");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  // Load bound students on mount using the teacher reports API
  const loadBoundStudents = useCallback(async () => {
    setLoadingBound(true);
    try {
      const reports = await getTeacherStudentReports();
      const students = reports.map((r) => ({
        student_id: r.student_id,
        username: r.name,
        full_name: r.name,
        email: "",
        major: r.major,
        grade: r.grade,
      }));
      setBoundStudents(students);
    } catch (e) {
      console.error("Failed to load bound students:", e);
    } finally {
      setLoadingBound(false);
    }
  }, []);

  useEffect(() => {
    loadBoundStudents();
  }, [loadBoundStudents]);

  // Search handler
  const handleSearch = async () => {
    const kw = searchKeyword.trim();
    if (!kw) return;
    setSearching(true);
    setError("");
    setSuccess("");
    try {
      const res = await searchRosterCandidates(kw);
      setSearchResults(res);
      setSearched(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "搜索失败";
      setError(msg);
      setSearchResults([]);
      setSearched(true);
    } finally {
      setSearching(false);
    }
  };

  // Add student to roster
  const handleAdd = async (studentId: number) => {
    setActionLoading(studentId);
    setError("");
    setSuccess("");
    try {
      await addStudentToRoster(studentId, groupName || undefined);
      setSuccess("添加成功");
      // Refresh search results and bound list
      if (searchKeyword.trim()) {
        const res = await searchRosterCandidates(searchKeyword.trim());
        setSearchResults(res);
      }
      await loadBoundStudents();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "添加失败";
      setError(msg);
    } finally {
      setActionLoading(null);
      setGroupName("");
    }
  };

  // Remove student from roster
  const handleRemove = async (studentId: number) => {
    setActionLoading(studentId);
    setError("");
    setSuccess("");
    try {
      await removeStudentFromRoster(studentId);
      setSuccess("移除成功");
      setConfirmRemoveId(null);
      // Refresh bound list and search results
      await loadBoundStudents();
      if (searchKeyword.trim()) {
        const res = await searchRosterCandidates(searchKeyword.trim());
        setSearchResults(res);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "移除失败";
      setError(msg);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="workspace-bg">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={teacherNavItems}
        label="教师功能"
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
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)}>
            <Icon name="menu" size={20} />
          </button>
          <span className="workspace-topbar__title">花名册管理</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">教师</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="teacher-dashboard">
        {/* Error / Success messages */}
        {error && (
          <div className="roster-error-banner">
            <Icon name="alert-circle" size={16} />
            <span>{error}</span>
            <button onClick={() => setError("")} className="roster-banner-close">&times;</button>
          </div>
        )}
        {success && (
          <div className="roster-success-banner">
            <Icon name="check-circle" size={16} />
            <span>{success}</span>
            <button onClick={() => setSuccess("")} className="roster-banner-close">&times;</button>
          </div>
        )}

        {/* Bound students section */}
        <div className="teacher-dashboard__card" style={{ marginBottom: 24 }}>
          <h2>
            <Icon name="users" size={18} style={{ marginRight: 8, verticalAlign: "middle" }} />
            我的学生 ({boundStudents.length})
          </h2>
          {loadingBound ? (
            <div className="roster-loading">加载中...</div>
          ) : boundStudents.length === 0 ? (
            <div className="roster-empty">
              <Icon name="users" size={32} style={{ opacity: 0.3 }} />
              <p>暂无绑定学生</p>
              <p style={{ fontSize: "0.8125rem", color: "var(--subtle)" }}>使用下方搜索功能添加学生到您的班级</p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="teacher-dashboard__table">
                <thead>
                  <tr>
                    <th>姓名</th>
                    <th>用户名</th>
                    <th>邮箱</th>
                    <th>专业</th>
                    <th>年级</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {boundStudents.map((s) => (
                    <tr key={s.student_id}>
                      <td>{s.full_name || s.username}</td>
                      <td>{s.username}</td>
                      <td>{s.email || "-"}</td>
                      <td>{s.major || "-"}</td>
                      <td>{s.grade || "-"}</td>
                      <td>
                        {confirmRemoveId === s.student_id ? (
                          <span className="roster-confirm-remove">
                            确认移除？
                            <button
                              className="btn-primary roster-btn-danger"
                              disabled={actionLoading === s.student_id}
                              onClick={() => handleRemove(s.student_id)}
                              style={{ marginLeft: 6, padding: "4px 10px", fontSize: "0.8125rem" }}
                            >
                              {actionLoading === s.student_id ? "..." : "确认"}
                            </button>
                            <button
                              className="btn-secondary"
                              onClick={() => setConfirmRemoveId(null)}
                              style={{ marginLeft: 4, padding: "4px 10px", fontSize: "0.8125rem" }}
                            >
                              取消
                            </button>
                          </span>
                        ) : (
                          <button
                            className="btn-secondary roster-btn-remove"
                            disabled={actionLoading === s.student_id}
                            onClick={() => setConfirmRemoveId(s.student_id)}
                            style={{ padding: "4px 10px", fontSize: "0.8125rem" }}
                          >
                            {actionLoading === s.student_id ? "..." : "移除"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Search and add section */}
        <div className="teacher-dashboard__card">
          <h2>
            <Icon name="search" size={18} style={{ marginRight: 8, verticalAlign: "middle" }} />
            搜索学生
          </h2>
          <div className="roster-search-bar">
            <input
              type="text"
              className="roster-search-input"
              placeholder="输入用户名、邮箱、专业或年级搜索..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
            />
            <button
              className="btn-primary roster-search-btn"
              disabled={searching || !searchKeyword.trim()}
              onClick={handleSearch}
            >
              {searching ? "搜索中..." : "搜索"}
            </button>
          </div>

          {searched && (
            <div style={{ marginTop: 16 }}>
              {searchResults.length === 0 ? (
                <div className="roster-empty" style={{ padding: "24px 0" }}>
                  <p>未找到匹配的学生</p>
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="teacher-dashboard__table">
                    <thead>
                      <tr>
                        <th>姓名</th>
                        <th>用户名</th>
                        <th>邮箱</th>
                        <th>专业</th>
                        <th>年级</th>
                        <th>状态</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults.map((s) => (
                        <tr key={s.student_id}>
                          <td>{s.full_name || s.username}</td>
                          <td>{s.username}</td>
                          <td>{s.email || "-"}</td>
                          <td>{s.major || "-"}</td>
                          <td>{s.grade || "-"}</td>
                          <td>
                            {s.already_bound ? (
                              <span className="roster-badge roster-badge-bound">已绑定</span>
                            ) : (
                              <span className="roster-badge roster-badge-available">可添加</span>
                            )}
                          </td>
                          <td>
                            {s.already_bound ? (
                              <span style={{ fontSize: "0.8125rem", color: "var(--subtle)" }}>-</span>
                            ) : (
                              <div className="roster-add-action">
                                <input
                                  type="text"
                                  className="roster-group-input"
                                  placeholder="分组名(可选)"
                                  value={actionLoading === s.student_id ? groupName : ""}
                                  onChange={(e) => setGroupName(e.target.value)}
                                />
                                <button
                                  className="btn-primary roster-btn-add"
                                  disabled={actionLoading === s.student_id}
                                  onClick={() => handleAdd(s.student_id)}
                                  style={{ padding: "4px 10px", fontSize: "0.8125rem" }}
                                >
                                  {actionLoading === s.student_id ? "..." : "添加"}
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

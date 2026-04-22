"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import {
  getTeacherStudentReports,
  getTeacherStudentReportList,
  getTeacherReportDetail,
  createTeacherComment,
  getTeacherComments,
  updateTeacherComment,
  deleteTeacherComment,
  type TeacherStudentReport,
  type TeacherStudentReportListItem,
  type TeacherReportDetail,
  type TeacherCommentItem,
} from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "状态跟进", icon: <Icon name="chat" size={18} /> },
  { href: "/teacher/roster", label: "花名册管理", icon: <Icon name="users" size={18} /> },
];

const followupStatusOptions = [
  { key: "pending", label: "待跟进" },
  { key: "in_progress", label: "跟进中" },
  { key: "read", label: "已读" },
  { key: "communicated", label: "已沟通" },
  { key: "review", label: "需复盘" },
  { key: "completed", label: "已完成" },
  { key: "overdue", label: "已逾期" },
];

const priorityOptions = [
  { key: "low", label: "低" },
  { key: "normal", label: "普通" },
  { key: "high", label: "高" },
  { key: "urgent", label: "紧急" },
];

export default function TeacherReportsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [reports, setReports] = useState<TeacherStudentReport[]>([]);
  const [loading, setLoading] = useState(true);

  // Report detail state
  const [selectedStudent, setSelectedStudent] = useState<TeacherStudentReport | null>(null);
  const [studentReportList, setStudentReportList] = useState<TeacherStudentReportListItem[]>([]);
  const [reportDetail, setReportDetail] = useState<TeacherReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Comment state
  const [comments, setComments] = useState<TeacherCommentItem[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [newComment, setNewComment] = useState("");
  const [newPriority, setNewPriority] = useState("normal");
  const [newVisible, setNewVisible] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editCommentText, setEditCommentText] = useState("");
  const [editPriority, setEditPriority] = useState("normal");
  const [editVisible, setEditVisible] = useState(true);
  const [editFollowUpStatus, setEditFollowUpStatus] = useState("");
  const [editFollowUpDate, setEditFollowUpDate] = useState("");
  const [commentError, setCommentError] = useState("");

  const router = useRouter();

  useEffect(() => {
    getTeacherStudentReports()
      .then((res) => setReports(res))
      .catch((e) => console.error("Failed to load reports:", e))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectStudent = async (student: TeacherStudentReport) => {
    setSelectedStudent(student);
    setReportDetail(null);
    setDetailLoading(true);
    try {
      const list = await getTeacherStudentReportList(student.student_id);
      setStudentReportList(list);
    } catch (e) {
      console.error("Failed to load student reports:", e);
      setStudentReportList([]);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSelectReport = async (reportId: number) => {
    setDetailLoading(true);
    setCommentError("");
    try {
      const detail = await getTeacherReportDetail(reportId);
      setReportDetail(detail);
      // Load comments for this report
      setCommentsLoading(true);
      try {
        const commentList = await getTeacherComments(reportId);
        setComments(commentList);
      } catch (e) {
        console.error("Failed to load comments:", e);
        setComments([]);
      } finally {
        setCommentsLoading(false);
      }
    } catch (e) {
      console.error("Failed to load report detail:", e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateComment = async () => {
    if (!reportDetail || !newComment.trim() || submitting) return;
    setSubmitting(true);
    setCommentError("");
    try {
      const created = await createTeacherComment(reportDetail.report_id, newComment.trim(), {
        priority: newPriority,
        visible_to_student: newVisible,
      });
      setComments((prev) => [created as TeacherCommentItem, ...prev]);
      setNewComment("");
      setNewPriority("normal");
      setNewVisible(true);
    } catch (e) {
      setCommentError(e instanceof Error ? e.message : "提交点评失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateComment = async (commentId: number) => {
    if (!editCommentText.trim() || submitting) return;
    setSubmitting(true);
    setCommentError("");
    try {
      const updated = await updateTeacherComment(commentId, {
        comment_text: editCommentText.trim(),
        priority: editPriority,
        visible_to_student: editVisible,
        follow_up_status: editFollowUpStatus || undefined,
        next_follow_up_date: editFollowUpDate || undefined,
      });
      setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, ...updated } as TeacherCommentItem : c)));
      setEditingCommentId(null);
    } catch (e) {
      setCommentError(e instanceof Error ? e.message : "更新点评失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (submitting) return;
    if (!confirm("确定删除此点评吗？")) return;
    setSubmitting(true);
    setCommentError("");
    try {
      await deleteTeacherComment(commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      if (editingCommentId === commentId) setEditingCommentId(null);
    } catch (e) {
      setCommentError(e instanceof Error ? e.message : "删除点评失败");
    } finally {
      setSubmitting(false);
    }
  };

  const startEditComment = (c: TeacherCommentItem) => {
    setEditingCommentId(c.id);
    setEditCommentText(c.comment);
    setEditPriority(c.priority);
    setEditVisible(c.visible_to_student);
    setEditFollowUpStatus(c.follow_up_status || "");
    setEditFollowUpDate(c.next_follow_up_date ? c.next_follow_up_date.slice(0, 10) : "");
  };

  const handleBack = () => {
    if (reportDetail) {
      setReportDetail(null);
    } else {
      setSelectedStudent(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const renderStudentList = () => (
    <>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>学生报告查看</h1>
      <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 16px" }}>点击学生查看报告详情</p>
      {loading ? (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
      ) : reports.length > 0 ? (
        <div className="history-list">
          {reports.map((r) => (
            <div
              key={r.student_id}
              className="history-item"
              style={{ cursor: "pointer" }}
              onClick={() => handleSelectStudent(r)}
            >
              <div>
                <p className="history-item__title">{r.name} — {r.target_job || r.career_goal || "未设置目标"}</p>
                <p className="history-item__desc">
                  {r.major} · {r.grade} · 匹配度 {r.match_score > 0 ? `${r.match_score} 分` : "待分析"} · {r.report_status}
                </p>
              </div>
              <span style={{
                padding: "2px 8px",
                borderRadius: 12,
                fontSize: "0.75rem",
                fontWeight: 600,
                background: r.report_status === "已完成" ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                color: r.report_status === "已完成" ? "#0b7b72" : "#b76a09",
              }}>
                {r.report_status}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无学生报告</div>
      )}
    </>
  );

  const renderStudentReports = () => (
    <>
      <button onClick={handleBack} style={{
        background: "none", border: "none", cursor: "pointer",
        color: "var(--color-primary)", fontSize: "0.9rem", marginBottom: 16, padding: 0,
      }}>
        ← 返回学生列表
      </button>
      <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: "0 0 8px" }}>
        {selectedStudent?.name} 的报告
      </h2>
      <p style={{ fontSize: "0.85rem", color: "var(--subtle)", margin: "0 0 16px" }}>
        {selectedStudent?.major} · {selectedStudent?.grade}
      </p>
      {detailLoading ? (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
      ) : studentReportList.length > 0 ? (
        <div className="history-list">
          {studentReportList.map((r) => (
            <div
              key={r.report_id}
              className="history-item"
              style={{ cursor: "pointer" }}
              onClick={() => handleSelectReport(r.report_id)}
            >
              <div>
                <p className="history-item__title">
                  {r.target_job || "未设置岗位"} — 报告 #{r.report_id}
                  {r.profile_version_no ? ` (画像 v${r.profile_version_no})` : ""}
                </p>
                <p className="history-item__desc">
                  状态: {r.status} · 创建: {r.created_at ? new Date(r.created_at).toLocaleString("zh-CN") : "-"}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>该学生暂无报告</div>
      )}
    </>
  );

  const renderReportDetail = () => {
    if (!reportDetail) return null;
    const d = reportDetail;
    const match = d.match_analysis;

    return (
      <>
        <button onClick={handleBack} style={{
          background: "none", border: "none", cursor: "pointer",
          color: "var(--color-primary)", fontSize: "0.9rem", marginBottom: 16, padding: 0,
        }}>
          ← 返回报告列表
        </button>

        <div style={{ display: "grid", gap: 16 }}>
          {/* Student info */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>学生信息</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, fontSize: "0.9rem" }}>
              <div><span style={{ color: "var(--subtle)" }}>姓名:</span> {d.student_name}</div>
              <div><span style={{ color: "var(--subtle)" }}>专业:</span> {d.student_major}</div>
              <div><span style={{ color: "var(--subtle)" }}>年级:</span> {d.student_grade}</div>
            </div>
          </div>

          {/* Match analysis */}
          {match && match.total_score > 0 && (
            <div className="teacher-dashboard__card">
              <h3 style={{ margin: "0 0 12px" }}>人岗匹配分析</h3>
              <div style={{ fontSize: "2rem", fontWeight: 700, color: match.total_score >= 80 ? "#0b7b72" : match.total_score >= 60 ? "#f59e0b" : "#ef4444", marginBottom: 12 }}>
                {match.total_score.toFixed(1)} 分
              </div>
              {match.strengths && match.strengths.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 4 }}>契合点</div>
                  {match.strengths.map((s, i) => (
                    <div key={i} style={{ fontSize: "0.85rem", color: "#0b7b72", padding: "2px 0" }}>+ {s}</div>
                  ))}
                </div>
              )}
              {match.gaps && match.gaps.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 4 }}>差距项</div>
                  {match.gaps.map((g, i) => (
                    <div key={i} style={{ fontSize: "0.85rem", color: "#ef4444", padding: "2px 0" }}>- {g.item || g.description || JSON.stringify(g)}</div>
                  ))}
                </div>
              )}
              {match.suggestions && match.suggestions.length > 0 && (
                <div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 4 }}>提升建议</div>
                  {match.suggestions.map((s, i) => (
                    <div key={i} style={{ fontSize: "0.85rem", color: "var(--color-primary)", padding: "2px 0" }}>{i + 1}. {s}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Report content */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>报告正文</h3>
            <div style={{
              background: "#f8fafc", borderRadius: 8, padding: 16,
              maxHeight: 400, overflow: "auto", fontSize: "0.85rem",
              whiteSpace: "pre-wrap", lineHeight: 1.6,
            }}>
              {d.markdown_content || "暂无报告内容"}
            </div>
          </div>

          {/* Teacher comments section */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>教师点评与跟进</h3>

            {commentError && (
              <div style={{ padding: "8px 12px", borderRadius: 6, background: "#fef2f2", color: "#b91c1c", fontSize: "0.85rem", marginBottom: 12 }}>
                {commentError}
              </div>
            )}

            {/* New comment form */}
            <div style={{ marginBottom: 16, padding: 16, background: "#f8fafc", borderRadius: 8 }}>
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="输入点评内容..."
                disabled={submitting}
                style={{
                  width: "100%", minHeight: 80, padding: 10, borderRadius: 6,
                  border: "1px solid #d1d5db", fontSize: "0.875rem", resize: "vertical",
                  marginBottom: 10, fontFamily: "inherit",
                }}
              />
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <label style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>优先级:</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    disabled={submitting}
                    style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: "0.8rem" }}
                  >
                    {priorityOptions.map((p) => (
                      <option key={p.key} value={p.key}>{p.label}</option>
                    ))}
                  </select>
                </div>
                <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={newVisible}
                    onChange={(e) => setNewVisible(e.target.checked)}
                    disabled={submitting}
                  />
                  对学生可见
                </label>
                <button
                  className="btn-primary"
                  onClick={handleCreateComment}
                  disabled={!newComment.trim() || submitting}
                  style={{ marginLeft: "auto", padding: "6px 16px", fontSize: "0.85rem" }}
                >
                  {submitting && editingCommentId === null ? "提交中..." : "提交点评"}
                </button>
              </div>
            </div>

            {/* Comments list */}
            {commentsLoading ? (
              <div style={{ textAlign: "center", padding: 20, color: "var(--subtle)", fontSize: "0.85rem" }}>加载点评中...</div>
            ) : comments.length > 0 ? (
              <div style={{ display: "grid", gap: 10 }}>
                {comments.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8,
                      padding: 14, background: "#fff",
                    }}
                  >
                    {editingCommentId === c.id ? (
                      /* Edit mode */
                      <div>
                        <textarea
                          value={editCommentText}
                          onChange={(e) => setEditCommentText(e.target.value)}
                          style={{
                            width: "100%", minHeight: 60, padding: 8, borderRadius: 6,
                            border: "1px solid #d1d5db", fontSize: "0.85rem", resize: "vertical",
                            marginBottom: 10, fontFamily: "inherit",
                          }}
                        />
                        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <label style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>优先级:</label>
                            <select
                              value={editPriority}
                              onChange={(e) => setEditPriority(e.target.value)}
                              style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: "0.8rem" }}
                            >
                              {priorityOptions.map((p) => (
                                <option key={p.key} value={p.key}>{p.label}</option>
                              ))}
                            </select>
                          </div>
                          <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.8rem", cursor: "pointer" }}>
                            <input
                              type="checkbox"
                              checked={editVisible}
                              onChange={(e) => setEditVisible(e.target.checked)}
                            />
                            对学生可见
                          </label>
                        </div>
                        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <label style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>跟进状态:</label>
                            <select
                              value={editFollowUpStatus}
                              onChange={(e) => setEditFollowUpStatus(e.target.value)}
                              style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: "0.8rem" }}
                            >
                              <option value="">未设置</option>
                              {followupStatusOptions.map((s) => (
                                <option key={s.key} value={s.key}>{s.label}</option>
                              ))}
                            </select>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <label style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>下次跟进日期:</label>
                            <input
                              type="date"
                              value={editFollowUpDate}
                              onChange={(e) => setEditFollowUpDate(e.target.value)}
                              style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d1d5db", fontSize: "0.8rem" }}
                            />
                          </div>
                        </div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <button
                            className="btn-primary"
                            onClick={() => handleUpdateComment(c.id)}
                            disabled={!editCommentText.trim() || submitting}
                            style={{ padding: "4px 14px", fontSize: "0.8rem" }}
                          >
                            {submitting ? "保存中..." : "保存"}
                          </button>
                          <button
                            className="btn-secondary"
                            onClick={() => setEditingCommentId(null)}
                            disabled={submitting}
                            style={{ padding: "4px 14px", fontSize: "0.8rem" }}
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Display mode */
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>{c.teacher_name}</span>
                            <span style={{
                              padding: "1px 8px", borderRadius: 10, fontSize: "0.7rem", fontWeight: 600,
                              background: c.priority === "urgent" ? "rgba(239,68,68,0.1)" : c.priority === "high" ? "rgba(245,158,11,0.1)" : c.priority === "low" ? "rgba(107,114,128,0.1)" : "rgba(0,0,0,0.05)",
                              color: c.priority === "urgent" ? "#ef4444" : c.priority === "high" ? "#f59e0b" : c.priority === "low" ? "#6b7280" : "#374151",
                            }}>
                              {priorityOptions.find((p) => p.key === c.priority)?.label || c.priority}
                            </span>
                            {!c.visible_to_student && (
                              <span style={{ padding: "1px 8px", borderRadius: 10, fontSize: "0.7rem", fontWeight: 600, background: "rgba(107,114,128,0.1)", color: "#6b7280" }}>
                                对学生隐藏
                              </span>
                            )}
                            {c.visible_to_student && c.student_read_at && (
                              <span style={{ padding: "1px 8px", borderRadius: 10, fontSize: "0.7rem", fontWeight: 600, background: "rgba(11,123,114,0.1)", color: "#0b7b72" }}>
                                学生已读
                              </span>
                            )}
                          </div>
                          {c.created_at && (
                            <span style={{ fontSize: "0.75rem", color: "var(--subtle)" }}>
                              {new Date(c.created_at).toLocaleString("zh-CN")}
                            </span>
                          )}
                        </div>
                        <p style={{ margin: "0 0 8px", fontSize: "0.875rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{c.comment}</p>
                        {(c.follow_up_status || c.next_follow_up_date) && (
                          <div style={{ display: "flex", gap: 12, fontSize: "0.8rem", color: "var(--subtle)", marginBottom: 8 }}>
                            {c.follow_up_status && (
                              <span>跟进: {followupStatusOptions.find((s) => s.key === c.follow_up_status)?.label || c.follow_up_status}</span>
                            )}
                            {c.next_follow_up_date && (
                              <span>下次跟进: {c.next_follow_up_date.slice(0, 10)}</span>
                            )}
                          </div>
                        )}
                        <div style={{ display: "flex", gap: 6 }}>
                          <button
                            className="btn-secondary"
                            onClick={() => startEditComment(c)}
                            disabled={submitting}
                            style={{ padding: "3px 10px", fontSize: "0.75rem" }}
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => handleDeleteComment(c.id)}
                            disabled={submitting}
                            style={{
                              padding: "3px 10px", fontSize: "0.75rem", borderRadius: 6,
                              border: "1px solid #fca5a5", background: "#fff", color: "#ef4444",
                              cursor: submitting ? "not-allowed" : "pointer",
                            }}
                          >
                            删除
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: 20, color: "var(--subtle)", fontSize: "0.85rem" }}>暂无点评</div>
            )}
          </div>
        </div>
      </>
    );
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
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单"><Icon name="menu" size={20} /></button>
          <span className="workspace-topbar__title">学生报告查看</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        {reportDetail ? renderReportDetail() : selectedStudent ? renderStudentReports() : renderStudentList()}
      </div>
    </div>
  );
}

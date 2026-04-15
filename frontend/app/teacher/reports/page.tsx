"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import {
  getTeacherStudentReports,
  getTeacherStudentReportList,
  getTeacherReportDetail,
  type TeacherStudentReport,
  type TeacherStudentReportListItem,
  type TeacherReportDetail,
} from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
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
    try {
      const detail = await getTeacherReportDetail(reportId);
      setReportDetail(detail);
    } catch (e) {
      console.error("Failed to load report detail:", e);
    } finally {
      setDetailLoading(false);
    }
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

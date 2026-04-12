"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getTeacherStudentReports, type TeacherStudentReport } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

export default function TeacherReportsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [reports, setReports] = useState<TeacherStudentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getTeacherStudentReports()
      .then((res) => setReports(res.filter(r => r.report_status !== "未开始")))
      .catch((e) => console.error("Failed to load reports:", e))
      .finally(() => setLoading(false));
  }, []);

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
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>学生报告查看</h1>
        <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 16px" }}>查看和管理学生的职业规划报告</p>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : reports.length > 0 ? (
          <div className="history-list">
            {reports.map((r) => (
              <div key={r.student_id} className="history-item">
                <div>
                  <p className="history-item__title">{r.name} — {r.target_job || r.career_goal}方向报告</p>
                  <p className="history-item__desc">
                    匹配度 {r.match_score > 0 ? `${r.match_score} 分` : "待分析"} · {r.report_status}
                  </p>
                </div>
                <span style={{
                  padding: "2px 8px",
                  borderRadius: 12,
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  background: r.report_status === "已完成" ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                  color: r.report_status === "已完成" ? "#0b7b72" : "#b76a09"
                }}>
                  {r.report_status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无学生报告</div>
        )}
      </div>
    </div>
  );
}

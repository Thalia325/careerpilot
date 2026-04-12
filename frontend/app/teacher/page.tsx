"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import {
  getTeacherStudentReports,
  getMatchDistribution,
  type TeacherStudentReport,
  type DistributionItem,
} from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

export default function TeacherPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [studentReports, setStudentReports] = useState<TeacherStudentReport[]>([]);
  const [matchDistribution, setMatchDistribution] = useState<DistributionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const [reportsRes, distRes] = await Promise.all([
          getTeacherStudentReports(),
          getMatchDistribution(),
        ]);
        setStudentReports(reportsRes);
        setMatchDistribution(distRes);
      } catch (e) {
        console.error("Failed to load teacher data:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
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
          <span className="workspace-topbar__title">教师工作台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">教师</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="teacher-dashboard">
        {loading ? (
          <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="teacher-dashboard__grid">
            <div className="teacher-dashboard__card">
              <h2>学生报告查看</h2>
              {studentReports.length > 0 ? (
                <table className="teacher-dashboard__table">
                  <thead>
                    <tr>
                      <th>学生</th>
                      <th>目标岗位</th>
                      <th>匹配度</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentReports.map((s) => (
                      <tr key={s.student_id}>
                        <td><strong>{s.name}</strong></td>
                        <td>{s.target_job || s.career_goal || "-"}</td>
                        <td>{s.match_score > 0 ? `${s.match_score} 分` : "-"}</td>
                        <td>
                          <span style={{
                            padding: "2px 8px",
                            borderRadius: 12,
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            background: s.report_status === "已完成" ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                            color: s.report_status === "已完成" ? "#0b7b72" : "#b76a09"
                          }}>
                            {s.report_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无学生数据</div>
              )}
            </div>

            <div className="teacher-dashboard__card">
              <h2>班级数据概览</h2>
              {matchDistribution.length > 0 && matchDistribution.some(d => d.count > 0) ? (
                <div className="teacher-dashboard__chart-area">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={matchDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#173f8a" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>暂无匹配数据</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

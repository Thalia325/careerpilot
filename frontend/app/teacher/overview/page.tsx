"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from "recharts";
import { getMajorDistribution, getClassOverview, type MajorDistributionItem, type ClassOverviewData } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
  { href: "/teacher/roster", label: "花名册管理", icon: <Icon name="users" size={18} /> },
];

const COLORS = ["#173f8a", "#0f74da", "#12b3a6", "#f59e0b", "#ef4444", "#8b5cf6", "#6366f1", "#14b8a6"];

export default function TeacherOverviewPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [majorDistribution, setMajorDistribution] = useState<MajorDistributionItem[]>([]);
  const [classData, setClassData] = useState<ClassOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    Promise.all([getMajorDistribution(), getClassOverview()])
      .then(([majors, overview]) => {
        setMajorDistribution(majors);
        setClassData(overview);
      })
      .catch((e) => console.error("Failed to load overview data:", e))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="workspace-bg">
        <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>加载中...</div>
      </div>
    );
  }

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
          <span className="workspace-topbar__title">班级数据概览</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        {/* Report completion rate */}
        {classData && (
          <div className="teacher-dashboard__card" style={{ marginBottom: 16, textAlign: "center", padding: "20px 16px" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--subtle)", marginBottom: 8 }}>报告完成率</div>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#0b7b72" }}>
              {classData.report_completion_rate}%
            </div>
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          {/* Major distribution */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>专业分布</h3>
            {majorDistribution.length > 0 && majorDistribution.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={majorDistribution} cx="50%" cy="50%" outerRadius={80} dataKey="value"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }>
                    {majorDistribution.map((_, index) => (
                      <Cell key={String(index)} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无数据</div>
            )}
          </div>

          {/* Job distribution */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>目标岗位分布</h3>
            {classData && classData.job_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={classData.job_distribution} cx="50%" cy="50%" outerRadius={80} dataKey="value"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }>
                    {classData.job_distribution.map((_, index) => (
                      <Cell key={String(index)} fill={COLORS[(index + 3) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无数据</div>
            )}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          {/* Resume completeness */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>简历完整度分布</h3>
            {classData && classData.resume_completeness.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={classData.resume_completeness}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#12b3a6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无数据</div>
            )}
          </div>

          {/* Skill gaps */}
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>技能短板 Top 10</h3>
            {classData && classData.skill_gaps.length > 0 ? (
              <div style={{ fontSize: "0.85rem" }}>
                {classData.skill_gaps.map((g, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #f1f5f9" }}>
                    <span>{i + 1}. {g.name}</span>
                    <span style={{ color: "#ef4444", fontWeight: 600 }}>{g.count} 人</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无数据</div>
            )}
          </div>
        </div>

        {/* Followup students */}
        {classData && classData.followup_students.length > 0 && (
          <div className="teacher-dashboard__card">
            <h3 style={{ margin: "0 0 12px" }}>待跟进学生</h3>
            <div style={{ overflowX: "auto" }}>
              <table className="teacher-dashboard__table">
                <thead>
                  <tr>
                    <th>学生</th>
                    <th>专业</th>
                    <th>职业目标</th>
                  </tr>
                </thead>
                <tbody>
                  {classData.followup_students.map((s) => (
                    <tr key={s.student_id}>
                      <td><strong>{s.name}</strong></td>
                      <td>{s.major || "-"}</td>
                      <td>{s.career_goal || "-"}</td>
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

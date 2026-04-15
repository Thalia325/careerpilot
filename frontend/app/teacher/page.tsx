"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import {
  getTeacherStudentReports,
  getMatchDistribution,
  getTeacherOverviewStats,
  type TeacherStudentReport,
  type TeacherReportFilters,
  type DistributionItem,
  type TeacherOverviewStats,
} from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

const metricCards = [
  { key: "total_students" as const, label: "学生总数", color: "#173f8a" },
  { key: "students_with_resume" as const, label: "已上传简历", color: "#0f74da" },
  { key: "students_with_profile" as const, label: "已生成画像", color: "#12b3a6" },
  { key: "students_with_report" as const, label: "已生成报告", color: "#0b7b72" },
  { key: "avg_match_score" as const, label: "平均匹配分", color: "#f59e0b", suffix: "分" },
  { key: "pending_review_reports" as const, label: "待点评报告", color: "#ef4444" },
  { key: "students_need_followup" as const, label: "待跟进学生", color: "#8b5cf6" },
];

const scoreRangeOptions = [
  { label: "全部", min: undefined, max: undefined },
  { label: "90分以上", min: 90, max: 101 },
  { label: "80-89分", min: 80, max: 90 },
  { label: "70-79分", min: 70, max: 80 },
  { label: "60-69分", min: 60, max: 70 },
  { label: "60分以下", min: 0, max: 60 },
];

const reportStatusOptions = ["", "已完成", "进行中", "待生成报告", "未开始"];

export default function TeacherPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [studentReports, setStudentReports] = useState<TeacherStudentReport[]>([]);
  const [matchDistribution, setMatchDistribution] = useState<DistributionItem[]>([]);
  const [overviewStats, setOverviewStats] = useState<TeacherOverviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Filter state
  const [filters, setFilters] = useState<TeacherReportFilters>({});
  const [selectedScoreRange, setSelectedScoreRange] = useState(0);

  // Extract unique values for filter dropdowns from current data
  const [allReports, setAllReports] = useState<TeacherStudentReport[]>([]);
  const majorOptions = [...new Set(allReports.map(r => r.major).filter(Boolean))];
  const gradeOptions = [...new Set(allReports.map(r => r.grade).filter(Boolean))];
  const targetJobOptions = [...new Set(allReports.map(r => r.target_job || r.career_goal).filter(Boolean))];

  const loadData = useCallback(async () => {
    try {
      const [reportsRes, distRes, statsRes] = await Promise.all([
        getTeacherStudentReports(),
        getMatchDistribution(),
        getTeacherOverviewStats(),
      ]);
      setAllReports(reportsRes);
      setStudentReports(reportsRes);
      setMatchDistribution(distRes);
      setOverviewStats(statsRes);
    } catch (e) {
      console.error("Failed to load teacher data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Apply filters
  useEffect(() => {
    let filtered = [...allReports];
    if (filters.major) filtered = filtered.filter(r => r.major === filters.major);
    if (filters.grade) filtered = filtered.filter(r => r.grade === filters.grade);
    if (filters.target_job) filtered = filtered.filter(r => r.target_job === filters.target_job || r.career_goal === filters.target_job);
    if (filters.report_status) filtered = filtered.filter(r => r.report_status === filters.report_status);
    if (filters.score_min !== undefined) filtered = filtered.filter(r => r.match_score >= (filters.score_min ?? 0));
    if (filters.score_max !== undefined) filtered = filtered.filter(r => r.match_score < (filters.score_max ?? 101));
    setStudentReports(filtered);
  }, [filters, allReports]);

  const handleScoreRangeChange = (idx: number) => {
    setSelectedScoreRange(idx);
    const opt = scoreRangeOptions[idx];
    setFilters(prev => ({ ...prev, score_min: opt.min, score_max: opt.max }));
  };

  const clearFilters = () => {
    setFilters({});
    setSelectedScoreRange(0);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const statusColor = (s: string) => {
    if (s === "已完成") return { bg: "rgba(11, 123, 114, 0.1)", color: "#0b7b72" };
    if (s === "跟进中") return { bg: "rgba(15, 116, 218, 0.1)", color: "#0f74da" };
    if (s === "待跟进" || s === "已逾期") return { bg: "rgba(239, 68, 68, 0.1)", color: "#ef4444" };
    return { bg: "rgba(245, 158, 11, 0.1)", color: "#b76a09" };
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
          <>
            {/* Overview metric cards */}
            {overviewStats && (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
                gap: 16,
                marginBottom: 24,
              }}>
                {metricCards.map((card) => (
                  <div key={card.key} className="teacher-dashboard__card" style={{ padding: "20px 16px", textAlign: "center" }}>
                    <div style={{ fontSize: "0.8rem", color: "var(--subtle)", marginBottom: 8 }}>{card.label}</div>
                    <div style={{ fontSize: "1.75rem", fontWeight: 700, color: card.color }}>
                      {overviewStats[card.key]}{card.suffix || ""}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="teacher-dashboard__grid">
              <div className="teacher-dashboard__card" style={{ gridColumn: "1 / -1" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h2 style={{ margin: 0 }}>学生报告查看</h2>
                  <button
                    onClick={clearFilters}
                    style={{
                      background: "none", border: "1px solid var(--subtle)", borderRadius: 6,
                      padding: "4px 12px", fontSize: "0.8rem", color: "var(--subtle)", cursor: "pointer",
                    }}
                  >
                    清除筛选
                  </button>
                </div>

                {/* Filter controls */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
                  <select
                    value={filters.major || ""}
                    onChange={e => setFilters(prev => ({ ...prev, major: e.target.value || undefined }))}
                    style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", minWidth: 120 }}
                  >
                    <option value="">全部专业</option>
                    {majorOptions.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>

                  <select
                    value={filters.grade || ""}
                    onChange={e => setFilters(prev => ({ ...prev, grade: e.target.value || undefined }))}
                    style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", minWidth: 100 }}
                  >
                    <option value="">全部年级</option>
                    {gradeOptions.map(g => <option key={g} value={g}>{g}</option>)}
                  </select>

                  <select
                    value={filters.target_job || ""}
                    onChange={e => setFilters(prev => ({ ...prev, target_job: e.target.value || undefined }))}
                    style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", minWidth: 140 }}
                  >
                    <option value="">全部岗位</option>
                    {targetJobOptions.map(j => <option key={j} value={j}>{j}</option>)}
                  </select>

                  <select
                    value={filters.report_status || ""}
                    onChange={e => setFilters(prev => ({ ...prev, report_status: e.target.value || undefined }))}
                    style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", minWidth: 120 }}
                  >
                    <option value="">全部状态</option>
                    {reportStatusOptions.slice(1).map(s => <option key={s} value={s}>{s}</option>)}
                  </select>

                  <select
                    value={selectedScoreRange}
                    onChange={e => handleScoreRangeChange(Number(e.target.value))}
                    style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", minWidth: 120 }}
                  >
                    {scoreRangeOptions.map((opt, idx) => (
                      <option key={idx} value={idx}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {studentReports.length > 0 ? (
                  <div style={{ overflowX: "auto" }}>
                    <table className="teacher-dashboard__table">
                      <thead>
                        <tr>
                          <th>学生</th>
                          <th>专业</th>
                          <th>年级</th>
                          <th>目标岗位</th>
                          <th>匹配度</th>
                          <th>报告状态</th>
                          <th>最近分析</th>
                          <th>跟进状态</th>
                        </tr>
                      </thead>
                      <tbody>
                        {studentReports.map((s) => {
                          const sc = statusColor(s.report_status);
                          const fc = statusColor(s.followup_status);
                          return (
                            <tr key={s.student_id}>
                              <td><strong>{s.name}</strong></td>
                              <td>{s.major || "-"}</td>
                              <td>{s.grade || "-"}</td>
                              <td>{s.target_job || s.career_goal || "-"}</td>
                              <td>{s.match_score > 0 ? `${s.match_score} 分` : "-"}</td>
                              <td>
                                <span style={{
                                  padding: "2px 8px", borderRadius: 12, fontSize: "0.75rem", fontWeight: 600,
                                  background: sc.bg, color: sc.color,
                                }}>
                                  {s.report_status}
                                </span>
                              </td>
                              <td style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>
                                {s.last_analysis_time ? new Date(s.last_analysis_time).toLocaleDateString("zh-CN") : "-"}
                              </td>
                              <td>
                                <span style={{
                                  padding: "2px 8px", borderRadius: 12, fontSize: "0.75rem", fontWeight: 600,
                                  background: fc.bg, color: fc.color,
                                }}>
                                  {s.followup_status}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>
                    {allReports.length === 0 ? "暂无学生数据" : "没有符合筛选条件的学生"}
                  </div>
                )}
              </div>

              <div className="teacher-dashboard__card">
                <h2>匹配分数分布</h2>
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
          </>
        )}
      </div>
    </div>
  );
}

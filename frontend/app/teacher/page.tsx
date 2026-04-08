"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: "🏠" },
  { href: "/teacher/reports", label: "学生报告查看", icon: "📋" },
  { href: "/teacher/overview", label: "班级数据概览", icon: "📊" },
  { href: "/teacher/advice", label: "指导建议", icon: "💬" }
];

const studentReports = [
  { id: 1, name: "陈同学", target: "产品经理", matchScore: 85.6, status: "已完成" },
  { id: 2, name: "王同学", target: "UI设计师", matchScore: 78.3, status: "已完成" },
  { id: 3, name: "李同学", target: "数据分析师", matchScore: 91.2, status: "已完成" },
  { id: 4, name: "张同学", target: "市场营销专员", matchScore: 72.8, status: "进行中" },
  { id: 5, name: "赵同学", target: "运营专员", matchScore: 88.1, status: "已完成" },
  { id: 6, name: "刘同学", target: "项目经理", matchScore: 69.5, status: "进行中" }
];

const matchDistribution = [
  { name: "90分以上", count: 8 },
  { name: "80-89分", count: 15 },
  { name: "70-79分", count: 12 },
  { name: "60-69分", count: 6 },
  { name: "60分以下", count: 3 }
];

export default function TeacherPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

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
            <span className="sidebar-drawer__link-icon">🚪</span>
            退出登录
          </button>
        }
      />
      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单">☰</button>
          <span className="workspace-topbar__title">教师工作台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">教师</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="teacher-dashboard">
        <div className="teacher-dashboard__grid">
          <div className="teacher-dashboard__card">
            <h2>学生报告查看</h2>
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
                  <tr key={s.id}>
                    <td><strong>{s.name}</strong></td>
                    <td>{s.target}</td>
                    <td>{s.matchScore} 分</td>
                    <td>
                      <span style={{
                        padding: "2px 8px",
                        borderRadius: 12,
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        background: s.status === "已完成" ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                        color: s.status === "已完成" ? "#0b7b72" : "#b76a09"
                      }}>
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="teacher-dashboard__card">
            <h2>班级数据概览</h2>
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
          </div>
        </div>
      </div>
    </div>
  );
}

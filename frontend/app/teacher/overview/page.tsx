"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { getMajorDistribution, type MajorDistributionItem } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

const COLORS = ["#173f8a", "#0f74da", "#12b3a6", "#f59e0b", "#ef4444", "#8b5cf6", "#6366f1", "#14b8a6"];

export default function TeacherOverviewPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [majorDistribution, setMajorDistribution] = useState<MajorDistributionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getMajorDistribution()
      .then((res) => setMajorDistribution(res))
      .catch((e) => console.error("Failed to load major distribution:", e))
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
          <span className="workspace-topbar__title">班级数据概览</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>岗位方向分布</h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : majorDistribution.length > 0 && majorDistribution.some(d => d.value > 0) ? (
          <div className="teacher-dashboard__card">
            <div className="teacher-dashboard__chart-area">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={majorDistribution}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }: { name?: string; percent?: number }) =>
                      `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {majorDistribution.map((_, index) => (
                      <Cell key={String(index)} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <div className="teacher-dashboard__card">
            <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>暂无专业分布数据</div>
          </div>
        )}
      </div>
    </div>
  );
}

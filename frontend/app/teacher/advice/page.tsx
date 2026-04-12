"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getTeacherAdvice, type TeacherAdviceItem } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

export default function TeacherAdvicePage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [adviceItems, setAdviceItems] = useState<TeacherAdviceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getTeacherAdvice()
      .then((res) => setAdviceItems(res))
      .catch((e) => console.error("Failed to load advice:", e))
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
          <span className="workspace-topbar__title">指导建议</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>指导建议</h1>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : adviceItems.length > 0 ? (
          <div className="history-list">
            {adviceItems.map((item) => (
              <div key={`${item.student_id}-${item.target_job}`} className="history-item">
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <p className="history-item__title" style={{ margin: 0 }}>
                      {item.name} — {item.target_job}
                    </p>
                    {item.match_score > 0 && (
                      <span style={{
                        padding: "1px 8px",
                        borderRadius: 10,
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        background: item.match_score >= 80 ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                        color: item.match_score >= 80 ? "#0b7b72" : "#b76a09",
                      }}>
                        {item.match_score} 分
                      </span>
                    )}
                  </div>
                  <p className="history-item__desc">{item.advice}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>暂无指导建议</div>
        )}
      </div>
    </div>
  );
}

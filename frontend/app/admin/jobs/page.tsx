"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import Link from "next/link";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: "🏠" },
  { href: "/admin/users", label: "用户管理", icon: "👥" },
  { href: "/admin/stats", label: "数据统计", icon: "📊" },
  { href: "/admin/jobs", label: "岗位管理", icon: "💼" },
  { href: "/admin/system", label: "系统监控", icon: "⚙️" }
];

const jobList = [
  { id: 1, name: "产品经理", industry: "互联网", count: 156 },
  { id: 2, name: "UI设计师", industry: "互联网", count: 142 },
  { id: 3, name: "运营专员", industry: "新媒体", count: 138 },
  { id: 4, name: "数据分析师", industry: "金融科技", count: 125 },
  { id: 5, name: "人力资源专员", industry: "企业服务", count: 120 },
  { id: 6, name: "项目经理", industry: "信息技术", count: 180 },
  { id: 7, name: "内容策划", industry: "内容平台", count: 108 },
  { id: 8, name: "金融分析师", industry: "金融", count: 112 },
  { id: 9, name: "教育培训师", industry: "教育科技", count: 95 },
  { id: 10, name: "市场策划", industry: "消费品", count: 96 }
];

const roleLabels: Record<string, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员"
};

export default function AdminJobsPage() {
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
        navItems={adminNavItems}
        label="管理功能"
        footer={
          <button className="sidebar-drawer__link" onClick={handleLogout}
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
          <span className="workspace-topbar__title">岗位管理</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>岗位数据管理</h2>
        <div className="admin-dashboard__card">
          <table className="admin-user-table">
            <thead>
              <tr><th>岗位名称</th><th>所属行业</th><th>数据条数</th></tr>
            </thead>
            <tbody>
              {jobList.map((j) => (
                <tr key={j.id}>
                  <td><strong>{j.name}</strong></td>
                  <td>{j.industry}</td>
                  <td>{j.count} 条</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

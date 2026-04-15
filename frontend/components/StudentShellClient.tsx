"use client";

import { useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";

const studentNavItems = [
  { href: "/student", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/student/profile", label: "我的能力分析", icon: <Icon name="chart" size={18} /> },
  { href: "/student/recommended", label: "推荐岗位", icon: <Icon name="briefcase" size={18} /> },
  { href: "/student/matching", label: "岗位匹配分析", icon: <Icon name="target" size={18} /> },
  { href: "/student/path", label: "职业路径规划", icon: <Icon name="trending-up" size={18} /> },
  { href: "/student/report", label: "完整报告", icon: <Icon name="file" size={18} /> },
  { href: "/student/jobs", label: "岗位探索", icon: <Icon name="search" size={18} /> },
  { href: "/student/history", label: "历史记录", icon: <Icon name="clock" size={18} /> },
];

export function StudentShellClient({ title, children }: { title: string; children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [roleLabel, setRoleLabel] = useState("同学");
  const router = useRouter();

  useEffect(() => {
    const role = localStorage.getItem("user_role");
    if (role === "teacher") setRoleLabel("教师");
    else if (role === "admin") setRoleLabel("管理员");
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  return (
    <div className="workspace-bg">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={studentNavItems}
        label="学生功能"
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
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单">
            <Icon name="menu" size={20} />
          </button>
          <span className="workspace-topbar__title">{title}</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">{roleLabel}</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      {children}
    </div>
  );
}

"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getJobsList, type JobListItem } from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

export default function AdminJobsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getJobsList(0, 100)
      .then((res) => {
        setJobs(res.items);
        setTotal(res.total);
      })
      .catch((e) => console.error("Failed to load jobs:", e))
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
        navItems={adminNavItems}
        label="管理功能"
        footer={
          <button className="sidebar-drawer__link" onClick={handleLogout}
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
          <span className="workspace-topbar__title">岗位管理</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>
          岗位数据管理
          <span style={{ fontSize: "0.875rem", fontWeight: 400, color: "var(--subtle)", marginLeft: 8 }}>
            共 {total} 个岗位画像
          </span>
        </h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <div className="admin-dashboard__card">
            <table className="admin-user-table">
              <thead>
                <tr><th>岗位编码</th><th>岗位名称</th><th>核心技能</th></tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.job_code}>
                    <td><code style={{ fontSize: "0.8125rem" }}>{j.job_code}</code></td>
                    <td><strong>{j.title}</strong></td>
                    <td>{(j.skills || []).slice(0, 4).join("、")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

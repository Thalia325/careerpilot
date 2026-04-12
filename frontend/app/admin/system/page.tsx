"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getSystemHealth, type SystemHealth } from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

export default function AdminSystemPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getSystemHealth()
      .then((res) => setHealth(res))
      .catch((e) => console.error("Failed to load system health:", e))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const formatTime = (iso: string) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleString("zh-CN");
  };

  return (
    <div className="workspace-bg">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={adminNavItems}
        label="管理功能"
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
          <span className="workspace-topbar__title">系统监控</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>系统监控</h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : health ? (
          <div className="admin-dashboard__card">
            <div style={{ padding: 24, display: "grid", gap: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>系统运行状态</span>
                <span style={{
                  padding: "2px 12px",
                  borderRadius: 12,
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  background: health.status === "healthy" ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                  color: health.status === "healthy" ? "#0b7b72" : "#b76a09",
                }}>
                  {health.status === "healthy" ? "正常" : "异常"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>数据库连接</span>
                <span style={{ fontSize: "0.9375rem", fontWeight: 600, color: health.database === "connected" ? "#0b7b72" : "#ef4444" }}>
                  {health.database === "connected" ? "已连接" : "连接失败"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>API 响应时间</span>
                <span style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{health.api_response_ms} ms</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>最后检测时间</span>
                <span style={{ fontSize: "0.9375rem" }}>{formatTime(health.last_check)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0" }}>
                <span style={{ fontSize: "0.9375rem", color: "var(--subtle)" }}>系统版本</span>
                <span style={{ fontSize: "0.9375rem" }}>v{health.version}</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>无法获取系统状态</div>
        )}
      </div>
    </div>
  );
}

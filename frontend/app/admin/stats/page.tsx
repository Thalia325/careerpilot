"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { formatShortDate } from "@/lib/format";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import {
  getAdminStatsOverview,
  getAdminStatsTrends,
  getAdminStatsWeekly,
  type AdminStatsOverview,
  type TrendDataPoint,
  type WeeklyDataPoint,
} from "@/lib/api";

const adminNavItems = [
  { href: "/admin", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/admin/users", label: "用户管理", icon: <Icon name="users" size={18} /> },
  { href: "/admin/stats", label: "数据统计", icon: <Icon name="chart" size={18} /> },
  { href: "/admin/jobs", label: "岗位管理", icon: <Icon name="briefcase" size={18} /> },
  { href: "/admin/system", label: "系统监控", icon: <Icon name="clipboard" size={18} /> },
];

type TimeRange = 7 | 14 | 30;
const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: 7, label: "近 7 天" },
  { value: 14, label: "近 14 天" },
  { value: 30, label: "近 30 天" },
];

function formatDateLabel(dateStr: string): string {
  return formatShortDate(dateStr + "T00:00:00");
}

export default function AdminStatsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [stats, setStats] = useState<AdminStatsOverview | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [weeklyData, setWeeklyData] = useState<WeeklyDataPoint[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>(14);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, trendsRes, weeklyRes] = await Promise.all([
        getAdminStatsOverview(),
        getAdminStatsTrends(timeRange),
        getAdminStatsWeekly(8),
      ]);
      setStats(statsRes);
      setTrendData(trendsRes);
      setWeeklyData(weeklyRes);
    } catch (e) {
      console.error("Failed to load stats:", e);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => { load(); }, [load]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const trendTotals = trendData.reduce(
    (acc, d) => ({ reports: acc.reports + d.reports, users: acc.users + d.users }),
    { reports: 0, users: 0 },
  );

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
          <span className="workspace-topbar__title">数据统计</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>数据统计看板</h2>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
        ) : (
          <>
            {/* Overview Cards */}
            <div className="admin-dashboard__stats" style={{ marginBottom: 24 }}>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">注册用户</span>
                <div className="admin-stat-card__value">{stats?.total_users ?? 0}</div>
                <span className="admin-stat-card__change">全部角色</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">职位画像</span>
                <div className="admin-stat-card__value">{stats?.total_positions ?? 0}</div>
                <span className="admin-stat-card__change">已入库岗位</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">累计报告</span>
                <div className="admin-stat-card__value">{stats?.total_reports ?? 0}</div>
                <span className="admin-stat-card__change">全部报告</span>
              </div>
              <div className="admin-stat-card">
                <span className="admin-stat-card__label">累计匹配</span>
                <div className="admin-stat-card__value">{stats?.total_matches ?? 0}</div>
                <span className="admin-stat-card__change">平均 {stats?.avg_match_score ?? 0} 分</span>
              </div>
            </div>

            {/* Daily Trend Chart */}
            <div className="admin-dashboard__card" style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
                <div>
                  <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: 0 }}>每日趋势</h2>
                  <span style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>
                    时间范围：{TIME_RANGE_OPTIONS.find(o => o.value === timeRange)?.label} | 时区：Asia/Shanghai (UTC+8)
                  </span>
                </div>
                <div style={{ display: "flex", gap: 4 }}>
                  {TIME_RANGE_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setTimeRange(opt.value)}
                      style={{
                        padding: "4px 12px",
                        fontSize: "0.8rem",
                        borderRadius: 4,
                        border: timeRange === opt.value ? "1px solid #173f8a" : "1px solid #d1d5db",
                        background: timeRange === opt.value ? "#173f8a" : "#fff",
                        color: timeRange === opt.value ? "#fff" : "#374151",
                        cursor: "pointer",
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              {trendData.length > 0 ? (
                <>
                  <div style={{ fontSize: "0.85rem", color: "var(--subtle)", marginBottom: 8 }}>
                    区间汇总：{trendTotals.users} 新用户，{trendTotals.reports} 新报告
                  </div>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={trendData.map(d => ({ ...d, dateLabel: formatDateLabel(d.date) }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="dateLabel" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip labelFormatter={(label) => `日期：${label}`} />
                      <Bar dataKey="users" fill="#173f8a" name="新用户" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="reports" fill="#12b3a6" name="新报告" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </>
              ) : (
                <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>
                  暂无趋势数据（时间范围：{TIME_RANGE_OPTIONS.find(o => o.value === timeRange)?.label}）
                </div>
              )}
            </div>

            {/* Weekly Trend Chart */}
            <div className="admin-dashboard__card">
              <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 16px" }}>周度使用趋势</h2>
              {weeklyData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={weeklyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="reports" fill="#173f8a" name="报告数" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="matches" fill="#12b3a6" name="匹配数" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: "center", padding: 48, color: "var(--subtle)" }}>暂无周度数据</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

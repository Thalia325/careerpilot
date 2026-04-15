"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getTeacherAdvice, updateFollowupStatus, type TeacherAdviceItem } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "指导建议", icon: <Icon name="chat" size={18} /> },
];

const followupStatusOptions = [
  { key: "pending", label: "待跟进" },
  { key: "in_progress", label: "跟进中" },
  { key: "read", label: "已读" },
  { key: "communicated", label: "已沟通" },
  { key: "review", label: "需复盘" },
  { key: "completed", label: "已完成" },
  { key: "overdue", label: "已逾期" },
];

export default function TeacherAdvicePage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [adviceItems, setAdviceItems] = useState<TeacherAdviceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [followupDate, setFollowupDate] = useState("");
  const [saving, setSaving] = useState(false);
  const router = useRouter();

  useEffect(() => {
    getTeacherAdvice()
      .then((res) => setAdviceItems(res))
      .catch((e) => console.error("Failed to load advice:", e))
      .finally(() => setLoading(false));
  }, []);

  const handleFollowup = async (studentId: number, statusValue: string) => {
    setSaving(true);
    try {
      await updateFollowupStatus(studentId, {
        status: statusValue,
        next_followup_date: followupDate || undefined,
        teacher_notes: notes || undefined,
      });
      setNotes("");
      setFollowupDate("");
      setExpandedId(null);
    } catch (e) {
      console.error("Failed to update followup:", e);
    } finally {
      setSaving(false);
    }
  };

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
              <div key={`${item.student_id}-${item.target_job}`} style={{ marginBottom: 12 }}>
                <div className="history-item" style={{ cursor: "pointer" }} onClick={() => setExpandedId(expandedId === item.student_id ? null : item.student_id)}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <p className="history-item__title" style={{ margin: 0 }}>
                        {item.name} — {item.target_job}
                      </p>
                      {item.match_score > 0 && (
                        <span style={{
                          padding: "1px 8px", borderRadius: 10, fontSize: "0.6875rem", fontWeight: 600,
                          background: item.match_score >= 80 ? "rgba(11, 123, 114, 0.1)" : "rgba(245, 158, 11, 0.1)",
                          color: item.match_score >= 80 ? "#0b7b72" : "#b76a09",
                        }}>
                          {item.match_score} 分
                        </span>
                      )}
                    </div>
                    <p className="history-item__desc">{item.advice}</p>
                  </div>
                  <span style={{ fontSize: "0.8rem", color: "var(--subtle)" }}>
                    {expandedId === item.student_id ? "收起 ▲" : "跟进 ▼"}
                  </span>
                </div>

                {expandedId === item.student_id && item.student_id !== 0 && (
                  <div style={{ background: "#f8fafc", borderRadius: 8, padding: 16, marginTop: 4 }}>
                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: 4 }}>教师备注</label>
                      <textarea
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                        placeholder="输入指导建议或跟进备注..."
                        style={{ width: "100%", minHeight: 60, padding: 8, borderRadius: 6, border: "1px solid #d1d5db", fontSize: "0.85rem", resize: "vertical" }}
                      />
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: 4 }}>下次跟进日期</label>
                      <input
                        type="date"
                        value={followupDate}
                        onChange={e => setFollowupDate(e.target.value)}
                        style={{
                          width: "100%",
                          minHeight: 44,
                          padding: "10px 12px",
                          borderRadius: 6,
                          border: "1px solid #d1d5db",
                          fontSize: "0.85rem",
                          background: "#fff",
                        }}
                      />
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: 8 }}>跟进状态</label>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(96px, 1fr))", gap: 8 }}>
                        {followupStatusOptions.map(({ key, label }) => (
                          <button
                            key={key}
                            onClick={() => handleFollowup(item.student_id, key)}
                            disabled={saving}
                            style={{
                              width: "100%",
                              minHeight: 40,
                              padding: "8px 12px",
                              borderRadius: 6,
                              border: "1px solid #d1d5db",
                              background: "#fff",
                              color: "#13233f",
                              cursor: saving ? "not-allowed" : "pointer",
                              fontSize: "0.8rem",
                              fontWeight: 600,
                              opacity: saving ? 0.6 : 1,
                              boxShadow: "none",
                              filter: "none",
                              transform: "none",
                            }}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
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

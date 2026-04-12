"use client";

import { useState, useEffect, useCallback } from "react";
import { getStudentHistory, renameHistoryItem, type HistoryItem } from "@/lib/api";
import { Icon, type IconName } from "@/components/Icon";

function formatTime(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "刚刚";
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffHours < 24) return `${diffHours} 小时前`;
  if (diffDays < 7) return `${diffDays} 天前`;
  return d.toLocaleDateString("zh-CN");
}

const TYPE_ICON: Record<string, IconName> = {
  report: "chart",
  matching: "target",
  path: "map",
  chat: "chat",
};

const TYPE_LABEL: Record<string, string> = {
  report: "报告",
  matching: "匹配",
  path: "路径",
  chat: "对话",
};

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const loadHistory = useCallback(async () => {
    try {
      const res = await getStudentHistory();
      setItems(res);
    } catch (e) {
      console.error("Failed to load history:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const startEdit = (item: HistoryItem) => {
    setEditingId(item.id);
    setEditValue(item.title);
  };

  const saveEdit = async (item: HistoryItem) => {
    const trimmed = editValue.trim();
    if (!trimmed || trimmed === item.title) {
      setEditingId(null);
      return;
    }
    try {
      await renameHistoryItem(item.type, item.ref_id, trimmed);
      setItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, title: trimmed } : i))
      );
    } catch (err) {
      console.error("Rename failed:", err);
    }
    setEditingId(null);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent, item: HistoryItem) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveEdit(item);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px" }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>历史记录</h1>
      {loading ? (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
      ) : items.length > 0 ? (
        <div className="history-list">
          {items.map((item) => (
            <div key={item.id} className="history-item" style={{ cursor: "default" }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: "1.1rem" }}><Icon name={TYPE_ICON[item.type] || "clipboard"} size={18} /></span>
                  <span style={{
                    padding: "2px 8px",
                    borderRadius: 6,
                    background: "rgba(15,116,218,0.06)",
                    color: "var(--brand)",
                    fontSize: "0.6875rem",
                    fontWeight: 600,
                  }}>
                    {TYPE_LABEL[item.type] || item.type}
                  </span>
                </div>

                {editingId === item.id ? (
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => handleEditKeyDown(e, item)}
                      onBlur={() => saveEdit(item)}
                      autoFocus
                      style={{
                        flex: 1,
                        padding: "6px 10px",
                        borderRadius: 8,
                        border: "2px solid var(--brand-2)",
                        fontSize: "0.9375rem",
                        outline: "none",
                      }}
                    />
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <p className="history-item__title" style={{ margin: 0 }}>{item.title}</p>
                    <button
                      onClick={() => startEdit(item)}
                      title="重命名"
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "var(--subtle)",
                        fontSize: "0.75rem",
                        padding: "2px 6px",
                        borderRadius: 4,
                        minHeight: 24,
                        minWidth: 24,
                        opacity: 0.5,
                        transition: "opacity 0.2s",
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.opacity = "1"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.opacity = "0.5"; }}
                    >
                      <Icon name="edit" size={14} />
                    </button>
                  </div>
                )}

                <p className="history-item__desc">{item.desc}</p>
              </div>
              <span className="history-item__time">{formatTime(item.time)}</span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>
          暂无历史记录，开始使用系统后将自动记录
        </div>
      )}
    </div>
  );
}

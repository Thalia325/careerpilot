"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getStudentHistory, renameHistoryItem, type HistoryItem } from "@/lib/api";
import { Icon, type IconName } from "@/components/Icon";

const ALL_TYPES = ["upload", "profile", "matching", "path", "report", "chat", "feedback"] as const;

const TYPE_ICON: Record<string, IconName> = {
  upload: "upload",
  profile: "chart",
  matching: "target",
  path: "map",
  report: "clipboard",
  chat: "chat",
  feedback: "star",
};

const TYPE_LABEL: Record<string, string> = {
  upload: "上传",
  profile: "画像",
  matching: "匹配",
  path: "路径",
  report: "报告",
  chat: "对话",
  feedback: "反馈",
};

const TYPE_COLOR: Record<string, string> = {
  upload: "rgba(34,139,34,0.06)",
  profile: "rgba(128,0,128,0.06)",
  matching: "rgba(15,116,218,0.06)",
  path: "rgba(255,140,0,0.06)",
  report: "rgba(0,128,128,0.06)",
  chat: "rgba(100,100,100,0.06)",
  feedback: "rgba(220,20,60,0.06)",
};

const TYPE_TEXT_COLOR: Record<string, string> = {
  upload: "#228B22",
  profile: "#800080",
  matching: "var(--brand)",
  path: "#D2691E",
  report: "#008B8B",
  chat: "#666",
  feedback: "#DC143C",
};

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

function getHistoryItemLink(item: HistoryItem): string {
  switch (item.type) {
    case "upload":
      return "/student/upload";
    case "profile":
      return `/student/profile?version=${item.ref_id}`;
    case "report":
      return `/results/${item.ref_id}`;
    case "matching":
      return `/student/matching?history=${item.id}`;
    case "path":
      return `/student/path?history=${item.id}`;
    case "chat":
      return `/student?history=${item.id}`;
    case "feedback":
      return "/student";
    default:
      return "/student";
  }
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeType, setActiveType] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const loadHistory = useCallback(async (type: string | null) => {
    setLoading(true);
    try {
      const res = await getStudentHistory(type || undefined);
      setItems(res);
    } catch (e) {
      console.error("Failed to load history:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(activeType); }, [loadHistory, activeType]);

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

  const renderItemContent = (item: HistoryItem) => (
    <>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: "1.1rem" }}><Icon name={TYPE_ICON[item.type] || "clipboard"} size={18} /></span>
          <span style={{
            padding: "2px 8px",
            borderRadius: 6,
            background: TYPE_COLOR[item.type] || "rgba(15,116,218,0.06)",
            color: TYPE_TEXT_COLOR[item.type] || "var(--brand)",
            fontSize: "0.6875rem",
            fontWeight: 600,
          }}>
            {TYPE_LABEL[item.type] || item.type}
          </span>
          {item.profile_version_id && (
            <span style={{
              padding: "1px 6px",
              borderRadius: 4,
              background: "rgba(128,0,128,0.06)",
              color: "#800080",
              fontSize: "0.625rem",
            }}>
              画像v{item.profile_version_id}
            </span>
          )}
        </div>

        {editingId === item.id ? (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ display: "flex", gap: 8, alignItems: "center" }}
          >
            <input
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => handleEditKeyDown(e, item)}
              onBlur={() => saveEdit(item)}
              onClick={(e) => e.stopPropagation()}
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
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                startEdit(item);
              }}
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
        {item.type === "profile" && item.uploaded_file_ids && item.uploaded_file_ids.length > 0 && (
          <p style={{ margin: "4px 0 0", fontSize: "0.75rem", color: "var(--subtle)" }}>
            来源文件 ID: {item.uploaded_file_ids.join(", ")}
          </p>
        )}
      </div>
      <span className="history-item__time">{formatTime(item.time)}</span>
    </>
  );

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "24px" }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 16px" }}>历史记录</h1>

      {/* Category filter tabs */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
        <button
          onClick={() => setActiveType(null)}
          style={{
            padding: "4px 14px",
            borderRadius: 20,
            border: activeType === null ? "2px solid var(--brand)" : "1px solid #ddd",
            background: activeType === null ? "rgba(15,116,218,0.08)" : "#fff",
            color: activeType === null ? "var(--brand)" : "#666",
            fontSize: "0.8125rem",
            fontWeight: activeType === null ? 600 : 400,
            cursor: "pointer",
          }}
        >
          全部
        </button>
        {ALL_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setActiveType(t)}
            style={{
              padding: "4px 14px",
              borderRadius: 20,
              border: activeType === t ? `2px solid ${TYPE_TEXT_COLOR[t]}` : "1px solid #ddd",
              background: activeType === t ? TYPE_COLOR[t] : "#fff",
              color: activeType === t ? TYPE_TEXT_COLOR[t] : "#666",
              fontSize: "0.8125rem",
              fontWeight: activeType === t ? 600 : 400,
              cursor: "pointer",
            }}
          >
            {TYPE_LABEL[t]}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
      ) : items.length > 0 ? (
        <div className="history-list">
          {items.map((item) => {
            const isClickable = item.type !== "feedback";
            if (isClickable) {
              return (
                <Link
                  key={item.id}
                  href={getHistoryItemLink(item)}
                  className="history-item"
                  style={{ cursor: "pointer", textDecoration: "none", color: "inherit", display: "block" }}
                >
                  {renderItemContent(item)}
                </Link>
              );
            }
            return (
              <div
                key={item.id}
                className="history-item"
                style={{ cursor: "default", display: "block" }}
              >
                {renderItemContent(item)}
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>
          {activeType ? `暂无${TYPE_LABEL[activeType] || ""}记录` : "暂无历史记录，开始使用系统后将自动记录"}
        </div>
      )}
    </div>
  );
}

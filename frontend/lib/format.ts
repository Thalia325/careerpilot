/**
 * Shared formatting utilities for consistent time, status, and error display (US-030).
 */

/** Application timezone label for display */
export const APP_TIMEZONE_LABEL = "Asia/Shanghai (UTC+8)";

/**
 * Format a timestamp string (ISO8601) into a consistent local display.
 * Shows "YYYY/MM/DD HH:mm" in zh-CN locale.
 */
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "-";
    return d.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Shanghai",
    });
  } catch {
    return "-";
  }
}

/**
 * Format a timestamp into a short date (MM/DD) for chart labels.
 */
export function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "-";
    return `${d.getMonth() + 1}/${d.getDate()}`;
  } catch {
    return "-";
  }
}

/**
 * Format a timestamp as relative time for recent events ("刚刚", "5分钟前", etc.).
 * Falls back to formatTime for older events.
 */
export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "-";
    const diff = Date.now() - d.getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return "刚刚";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}天前`;
    return formatTime(iso);
  } catch {
    return "-";
  }
}

/** Report status display mapping */
export const REPORT_STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: "草稿", color: "#6b7280" },
  generating: { label: "生成中", color: "#2563eb" },
  completed: { label: "已完成", color: "#16a34a" },
  failed: { label: "生成失败", color: "#dc2626" },
};

/** Analysis step status display */
export const ANALYSIS_STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "#6b7280" },
  running: { label: "进行中", color: "#2563eb" },
  completed: { label: "已完成", color: "#16a34a" },
  failed: { label: "失败", color: "#dc2626" },
};

/** Teacher follow-up status display */
export const FOLLOWUP_STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: "待跟进", color: "#6b7280" },
  in_progress: { label: "跟进中", color: "#2563eb" },
  read: { label: "已读", color: "#0891b2" },
  communicated: { label: "已沟通", color: "#7c3aed" },
  review: { label: "需复盘", color: "#d97706" },
  completed: { label: "已完成", color: "#16a34a" },
  overdue: { label: "已逾期", color: "#dc2626" },
};

/** Get status label, falling back to the raw key */
export function getStatusLabel(map: Record<string, { label: string; color: string }>, key: string): string {
  return map[key]?.label ?? key;
}

/** Get status color, falling back to gray */
export function getStatusColor(map: Record<string, { label: string; color: string }>, key: string): string {
  return map[key]?.color ?? "#6b7280";
}

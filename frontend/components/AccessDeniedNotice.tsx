"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Icon } from "@/components/Icon";

const roleLabels: Record<string, string> = {
  student: "学生",
  teacher: "教师",
  admin: "管理员",
};

/**
 * Shows a dismissible banner when the user is redirected due to cross-role access.
 * Reads the `notice=access_denied` search param set by middleware.
 */
export function AccessDeniedNotice() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (searchParams.get("notice") === "access_denied") {
      setVisible(true);
    }
  }, [searchParams]);

  if (!visible) return null;

  const userRole = typeof window !== "undefined"
    ? localStorage.getItem("user_role") || ""
    : "";

  const roleLabel = roleLabels[userRole] || userRole;

  const handleDismiss = () => {
    setVisible(false);
    // Clean the URL query param without full reload
    router.replace(pathname);
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 16px",
        margin: "8px 16px",
        background: "var(--color-warning-bg)",
        borderRadius: "var(--radius-sm)",
        fontSize: "var(--text-small)",
        color: "var(--color-warning)",
        border: "1px solid rgba(234, 88, 12, 0.2)",
      }}
    >
      <Icon name="alert-circle" size={18} />
      <span style={{ flex: 1 }}>
        您没有权限访问该页面，已为您跳转到{roleLabel}首页。
      </span>
      <button
        onClick={handleDismiss}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "var(--color-warning)",
          fontSize: 16,
          lineHeight: 1,
          padding: 4,
        }}
        aria-label="关闭提示"
      >
        ×
      </button>
    </div>
  );
}

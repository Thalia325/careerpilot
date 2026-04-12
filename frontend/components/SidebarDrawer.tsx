"use client";

import { ReactNode, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Icon } from "./Icon";

type NavItem = {
  href: string;
  label: string;
  icon: ReactNode;
  subtitle?: string;
};

type SidebarDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  navItems: NavItem[];
  label?: string;
  footer?: ReactNode;
};

export function SidebarDrawer({ isOpen, onClose, navItems, label, footer }: SidebarDrawerProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleNav = useCallback((href: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    onClose();
    if (pathname === href) return;
    const isOnHomePage = ["/student", "/teacher", "/admin"].includes(pathname);
    if (isOnHomePage) {
      router.push(href);
    } else {
      router.replace(href);
    }
  }, [onClose, pathname, router]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [isOpen, onClose]);

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <>
      <div
        className={`sidebar-overlay ${isOpen ? "is-open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`sidebar-drawer ${isOpen ? "is-open" : ""}`} role="navigation" aria-label={label || "主导航"}>
        <div className="sidebar-drawer__header">
          <div className="sidebar-drawer__brand">
            <span className="sidebar-drawer__brand-logo">CP</span>
            <span className="sidebar-drawer__brand-text">
              <strong>职航智策</strong>
              <small>AI 职业规划助手</small>
            </span>
          </div>
          <button className="sidebar-drawer__close" onClick={onClose} aria-label="关闭菜单">
            <Icon name="close" size={16} />
          </button>
        </div>
        <nav className="sidebar-drawer__nav">
          {label && <p className="sidebar-drawer__nav-label">{label}</p>}
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={`sidebar-drawer__link ${isActive(item.href) ? "active" : ""}`}
              onClick={handleNav(item.href)}
            >
              <span className="sidebar-drawer__link-icon">{item.icon}</span>
              <span>
                <span style={{ display: "block" }}>{item.label}</span>
                {item.subtitle && (
                  <span style={{ display: "block", fontSize: "0.6875rem", color: "var(--subtle)", fontWeight: 400, marginTop: 2 }}>
                    {item.subtitle}
                  </span>
                )}
              </span>
            </a>
          ))}
        </nav>
        {footer && <div className="sidebar-drawer__footer">{footer}</div>}
      </aside>
    </>
  );
}

type RoleShellProps = {
  title: string;
  navItems: NavItem[];
  navLabel?: string;
  children: ReactNode;
};

export function RoleShell({ title, navItems, navLabel, children }: RoleShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [roleLabel, setRoleLabel] = useState("");
  const router = useRouter();

  useEffect(() => {
    const role = localStorage.getItem("user_role");
    if (role === "teacher") setRoleLabel("教师");
    else if (role === "admin") setRoleLabel("管理员");
    else setRoleLabel("同学");
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
        navItems={navItems}
        label={navLabel}
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
            ☰
          </button>
          <span className="workspace-topbar__title">{title}</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">{roleLabel}</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div>
        {children}
      </div>
    </div>
  );
}

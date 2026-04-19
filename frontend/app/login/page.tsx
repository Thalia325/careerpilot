"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Icon } from "@/components/Icon";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

const roles = [
  { key: "student", label: "学生" },
  { key: "teacher", label: "教师" },
  { key: "admin", label: "管理员" }
] as const;

type RoleKey = typeof roles[number]["key"];

const roleRedirects: Record<RoleKey, string> = {
  student: "/student",
  teacher: "/teacher",
  admin: "/admin"
};

function setCookie(name: string, value: string, days: number = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Strict${secure}`;
}

export default function LoginPage() {
  const router = useRouter();
  const isDevelopment = process.env.NODE_ENV === "development";
  const [activeRole, setActiveRole] = useState<RoleKey>("student");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, role: activeRole })
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail || "登录失败，请检查用户名和密码";
        throw new Error(detail);
      }

      const data = await response.json();
      const token = data.token || data.access_token;

      if (!token) {
        throw new Error("登录响应缺少令牌");
      }

      const role = (data.role || activeRole) as RoleKey;

      localStorage.setItem("token", token);
      localStorage.setItem("user_role", role);
      if (data.user_id !== undefined && data.user_id !== null) {
        localStorage.setItem("user_id", String(data.user_id));
      }
      if (data.username) {
        localStorage.setItem("username", data.username);
      }
      localStorage.removeItem("chat_messages");
      setCookie("auth_token", token);
      setCookie("user_role", role);

      router.replace(roleRedirects[role]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录出错，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <span className="landing-hero-section__badge">CareerPilot</span>
          <h1>欢迎使用职航智策</h1>
          <p>AI 职业规划助手，助力你的职业发展</p>
        </div>

        <div className="login-tabs">
          {roles.map((r) => (
            <button
              key={r.key}
              className={`login-tab ${activeRole === r.key ? "active" : ""}`}
              onClick={() => { setActiveRole(r.key); setError(""); }}
              type="button"
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="login-card__body">
          <form onSubmit={handleLogin} className="login-form">
            {error && <div className="login-form__error">{error}</div>}

            <div>
              <label htmlFor="username">用户名</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="输入用户名"
                required
              />
            </div>

            <div>
              <label htmlFor="password">密码</label>
              <div className="password-field">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="输入密码"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="password-toggle"
                  tabIndex={-1}
                  aria-label={showPassword ? "隐藏密码" : "显示密码"}
                >
                  <Icon name={showPassword ? "eye" : "eye-off"} size={18} />
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`btn-primary login-form__submit ${loading ? "btn-loading" : ""}`}
            >
              <span className="btn-text">{loading ? "登录中..." : "登录"}</span>
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 16, fontSize: 14, color: "var(--color-text-secondary, #888)" }}>
            还没有账号？{" "}
            <Link href="/register" style={{ color: "var(--color-primary, #4f46e5)", textDecoration: "underline" }}>
              立即注册
            </Link>
          </p>

          {isDevelopment && (
            <div className="login-form__dev-note">
              <p>开发环境演示账号</p>
              <div className="login-form__dev-accounts">
                <div>学生：student_demo / demo123</div>
                <div>教师：teacher_demo / demo123</div>
                <div>管理员：admin_demo / demo123</div>
              </div>
              <button
                type="button"
                className="btn-primary"
                style={{ marginTop: "12px", width: "100%", background: "#555" }}
                onClick={() => {
                  setCookie("dev_bypass", "true");
                  setCookie("user_role", activeRole);
                  localStorage.setItem("token", "dev-bypass");
                  localStorage.setItem("user_role", activeRole);
                  localStorage.setItem("user_id", "dev-bypass");
                  localStorage.setItem("username", `dev-${activeRole}`);
                  localStorage.removeItem("chat_messages");
                  router.replace(roleRedirects[activeRole]);
                }}
              >
                开发模式直接进入（{roles.find(r => r.key === activeRole)?.label}）
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

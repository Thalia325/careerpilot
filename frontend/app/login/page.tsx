"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const isDevelopment = process.env.NODE_ENV === "development";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error("登录失败，请检查用户名和密码");
      }

      const data = await response.json();
      const token = data.token || data.access_token;

      if (!token) {
        throw new Error("登录响应缺少令牌");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("user_role", data.role || "student");

      const role = data.role || "student";
      const redirectPath =
        role === "teacher"
          ? "/teacher"
          : role === "admin"
            ? "/admin"
            : "/student/dashboard";

      router.push(redirectPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录出错，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing">
      <section className="landing-hero">
        <div className="landing-panel">
          <p className="eyebrow">登录入口</p>
          <h1>统一身份接入</h1>
          <p>使用您的账号登录 CareerPilot 职业规划系统</p>

          <form onSubmit={handleLogin} style={{ marginTop: "24px" }}>
            {error && (
              <div
                role="alert"
                style={{
                  padding: "12px 16px",
                  borderRadius: "12px",
                  background: "rgba(220, 38, 38, 0.12)",
                  color: "#dc2626",
                  marginBottom: "16px",
                  fontSize: "0.95rem"
                }}
              >
                {error}
              </div>
            )}

            <div style={{ marginBottom: "16px" }}>
              <label
                htmlFor="username"
                style={{
                  display: "block",
                  marginBottom: "8px",
                  fontWeight: 600,
                  fontSize: "0.95rem"
                }}
              >
                用户名
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="输入用户名"
                required
                aria-label="用户名输入框"
              />
            </div>

            <div style={{ marginBottom: "22px" }}>
              <label
                htmlFor="password"
                style={{
                  display: "block",
                  marginBottom: "8px",
                  fontWeight: 600,
                  fontSize: "0.95rem"
                }}
              >
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码"
                required
                aria-label="密码输入框"
              />
            </div>

            <button type="submit" disabled={loading} style={{ width: "100%" }}>
              {loading ? "登录中..." : "登录"}
            </button>
          </form>

          {isDevelopment && (
            <div
              style={{
                marginTop: "32px",
                paddingTop: "24px",
                borderTop: "1px solid rgba(214, 223, 238, 0.6)",
                fontSize: "0.9em",
                color: "#666"
              }}
            >
              <p style={{ marginTop: 0, fontWeight: 600 }}>
                开发环境演示账号（仅测试使用）：
              </p>
              <div className="plain-list">
                <div>学生端：student_demo / demo123</div>
                <div>教师端：teacher_demo / demo123</div>
                <div>管理端：admin_demo / demo123</div>
              </div>
            </div>
          )}
        </div>
        <div className="landing-side">
          <h2>快速进入</h2>
          <p style={{ color: "var(--subtle)", marginBottom: "18px" }}>
            或直接跳过登录流程，查看各角色演示：
          </p>
          <div className="plain-list">
            <a href="/student/dashboard">作为学生查看</a>
            <a href="/teacher">作为教师查看</a>
            <a href="/admin">作为管理员查看</a>
          </div>
        </div>
      </section>
    </div>
  );
}


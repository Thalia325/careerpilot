"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerAccount } from "@/lib/api";
import { Icon } from "@/components/Icon";

const roles = [
  { key: "student", label: "学生" },
  { key: "teacher", label: "教师" },
] as const;

type RoleKey = typeof roles[number]["key"];

const roleRedirects: Record<string, string> = {
  student: "/student",
  teacher: "/teacher",
  admin: "/admin",
};

function setCookie(name: string, value: string, days: number = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Strict${secure}`;
}

function validatePassword(p: string): string | null {
  if (p.length < 6) return "密码至少6位";
  if (!/[a-zA-Z]/.test(p)) return "密码必须包含英文字母";
  if (!/\d/.test(p)) return "密码必须包含数字";
  return null;
}

export default function RegisterPage() {
  const router = useRouter();
  const [activeRole, setActiveRole] = useState<RoleKey>("student");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [teacherCode, setTeacherCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (username.length < 3) {
      setError("账号至少3个字符");
      return;
    }

    const pwErr = validatePassword(password);
    if (pwErr) {
      setError(pwErr);
      return;
    }

    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }

    if (!fullName.trim()) {
      setError("请输入昵称");
      return;
    }

    if (!email.trim()) {
      setError("请输入邮箱");
      return;
    }

    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
      setError("邮箱格式不正确");
      return;
    }

    setLoading(true);

    try {
      const data = await registerAccount(
        username,
        password,
        fullName,
        activeRole,
        email.trim(),
        activeRole === "student" ? teacherCode.trim() : "",
      );
      const token = data.access_token;

      if (!token) {
        throw new Error("注册响应缺少令牌");
      }

      const role = (data.role || activeRole) as string;

      localStorage.setItem("token", token);
      localStorage.setItem("user_role", role);
      localStorage.setItem("user_id", String(data.user_id));
      localStorage.setItem("username", data.username);
      localStorage.removeItem("chat_messages");
      setCookie("auth_token", token);
      setCookie("user_role", role);

      router.replace(roleRedirects[role] || "/student");
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message || "注册失败，请重试");
      } else {
        setError("注册出错，请重试");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <span className="landing-hero-section__badge">CareerPilot</span>
          <h1>创建账号</h1>
          <p>注册职航智策，开始你的职业规划之旅</p>
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
          <form onSubmit={handleRegister} className="login-form">
            {error && <div className="login-form__error">{error}</div>}

            <div>
              <label htmlFor="username">账号</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="自定义账号（至少3个字符）"
                required
              />
            </div>

            <div>
              <label htmlFor="fullName">昵称</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="你的昵称"
                required
              />
            </div>

            <div>
              <label htmlFor="email">{activeRole === "teacher" ? "绑定邮箱" : "邮箱"}</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={
                  activeRole === "teacher"
                    ? "建议填写常用邮箱，便于学生通过邮箱绑定你"
                    : "用于账号通知和绑定老师"
                }
                required
              />
            </div>

            {activeRole === "student" && (
              <div>
                <label htmlFor="teacherCode">所属老师</label>
                <input
                  id="teacherCode"
                  type="text"
                  value={teacherCode}
                  onChange={(e) => setTeacherCode(e.target.value)}
                  placeholder="填写老师账号或绑定邮箱，可稍后由管理员绑定"
                />
              </div>
            )}

            <div>
              <label htmlFor="password">密码</label>
              <div className="password-field">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="至少6位，需包含英文和数字"
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

            <div>
              <label htmlFor="confirmPassword">确认密码</label>
              <div className="password-field">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="再次输入密码"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(v => !v)}
                  className="password-toggle"
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? "隐藏密码" : "显示密码"}
                >
                  <Icon name={showConfirmPassword ? "eye" : "eye-off"} size={18} />
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`btn-primary login-form__submit ${loading ? "btn-loading" : ""}`}
            >
              <span className="btn-text">{loading ? "注册中..." : "注册"}</span>
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 16, fontSize: 14, color: "var(--color-text-secondary, #888)" }}>
            已有账号？{" "}
            <Link href="/login" style={{ color: "var(--color-primary, #4f46e5)", textDecoration: "underline" }}>
              去登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

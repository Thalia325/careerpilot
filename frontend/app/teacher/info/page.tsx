"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { Icon } from "@/components/Icon";
import { getTeacherInfo, updateTeacherInfo, changePassword, type TeacherInfo, type TeacherInfoInput } from "@/lib/api";

const teacherNavItems = [
  { href: "/teacher", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/teacher/info", label: "个人信息", icon: <Icon name="user" size={18} /> },
  { href: "/teacher/reports", label: "学生报告查看", icon: <Icon name="clipboard" size={18} /> },
  { href: "/teacher/overview", label: "班级数据概览", icon: <Icon name="chart" size={18} /> },
  { href: "/teacher/advice", label: "状态跟进", icon: <Icon name="chat" size={18} /> },
  { href: "/teacher/roster", label: "花名册管理", icon: <Icon name="users" size={18} /> },
];

const emptyForm: TeacherInfoInput = {
  full_name: "",
  email: "",
  department: "",
  title: "",
};

export default function TeacherInfoPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [info, setInfo] = useState<TeacherInfo | null>(null);
  const [form, setForm] = useState<TeacherInfoInput>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pwForm, setPwForm] = useState({ old_password: "", new_password: "", confirm: "" });
  const [pwMessage, setPwMessage] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwSaving, setPwSaving] = useState(false);
  const [showPw, setShowPw] = useState({ old: false, new: false, confirm: false });
  const router = useRouter();

  useEffect(() => {
    getTeacherInfo()
      .then((data) => {
        setInfo(data);
        setForm({
          full_name: data.full_name || "",
          email: data.email || "",
          department: data.department || "",
          title: data.title || "",
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : "加载教师信息失败"))
      .finally(() => setLoading(false));
  }, []);

  const updateField = (key: keyof TeacherInfoInput, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setMessage("");
    setError("");
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!form.full_name.trim()) {
      setError("请输入姓名");
      return;
    }
    if (form.email.trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) {
      setError("邮箱格式不正确");
      return;
    }

    setSaving(true);
    try {
      const updated = await updateTeacherInfo({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        department: form.department.trim(),
        title: form.title.trim(),
      });
      setInfo(updated);
      setForm({
        full_name: updated.full_name || "",
        email: updated.email || "",
        department: updated.department || "",
        title: updated.title || "",
      });
      setMessage("教师信息已保存。学生注册或绑定时可使用你的用户名或邮箱。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
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
          <span className="workspace-topbar__title">个人信息</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">教师</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <main className="student-info-page">
        <section className="student-info-panel">
          <div className="student-info-header">
            <div>
              <h1>个人信息</h1>
              <p>这里的信息用于教师端展示，也方便学生通过用户名或邮箱绑定到你名下。</p>
            </div>
            <div className="student-info-account">
              <span>用户名</span>
              <strong>{info?.username || "-"}</strong>
            </div>
          </div>

          {loading ? (
            <p className="student-info-muted">加载中...</p>
          ) : (
            <>
              <div className="student-info-current-teacher">
                当前绑定学生：<strong>{info?.student_count ?? 0}</strong> 人
              </div>

              <form className="student-info-form" onSubmit={handleSubmit}>
                {error && <div className="student-info-alert student-info-alert--error">{error}</div>}
                {message && <div className="student-info-alert student-info-alert--success">{message}</div>}

                <label>
                  <span>姓名</span>
                  <input value={form.full_name} onChange={(event) => updateField("full_name", event.target.value)} required />
                </label>

                <label>
                  <span>邮箱</span>
                  <input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} placeholder="用于学生绑定和后续通知" />
                </label>

                <label>
                  <span>学院 / 部门</span>
                  <input value={form.department} onChange={(event) => updateField("department", event.target.value)} placeholder="例如：计算机学院" />
                </label>

                <label>
                  <span>职称 / 岗位</span>
                  <input value={form.title} onChange={(event) => updateField("title", event.target.value)} placeholder="例如：就业指导老师" />
                </label>

                <div className="student-info-actions">
                  <button className="btn-primary" type="submit" disabled={saving}>
                    {saving ? "保存中..." : "保存信息"}
                  </button>
                </div>
              </form>

              {/* Change Password */}
              <div style={{ marginTop: 32, borderTop: "1px solid #e5e7eb", paddingTop: 24 }}>
                <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 12px" }}>修改密码</h2>
                {pwMessage && <div className="student-info-alert student-info-alert--success">{pwMessage}</div>}
                {pwError && <div className="student-info-alert student-info-alert--error">{pwError}</div>}
                <form className="student-info-form" onSubmit={async (e) => {
                  e.preventDefault();
                  setPwMessage("");
                  setPwError("");
                  if (pwForm.new_password.length < 6) { setPwError("新密码至少6位"); return; }
                  if (pwForm.new_password !== pwForm.confirm) { setPwError("两次输入的新密码不一致"); return; }
                  setPwSaving(true);
                  try {
                    await changePassword(pwForm.old_password, pwForm.new_password);
                    setPwMessage("密码修改成功，下次登录请使用新密码。");
                    setPwForm({ old_password: "", new_password: "", confirm: "" });
                  } catch (err) {
                    setPwError(err instanceof Error ? err.message : "修改密码失败");
                  } finally {
                    setPwSaving(false);
                  }
                }}>
                  <label>
                    <span>旧密码</span>
                    <div className="password-field">
                      <input type={showPw.old ? "text" : "password"} value={pwForm.old_password} onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))} placeholder="输入当前密码" required />
                      <button type="button" onClick={() => setShowPw(v => ({ ...v, old: !v.old }))} className="password-toggle" tabIndex={-1} aria-label={showPw.old ? "隐藏密码" : "显示密码"}><Icon name={showPw.old ? "eye" : "eye-off"} size={18} /></button>
                    </div>
                  </label>
                  <label>
                    <span>新密码</span>
                    <div className="password-field">
                      <input type={showPw.new ? "text" : "password"} value={pwForm.new_password} onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))} placeholder="至少6位" required />
                      <button type="button" onClick={() => setShowPw(v => ({ ...v, new: !v.new }))} className="password-toggle" tabIndex={-1} aria-label={showPw.new ? "隐藏密码" : "显示密码"}><Icon name={showPw.new ? "eye" : "eye-off"} size={18} /></button>
                    </div>
                  </label>
                  <label>
                    <span>确认新密码</span>
                    <div className="password-field">
                      <input type={showPw.confirm ? "text" : "password"} value={pwForm.confirm} onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))} placeholder="再次输入新密码" required />
                      <button type="button" onClick={() => setShowPw(v => ({ ...v, confirm: !v.confirm }))} className="password-toggle" tabIndex={-1} aria-label={showPw.confirm ? "隐藏密码" : "显示密码"}><Icon name={showPw.confirm ? "eye" : "eye-off"} size={18} /></button>
                    </div>
                  </label>
                  <div className="student-info-actions">
                    <button className="btn-primary" type="submit" disabled={pwSaving}>
                      {pwSaving ? "修改中..." : "修改密码"}
                    </button>
                  </div>
                </form>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

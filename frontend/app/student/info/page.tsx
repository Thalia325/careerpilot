"use client";

import { useEffect, useState } from "react";
import { getStudentSession, updateStudentInfo, type StudentInfoInput, type StudentSession } from "@/lib/api";

const emptyForm: StudentInfoInput = {
  full_name: "",
  email: "",
  major: "",
  grade: "",
  career_goal: "",
  teacher_code: "",
};

export default function StudentInfoPage() {
  const [form, setForm] = useState<StudentInfoInput>(emptyForm);
  const [session, setSession] = useState<StudentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getStudentSession()
      .then((data) => {
        setSession(data);
        setForm({
          full_name: data.full_name || "",
          email: data.email || "",
          major: data.major || "",
          grade: data.grade || "",
          career_goal: data.career_goal || "",
          teacher_code: "",
        });
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "加载个人信息失败");
      })
      .finally(() => setLoading(false));
  }, []);

  const updateField = (key: keyof StudentInfoInput, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setMessage("");
    setError("");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!form.full_name.trim()) {
      setError("请输入姓名或昵称");
      return;
    }
    if (form.email.trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) {
      setError("邮箱格式不正确");
      return;
    }

    setSaving(true);
    try {
      const updated = await updateStudentInfo({
        ...form,
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        major: form.major.trim(),
        grade: form.grade.trim(),
        career_goal: form.career_goal.trim(),
        teacher_code: form.teacher_code?.trim() || "",
      });
      setSession(updated);
      setForm({
        full_name: updated.full_name || "",
        email: updated.email || "",
        major: updated.major || "",
        grade: updated.grade || "",
        career_goal: updated.career_goal || "",
        teacher_code: "",
      });
      setMessage("个人信息已保存，教师端和管理端会读取最新数据。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <main className="student-info-page">
        <div className="student-info-panel">
          <p className="student-info-muted">加载中...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="student-info-page">
      <section className="student-info-panel">
        <div className="student-info-header">
          <div>
            <h1>个人信息</h1>
            <p>完善这些信息后，老师端和管理端会同步看到你的专业、年级、目标方向和所属老师。</p>
          </div>
          <div className="student-info-account">
            <span>账号</span>
            <strong>{session?.username || "-"}</strong>
          </div>
        </div>

        {session?.teacher ? (
          <div className="student-info-current-teacher">
            当前所属老师：<strong>{session.teacher.teacher_name || session.teacher.teacher_username}</strong>
            {session.teacher.teacher_username ? <span>（{session.teacher.teacher_username}）</span> : null}
          </div>
        ) : (
          <div className="student-info-current-teacher student-info-current-teacher--empty">
            当前还没有绑定老师。填写老师用户名或邮箱后，保存即可加入该老师的学生列表。
          </div>
        )}

        <form className="student-info-form" onSubmit={handleSubmit}>
          {error && <div className="student-info-alert student-info-alert--error">{error}</div>}
          {message && <div className="student-info-alert student-info-alert--success">{message}</div>}

          <label>
            <span>姓名 / 昵称</span>
            <input
              value={form.full_name}
              onChange={(event) => updateField("full_name", event.target.value)}
              placeholder="例如：张同学"
              required
            />
          </label>

          <label>
            <span>邮箱</span>
            <input
              type="email"
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              placeholder="用于老师识别和后续通知"
            />
          </label>

          <label>
            <span>专业</span>
            <input
              value={form.major}
              onChange={(event) => updateField("major", event.target.value)}
              placeholder="例如：软件工程"
            />
          </label>

          <label>
            <span>年级</span>
            <select value={form.grade} onChange={(event) => updateField("grade", event.target.value)}>
              <option value="">请选择年级</option>
              <option value="大一">大一</option>
              <option value="大二">大二</option>
              <option value="大三">大三</option>
              <option value="大四">大四</option>
              <option value="研一">研一</option>
              <option value="研二">研二</option>
              <option value="研三">研三</option>
            </select>
          </label>

          <label>
            <span>职业目标</span>
            <input
              value={form.career_goal}
              onChange={(event) => updateField("career_goal", event.target.value)}
              placeholder="例如：前端开发工程师、数据分析师"
            />
          </label>

          <label>
            <span>所属老师</span>
            <input
              value={form.teacher_code || ""}
              onChange={(event) => updateField("teacher_code", event.target.value)}
              placeholder="填写老师用户名或邮箱；不填写则保持当前绑定"
            />
          </label>

          <div className="student-info-actions">
            <button className="btn-primary" type="submit" disabled={saving}>
              {saving ? "保存中..." : "保存信息"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { sendChatMessage, getApiKeyStatus, listFiles, uploadFile, deleteFile, UploadedFileInfo } from "@/lib/api";
import Link from "next/link";

const studentNavItems = [
  { href: "/student", label: "首页", icon: "🏠" },
  { href: "/student/jobs", label: "岗位探索", icon: "🔍" },
  { href: "/student/profile", label: "我的能力分析", icon: "📊" },
  { href: "/student/reports", label: "制定我的职业规划", icon: "📋", subtitle: "含岗位匹配 + 发展路径 + 行动计划" },
  { href: "/student/history", label: "历史记录", icon: "🕐" },
  { href: "/student/recommended", label: "推荐岗位", icon: "💼" },
  { href: "/student/dashboard", label: "个人概览", icon: "👤" },
  { href: "/student/settings", label: "AI 模型设置", icon: "⚙️" }
];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const suggestedQuestions = [
  "产品经理需要什么技能？",
  "数据分析师的职业路径是什么？",
  "UI设计师怎么入行？",
  "市场营销适合什么人？",
  "项目经理的日常工作是什么？",
];

const ALLOWED_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/png", "image/jpeg"];
const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

function getUserId(): number | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.sub === "string" ? parseInt(payload.sub, 10) : payload.sub;
  } catch {
    return null;
  }
}

export default function StudentMainPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [roleLabel, setRoleLabel] = useState("同学");
  const [showGuide, setShowGuide] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [isDraggingUpload, setIsDraggingUpload] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const refreshFiles = useCallback(async () => {
    try {
      const files = await listFiles();
      setUploadedFiles(files);
    } catch {}
  }, []);

  useEffect(() => {
    const role = localStorage.getItem("user_role");
    if (role === "teacher") setRoleLabel("教师");
    else if (role === "admin") setRoleLabel("管理员");
  }, []);

  useEffect(() => {
    getApiKeyStatus()
      .then((data) => setApiKeyConfigured(data.configured))
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshFiles();
  }, [refreshFiles]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = query.trim();
    if (!text || isLoading) return;
    setQuery("");
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", content: result.reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "AI 连接失败，请检查网络或 API Key 配置" }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = "";
  };

  const processFile = async (file: File) => {
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext))) {
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      return;
    }

    const userId = getUserId();
    if (!userId) return;

    setIsUploading(true);
    try {
      await uploadFile(file, userId, "resume");
      await refreshFiles();
    } catch {
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    setDeletingId(fileId);
    try {
      await deleteFile(fileId);
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch {
    } finally {
      setDeletingId(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const fileTypeLabel: Record<string, string> = {
    resume: "简历",
    transcript: "成绩单",
    certificate: "证书",
  };

  const renderFileList = () => {
    if (uploadedFiles.length === 0) return null;
    return (
      <div className="student-main__file-list">
        <div className="student-main__file-list-title">已上传文件</div>
        {uploadedFiles.map((f) => (
          <div key={f.id} className="student-main__file-item">
            <span className="student-main__file-item-icon">📄</span>
            <span className="student-main__file-item-name">{f.file_name}</span>
            <span className="student-main__file-item-type">{fileTypeLabel[f.file_type] || f.file_type}</span>
            {f.created_at && (
              <span className="student-main__file-item-date">
                {new Date(f.created_at).toLocaleDateString("zh-CN")}
              </span>
            )}
            <button
              className="student-main__file-item-delete"
              onClick={() => handleDeleteFile(f.id)}
              disabled={deletingId === f.id}
              aria-label="删除文件"
            >
              {deletingId === f.id ? "…" : "✕"}
            </button>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="student-main">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={studentNavItems}
        label="学生功能"
        footer={
          <button
            className="sidebar-drawer__link"
            onClick={handleLogout}
            style={{ background: "none", border: "none", cursor: "pointer", width: "100%", color: "var(--color-error)" }}
          >
            <span className="sidebar-drawer__link-icon">🚪</span>
            退出登录
          </button>
        }
      />

      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单">☰</button>
          <span className="workspace-topbar__title">职航智策</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="guide-btn" onClick={() => setShowGuide(!showGuide)}>使用指南</button>
          <span className="workspace-topbar__user">{roleLabel}</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      {showGuide && (
        <div style={{ maxWidth: 720, margin: "16px auto", padding: "20px 24px", background: "#fff", borderRadius: 16, border: "1px solid rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 12px" }}>三步使用指南</h3>
          <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 8px" }}>1. 在 AI 模型设置中配置你的文心一言 API Key</p>
          <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 8px" }}>2. 上传简历或直接输入你想了解的职业方向</p>
          <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0" }}>3. AI 为你分析职业方向、岗位匹配和发展路径</p>
        </div>
      )}

      {messages.length === 0 ? (
        <div className="student-main__centered">
          <div className="student-main__greeting">
            <h1>你好，想了解什么职业方向？</h1>
            <p>输入你感兴趣的岗位方向或上传简历，AI 帮你分析</p>
            <div className="student-main__tags">
              {suggestedQuestions.map((q) => (
                <button key={q} className="student-main__tag" onClick={() => setQuery(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>

          <div className="student-main__input-area--centered">
            <div className="student-main__input-wrapper">
              <div className="student-main__input-row">
                <input
                  className="student-main__input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={apiKeyConfigured ? "输入你感兴趣的方向、岗位或问题…" : "请先配置 API Key 后再开始对话"}
                  disabled={isLoading}
                />
                <button className="student-main__send-btn" onClick={handleSend} disabled={isLoading || !query.trim()} aria-label="发送">
                  ➤
                </button>
              </div>
              <input ref={fileInputRef} hidden type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" onChange={handleFile} />
              <button
                className={`student-main__upload-card${isDraggingUpload ? " is-dragging" : ""}`}
                onClick={() => { if (!isUploading) fileInputRef.current?.click(); }}
                onDragOver={(e) => { e.preventDefault(); setIsDraggingUpload(true); }}
                onDragLeave={() => setIsDraggingUpload(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDraggingUpload(false);
                  const file = e.dataTransfer.files?.[0];
                  if (file) processFile(file);
                }}
                disabled={isUploading}
              >
                <span className="student-main__upload-card-icon">{isUploading ? "⏳" : "📄"}</span>
                <span className="student-main__upload-card-text">{isUploading ? "正在上传…" : "点击上传简历或将文件拖拽到这里"}</span>
                <span className="student-main__upload-card-hint">支持 PDF / Word / 图片，上传后生成你的能力档案</span>
              </button>
              {renderFileList()}
              {!apiKeyConfigured && (
                <div style={{ textAlign: "center", marginTop: "10px" }}>
                  <Link href="/student/settings" style={{ fontSize: "0.8125rem", color: "#4f46e5" }}>
                    未配置 AI 模型 → 点击设置
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div style={{ flex: 1, overflow: "auto", padding: "16px", maxWidth: 800, margin: "0 auto", width: "100%" }}>
            {messages.map((msg, i) => (
              <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", marginBottom: "12px" }}>
                <div style={{
                  maxWidth: "75%", padding: "10px 14px", fontSize: "0.875rem", lineHeight: "1.6", whiteSpace: "pre-wrap",
                  borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  background: msg.role === "user" ? "#4f46e5" : "#f3f4f6",
                  color: msg.role === "user" ? "#fff" : "#1f2430",
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "12px" }}>
                <div style={{ padding: "10px 14px", borderRadius: "16px 16px 16px 4px", background: "#f3f4f6", color: "#888", fontSize: "0.875rem" }}>
                  AI 正在思考...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="student-main__input-area">
            <div className="student-main__input-wrapper">
              <div className="student-main__input-row">
                <input
                  className="student-main__input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={apiKeyConfigured ? "输入你感兴趣的方向、岗位或问题…" : "请先配置 API Key 后再开始对话"}
                  disabled={isLoading}
                />
                <button className="student-main__send-btn" onClick={handleSend} disabled={isLoading || !query.trim()} aria-label="发送">
                  ➤
                </button>
              </div>
              <div className="student-main__upload-row">
                <input ref={fileInputRef} hidden type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" onChange={handleFile} />
                <button className="student-main__upload-btn" onClick={() => { if (!isUploading) fileInputRef.current?.click(); }} disabled={isUploading}>
                  {isUploading ? "⏳ 上传中…" : "📎 上传简历"}
                </button>
                <span className="student-main__upload-hint">上传简历，生成你的能力档案</span>
                {!apiKeyConfigured && (
                  <Link href="/student/settings" style={{ fontSize: "0.8125rem", color: "#4f46e5", marginLeft: "12px" }}>
                    未配置 AI 模型 → 点击设置
                  </Link>
                )}
              </div>
              {renderFileList()}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

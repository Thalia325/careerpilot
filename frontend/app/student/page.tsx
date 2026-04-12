"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import Markdown from "react-markdown";
import {
  sendChatMessage,
  listFiles,
  uploadFile,
  deleteFile,
  getStudentSession,
  parseOCR,
  generateStudentProfile,
  getMatching,
  generateReport,
  type UploadedFileInfo,
  type StudentSession,
  APIError,
} from "@/lib/api";
import { PipelineProgress, type PipelineStep, type PipelineStepStatus } from "@/components/PipelineProgress";
import { JobSelector } from "@/components/JobSelector";
import { Icon } from "@/components/Icon";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const defaultSuggestions = [
  "产品经理需要什么技能？",
  "数据分析师的职业路径是什么？",
  "项目经理的日常工作是什么？",
];

function buildSuggestions(session: StudentSession | null): string[] {
  if (!session) return defaultSuggestions;
  const { career_goal, major, suggested_job_title } = session;
  const goal = career_goal || suggested_job_title || "";
  const items: string[] = [];
  if (goal) {
    items.push(`${goal}需要什么技能？`);
    items.push(`${goal}的职业发展路径是什么？`);
    items.push(`如何提升${goal}方向的竞争力？`);
  }
  if (major && major !== goal) {
    items.push(`${major}专业适合哪些职业方向？`);
  }
  if (items.length < 3) {
    for (const d of defaultSuggestions) {
      if (items.length >= 5) break;
      if (!items.includes(d)) items.push(d);
    }
  }
  return items.slice(0, 5);
}

const ALLOWED_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/png", "image/jpeg"];
const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const PIPELINE_STEP_KEYS = ["uploaded", "parsed", "profiled", "matched", "reported"] as const;
const PIPELINE_STEP_LABELS: Record<string, string> = {
  uploaded: "已上传",
  parsed: "已解析",
  profiled: "已生成画像",
  matched: "已匹配",
  reported: "已出报告",
};

function getUserId(): number | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("token");
  if (!token) return null;
  if (token === "dev-bypass") return 1;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.sub === "string" ? parseInt(payload.sub, 10) : payload.sub;
  } catch {
    return null;
  }
}

function buildSteps(
  currentKey: string | null,
  errorKey: string | null,
  errorDetail?: string
): PipelineStep[] {
  const idx = currentKey ? PIPELINE_STEP_KEYS.indexOf(currentKey as typeof PIPELINE_STEP_KEYS[number]) : -1;
  return PIPELINE_STEP_KEYS.map((key, i) => {
    let status: PipelineStepStatus = "pending";
    let detail: string | undefined;
    if (errorKey === key) {
      status = "error";
      detail = errorDetail;
    } else if (idx >= 0 && i < idx) {
      status = "done";
    } else if (idx >= 0 && i === idx) {
      status = "done";
    } else if (currentKey === null && i === 0) {
      status = "pending";
    }
    return { key, label: PIPELINE_STEP_LABELS[key], status, detail };
  });
}

export default function StudentMainPage() {
  const [query, setQuery] = useState("");
  const [showGuide, setShowGuide] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDraggingUpload, setIsDraggingUpload] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [session, setSession] = useState<StudentSession | null>(null);
  const [jobCode, setJobCode] = useState<string | null>(null);
  const [jobTitle, setJobTitle] = useState<string>("");
  const [pipelineCurrent, setPipelineCurrent] = useState<string | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [pipelineErrorDetail, setPipelineErrorDetail] = useState<string | undefined>();
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineDone, setPipelineDone] = useState(false);
  const [reportId, setReportId] = useState<number | null>(null);

  const refreshFiles = useCallback(async () => {
    try {
      const files = await listFiles();
      setUploadedFiles(files);
    } catch {}
  }, []);

  useEffect(() => {
    refreshFiles();
    getStudentSession()
      .then((s) => {
        setSession(s);
        if (s.suggested_job_code) {
          setJobCode(s.suggested_job_code);
          setJobTitle(s.suggested_job_title || "");
        }
      })
      .catch(() => {});
  }, [refreshFiles]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const runPipeline = useCallback(
    async (sid: number, jCode: string, fileIds: number[]) => {
      setPipelineRunning(true);
      setPipelineDone(false);
      setPipelineError(null);
      setPipelineErrorDetail(undefined);

      try {
        setPipelineCurrent("uploaded");

        setPipelineCurrent("parsed");
        for (const fid of fileIds) {
          await parseOCR(fid, "resume");
        }

        setPipelineCurrent("profiled");
        await generateStudentProfile(sid, fileIds);

        setPipelineCurrent("matched");
        await getMatching(sid, jCode);

        setPipelineCurrent("reported");
        const report = await generateReport(sid, jCode);
        setReportId(report.report_id);

        setPipelineCurrent("reported");
        setPipelineDone(true);
      } catch (err: unknown) {
        const current = pipelineCurrent;
        setPipelineError(current);
        let detail = "未知错误";
        if (err instanceof APIError) {
          detail = err.message;
        } else if (err instanceof Error) {
          detail = err.message;
        }
        setPipelineErrorDetail(detail);
      } finally {
        setPipelineRunning(false);
      }
    },
    [pipelineCurrent]
  );

  const retryPipeline = useCallback(() => {
    if (!session?.student_id || !jobCode || uploadedFiles.length === 0) return;
    const fileIds = uploadedFiles.map((f) => f.id);
    const errorIdx = pipelineError
      ? PIPELINE_STEP_KEYS.indexOf(pipelineError as typeof PIPELINE_STEP_KEYS[number])
      : 0;
    const startKey = PIPELINE_STEP_KEYS[Math.max(0, errorIdx)];
    setPipelineCurrent(startKey);
    runPipeline(session.student_id, jobCode, fileIds);
  }, [session, jobCode, uploadedFiles, pipelineError, runPipeline]);

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
    } catch (err) {
      let errorMsg = "AI 连接失败，请检查网络或 Access Token 配置";
      if (err instanceof APIError) {
        if (err.statusCode === 401) {
          errorMsg = "登录已过期，请重新登录后再试。";
        } else if (err.isNetworkError) {
          errorMsg = "无法连接到服务器，请确认后端服务已启动（http://localhost:8000）。";
        } else {
          errorMsg = `请求失败：${err.message}`;
        }
      }
      setMessages((prev) => [...prev, { role: "assistant", content: errorMsg }]);
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
    setUploadError("");
    setUploadSuccess("");

    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext))) {
      setUploadError("不支持的文件类型。请上传 PDF、DOCX、PNG 或 JPG 文件。");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setUploadError(`文件过大。请上传不超过 10MB 的文件（当前：${(file.size / 1024 / 1024).toFixed(2)}MB）。`);
      return;
    }

    const userId = getUserId();
    if (!userId) {
      setUploadError("登录信息已过期，请重新登录。");
      return;
    }

    setIsUploading(true);
    try {
      const uploaded = await uploadFile(file, userId, "resume");
      await refreshFiles();
      setUploadSuccess(`${file.name} 上传成功`);
      setTimeout(() => setUploadSuccess(""), 3000);

      if (session?.student_id && jobCode) {
        runPipeline(session.student_id, jobCode, [uploaded.id]);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "上传失败，请稍后重试";
      setUploadError(msg);
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

  const handleJobSelect = (code: string, title: string) => {
    setJobCode(code);
    setJobTitle(title);
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
            <span className="student-main__file-item-icon"><Icon name="file" size={16} /></span>
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
              {deletingId === f.id ? "…" : "×"}
            </button>
          </div>
        ))}
      </div>
    );
  };

  const renderPipeline = () => {
    if (!pipelineCurrent && !pipelineDone && !pipelineError) return null;

    const steps = buildSteps(
      pipelineDone ? "reported" : pipelineCurrent,
      pipelineError,
      pipelineErrorDetail
    );

    return (
      <PipelineProgress
        steps={steps}
        onRetry={retryPipeline}
      />
    );
  };

  const renderPipelineResult = () => {
    if (!pipelineDone) return null;
    return (
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
        <Link href="/student/profile" className="btn-primary" style={{ textDecoration: "none", display: "inline-flex", fontSize: 14, padding: "8px 16px" }}>
          查看能力画像
        </Link>
        <Link href="/student/matching" className="btn-primary" style={{ textDecoration: "none", display: "inline-flex", fontSize: 14, padding: "8px 16px", background: "#7c3aed" }}>
          查看匹配分析
        </Link>
        <Link href="/student/path" className="btn-primary" style={{ textDecoration: "none", display: "inline-flex", fontSize: 14, padding: "8px 16px", background: "#0891b2" }}>
          查看职业路径
        </Link>
        {reportId && (
          <Link href={`/results/${reportId}`} className="btn-primary" style={{ textDecoration: "none", display: "inline-flex", fontSize: 14, padding: "8px 16px", background: "#059669" }}>
            查看完整报告
          </Link>
        )}
      </div>
    );
  };

  const needsJobSelect = !jobCode && uploadedFiles.length > 0 && !pipelineRunning && !pipelineDone;

  return (
    <div className="student-main">
      {showGuide && (
        <div style={{ maxWidth: 720, margin: "16px auto", padding: "20px 24px", background: "#fff", borderRadius: 16, border: "1px solid rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 12px" }}>两步使用指南</h3>
          <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 8px" }}>1. 上传简历或直接输入你想了解的职业方向</p>
          <p style={{ fontSize: "0.9375rem", color: "var(--subtle)", margin: "0 0 8px" }}>2. AI 为你分析职业方向、岗位匹配和发展路径</p>
          <button
            onClick={() => setShowGuide(false)}
            style={{ marginTop: 8, fontSize: "0.8125rem", background: "none", border: "1px solid #ddd", color: "var(--subtle)", cursor: "pointer", padding: "4px 12px", borderRadius: 6, minHeight: 28 }}
          >
            关闭
          </button>
        </div>
      )}

      {!showGuide && (
        <div style={{ textAlign: "center", padding: "4px 24px" }}>
          <button
            className="guide-btn"
            onClick={() => setShowGuide(!showGuide)}
            style={{ fontSize: "0.8125rem", background: "none", border: "1px solid #ddd", color: "var(--subtle)", cursor: "pointer", padding: "4px 12px", borderRadius: 6, minHeight: 28 }}
          >
            使用指南
          </button>
        </div>
      )}

      {renderPipeline()}
      {renderPipelineResult()}

      {needsJobSelect && (
        <div style={{ maxWidth: 720, margin: "0 auto 16px" }}>
          <JobSelector
            onSelect={(code, title) => {
              handleJobSelect(code, title);
              if (session?.student_id) {
                const fileIds = uploadedFiles.map((f) => f.id);
                runPipeline(session.student_id, code, fileIds);
              }
            }}
          />
        </div>
      )}

      {messages.length === 0 ? (
        <div className="student-main__centered">
          <div className="student-main__greeting">
            <h1>你好，想了解什么职业方向？</h1>
            <p>输入你感兴趣的岗位方向或上传简历，AI 帮你分析</p>
            <div className="student-main__tags">
              {buildSuggestions(session).map((q) => (
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
                  placeholder="输入你感兴趣的方向、岗位或问题…"
                  disabled={isLoading}
                />
                <button className="student-main__send-btn" onClick={handleSend} disabled={isLoading || !query.trim()} aria-label="发送">
                  <Icon name="send" size={16} />
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
                disabled={isUploading || pipelineRunning}
              >
                <span className="student-main__upload-card-icon">{isUploading ? <Icon name="loading" size={20} spin /> : <Icon name="file" size={20} />}</span>
                <span className="student-main__upload-card-text">{isUploading ? "正在上传…" : pipelineRunning ? "分析进行中…" : "点击上传简历或将文件拖拽到这里"}</span>
                <span className="student-main__upload-card-hint">支持 PDF / Word / 图片，上传后自动生成你的能力档案和匹配报告</span>
              </button>
              {uploadError && <p className="student-main__upload-error">{uploadError}</p>}
              {uploadSuccess && <p className="student-main__upload-success">{uploadSuccess}</p>}
              {renderFileList()}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="chat-new-topic-bar">
            <button
              className="chat-new-topic-btn"
              onClick={() => {
                setMessages([]);
                setQuery("");
                setPipelineCurrent(null);
                setPipelineDone(false);
                setPipelineError(null);
                setPipelineErrorDetail(undefined);
                setReportId(null);
                setUploadError("");
                setUploadSuccess("");
                refreshFiles();
                getStudentSession()
                  .then((s) => {
                    setSession(s);
                    if (s.suggested_job_code) {
                      setJobCode(s.suggested_job_code);
                      setJobTitle(s.suggested_job_title || "");
                    }
                  })
                  .catch(() => {});
              }}
              disabled={isLoading}
            >
              + 开启新话题
            </button>
          </div>
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", marginBottom: "12px" }}>
                <div style={{
                  maxWidth: "75%", padding: "10px 14px", fontSize: "0.875rem", lineHeight: "1.6",
                  whiteSpace: msg.role === "user" ? "pre-wrap" : "normal",
                  borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  background: msg.role === "user" ? "#4f46e5" : "#f3f4f6",
                  color: msg.role === "user" ? "#fff" : "#1f2430",
                }}>
                  {msg.role === "user" ? (
                    msg.content
                  ) : (
                    <div className="ai-report">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "12px" }}>
                <div className="chat-loading">
                  <span className="chat-loading__spinner" />
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
                  placeholder="输入你感兴趣的方向、岗位或问题…"
                  disabled={isLoading}
                />
                <button className="student-main__send-btn" onClick={handleSend} disabled={isLoading || !query.trim()} aria-label="发送">
                  <Icon name="send" size={16} />
                </button>
              </div>
              <div className="student-main__upload-row">
                <input ref={fileInputRef} hidden type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" onChange={handleFile} />
                <button className="student-main__upload-btn" onClick={() => { if (!isUploading) fileInputRef.current?.click(); }} disabled={isUploading || pipelineRunning}>
                  {isUploading ? "上传中…" : pipelineRunning ? "分析中…" : "上传简历"}
                </button>
                <span className="student-main__upload-hint">
                  {pipelineRunning ? "分析进行中，请稍候…" : "上传简历，自动生成能力档案和匹配报告"}
                </span>
              </div>
              {uploadError && <p className="student-main__upload-error">{uploadError}</p>}
              {uploadSuccess && <p className="student-main__upload-success">{uploadSuccess}</p>}
              {renderFileList()}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

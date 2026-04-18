"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import Markdown from "react-markdown";
import {
  sendChatMessage,
  listFiles,
  uploadFile,
  deleteFile,
  clearFiles,
  getStudentSession,
  parseOCR,
  generateStudentProfile,
  getMatching,
  getPathPlan,
  generateReport,
  getGreeting,
  updateTargetJob,
  startAnalysisRun,
  getLatestAnalysis,
  updateAnalysisContext,
  markStepRunning,
  markStepComplete,
  markStepFailed,
  markAnalysisComplete,
  resetAnalysisRun,
  type UploadedFileInfo,
  type StudentSession,
  type AnalysisRunState,
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

const PIPELINE_STEP_KEYS = ["uploaded", "parsed", "profiled", "matched", "pathed", "reported"] as const;
const PIPELINE_STEP_LABELS: Record<string, string> = {
  uploaded: "已上传",
  parsed: "已解析",
  profiled: "已生成画像",
  matched: "已匹配",
  pathed: "已规划路径",
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

function getAccountStorageKey(name: string): string | null {
  if (typeof window === "undefined") return null;
  const userId = getUserId() ?? localStorage.getItem("user_id");
  if (!userId) return null;
  return `${name}:user:${userId}`;
}

function buildSteps(
  currentKey: string | null,
  errorKey: string | null,
  errorDetail?: string,
  completedKeys?: Set<string>,
): PipelineStep[] {
  const idx = currentKey ? PIPELINE_STEP_KEYS.indexOf(currentKey as typeof PIPELINE_STEP_KEYS[number]) : -1;
  return PIPELINE_STEP_KEYS.map((key, i) => {
    let status: PipelineStepStatus = "pending";
    let detail: string | undefined;
    if (errorKey === key) {
      status = "error";
      detail = errorDetail;
    } else if (completedKeys?.has(key)) {
      status = "done";
    } else if (idx >= 0 && i < idx) {
      status = "done";
    } else if (idx >= 0 && i === idx) {
      status = "running";
    } else if (currentKey === null && i === 0) {
      status = "pending";
    }
    return { key, label: PIPELINE_STEP_LABELS[key], status, detail };
  });
}

export default function StudentMainPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const historyId = searchParams.get("history");
  const isHistoricalChatView = !!(historyId && historyId.startsWith("chat-"));
  const [query, setQuery] = useState("");
  const [showGuide, setShowGuide] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messagesLoaded, setMessagesLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDraggingUpload, setIsDraggingUpload] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const dragDepthRef = useRef(0);

  const [session, setSession] = useState<StudentSession | null>(null);
  const [jobCode, setJobCode] = useState<string | null>(null);
  const [jobTitle, setJobTitle] = useState<string>("");
  const [pipelineCurrent, setPipelineCurrent] = useState<string | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [pipelineErrorDetail, setPipelineErrorDetail] = useState<string | undefined>();
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineDone, setPipelineDone] = useState(false);
  const [pipelineCompletedSteps, setPipelineCompletedSteps] = useState<Set<string>>(new Set());
  const [analysisRunId, setAnalysisRunId] = useState<number | null>(null);
  const [reportId, setReportId] = useState<number | null>(null);
  const [matchResultId, setMatchResultId] = useState<number | null>(null);
  const [profileVersionId, setProfileVersionId] = useState<number | null>(null);
  const [pathRecommendationId, setPathRecommendationId] = useState<number | null>(null);
  const [jobSelectError, setJobSelectError] = useState("");
  const [jobSelectorDismissed, setJobSelectorDismissed] = useState(false);
  const [incompleteRunData, setIncompleteRunData] = useState(false);
  const [runFileIds, setRunFileIds] = useState<number[]>([]);
  const [retrying, setRetrying] = useState(false);
  const [greeting, setGreeting] = useState({ title: "你好，想了解什么职业方向？", sub: "输入你感兴趣的岗位方向或上传简历，AI 帮你分析" });

  const refreshFiles = useCallback(async () => {
    try {
      const files = await listFiles();
      setUploadedFiles(files);
    } catch {}
  }, []);

  const loadGreeting = useCallback(async () => {
    try {
      const g = await getGreeting();
      setGreeting({ title: g.greeting, sub: g.subline });
    } catch {}
  }, []);

  useEffect(() => {
    refreshFiles();
    loadGreeting();
    getStudentSession()
      .then((s) => {
        setSession(s);
        if (s.target_job_code) {
          setJobCode(s.target_job_code);
          setJobTitle(s.target_job_title || "");
        } else if (s.suggested_job_code) {
          setJobCode(s.suggested_job_code);
          setJobTitle(s.suggested_job_title || "");
        }
      })
      .catch(() => {});

    // Restore pipeline state from latest analysis run
    (async () => {
      try {
        const run = await getLatestAnalysis();
        if (run.status === "completed") {
          const completed = new Set<string>();
          for (const [key, done] of Object.entries(run.step_results ?? {})) {
            if (done) completed.add(key);
          }
          setAnalysisRunId(run.run_id);
          setReportId(run.report_id ?? null);
          setMatchResultId(run.match_result_id ?? null);
          setProfileVersionId(run.profile_version_id ?? null);
          setPathRecommendationId(run.path_recommendation_id ?? null);
          setRunFileIds(run.uploaded_file_ids ?? []);
          // Detect data incompleteness: completed run but missing report_id
          const hasMissingData = !run.report_id;
          if (hasMissingData) {
            // Remove "reported" from completed steps since no report exists
            completed.delete("reported");
          }
          setIncompleteRunData(hasMissingData);
          setPipelineCompletedSteps(completed);
          setPipelineCurrent(hasMissingData ? "pathed" : "reported");
          setPipelineDone(!hasMissingData);
          if (run.target_job_code) {
            setJobCode(run.target_job_code);
          }
        } else if (run.status === "failed") {
          const completed = new Set<string>();
          for (const [key, done] of Object.entries(run.step_results ?? {})) {
            if (done) completed.add(key);
          }
          setAnalysisRunId(run.run_id);
          setRunFileIds(run.uploaded_file_ids ?? []);
          setPipelineCompletedSteps(completed);
          setPipelineCurrent(run.current_step || run.failed_step);
          setPipelineError(run.failed_step || run.current_step);
          setPipelineErrorDetail(run.error_detail || undefined);
          if (run.target_job_code) {
            setJobCode(run.target_job_code);
          }
        } else if (run.status === "running") {
          const completed = new Set<string>();
          for (const [key, done] of Object.entries(run.step_results ?? {})) {
            if (done) completed.add(key);
          }
          setAnalysisRunId(run.run_id);
          setRunFileIds(run.uploaded_file_ids ?? []);
          setPipelineCompletedSteps(completed);
          setPipelineCurrent(run.current_step);
          setPipelineRunning(true);
          if (run.target_job_code) {
            setJobCode(run.target_job_code);
          }
        }
      } catch {
        // No previous run — start fresh
      }
    })();
  }, [refreshFiles, loadGreeting]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Save messages to localStorage whenever they change (skip in historical view)
  useEffect(() => {
    if (!messagesLoaded) return;
    if (isHistoricalChatView) return;
    const key = getAccountStorageKey("chat_messages");
    if (!key) return;
    if (messages.length > 0) {
      localStorage.setItem(key, JSON.stringify(messages));
    } else {
      localStorage.removeItem(key);
    }
  }, [messages, messagesLoaded, isHistoricalChatView]);

  // Load messages from localStorage on mount
  useEffect(() => {
    localStorage.removeItem("chat_messages");
    const key = getAccountStorageKey("chat_messages");
    if (!key) {
      setMessagesLoaded(true);
      return;
    }
    const saved = localStorage.getItem(key);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const hasMockNotice = parsed.some(
            (msg: ChatMessage) => typeof msg?.content === "string" && msg.content.includes("Mock 模式"),
          );
          if (hasMockNotice) {
            localStorage.removeItem(key);
          } else {
            setMessages(parsed);
          }
        }
      } catch {
        // Ignore invalid saved data
      }
    }
    setMessagesLoaded(true);
  }, []);

  // Load historical chat messages when ?history=chat-{id} is present
  useEffect(() => {
    if (!historyId || !historyId.startsWith("chat-")) return;
    const msgId = parseInt(historyId.replace("chat-", ""), 10);
    if (isNaN(msgId)) return;

    // Backup current messages before overwriting with historical ones
    const currentKey = getAccountStorageKey("chat_messages");
    const backupKey = getAccountStorageKey("chat_messages_current_backup");
    if (currentKey && backupKey) {
      const current = localStorage.getItem(currentKey);
      if (current && !localStorage.getItem(backupKey)) {
        localStorage.setItem(backupKey, current);
      }
    }

    (async () => {
      try {
        const { getChatHistory } = await import("@/lib/api");
        const res = await getChatHistory(msgId);
        if (res.messages && res.messages.length > 0) {
          setMessages(
            res.messages.map((m) => ({
              role: m.role as "user" | "assistant",
              content: m.content,
            }))
          );
        }
        setMessagesLoaded(true);
      } catch (err) {
        console.error("Failed to load chat history:", err);
      }
    })();
  }, [historyId]);

  // Cleanup backup when not in historical view
  useEffect(() => {
    if (isHistoricalChatView) return;
    const backupKey = getAccountStorageKey("chat_messages_current_backup");
    if (backupKey) {
      localStorage.removeItem(backupKey);
    }
  }, [isHistoricalChatView]);

  // Return from historical chat view to current conversation
  const exitHistoricalView = useCallback(() => {
    const backupKey = getAccountStorageKey("chat_messages_current_backup");
    if (backupKey) {
      const backup = localStorage.getItem(backupKey);
      if (backup) {
        try {
          const parsed = JSON.parse(backup);
          if (Array.isArray(parsed)) {
            setMessages(parsed);
          }
        } catch {
          setMessages([]);
        }
        localStorage.removeItem(backupKey);
      } else {
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
    router.push("/student");
  }, [router]);

  const runPipeline = useCallback(
    async (
      sid: number,
      jCode: string,
      fileIds: number[],
      options?: { resumeFromStep?: string; existingRunId?: number },
    ) => {
      const { resumeFromStep, existingRunId } = options ?? {};
      const startIdx = resumeFromStep
        ? PIPELINE_STEP_KEYS.indexOf(resumeFromStep as typeof PIPELINE_STEP_KEYS[number])
        : 0;

      setPipelineRunning(true);
      if (!resumeFromStep) {
        setPipelineDone(false);
        setPipelineError(null);
        setPipelineErrorDetail(undefined);
        setPipelineCompletedSteps(new Set());
        setIncompleteRunData(false);
        setRunFileIds(fileIds);
      } else {
        setPipelineError(null);
        setPipelineErrorDetail(undefined);
      }

      let runId: number | null = existingRunId ?? null;
      // Track current step locally to avoid stale closure
      let currentStep: string = startIdx >= 0 ? PIPELINE_STEP_KEYS[Math.max(0, startIdx)] : "uploaded";
      let localProfileVersionId = profileVersionId;
      let localMatchResultId = matchResultId;

      try {
        // Create a new run only when not resuming
        if (!runId) {
          const run = await startAnalysisRun(sid, jCode, fileIds);
          runId = run.run_id;
          setAnalysisRunId(runId);
        }

        for (let i = Math.max(0, startIdx); i < PIPELINE_STEP_KEYS.length; i++) {
          const step = PIPELINE_STEP_KEYS[i];
          currentStep = step;
          setPipelineCurrent(step);
          await markStepRunning(runId, step);

          switch (step) {
            case "uploaded":
              // File already uploaded — just mark complete
              break;
            case "parsed":
              for (const fid of fileIds) {
                await parseOCR(fid, "resume");
              }
              break;
            case "profiled": {
              const profile = await generateStudentProfile(sid, fileIds);
              localProfileVersionId = profile.profile_version_id ?? null;
              if (localProfileVersionId) {
                await updateAnalysisContext(runId, { profile_version_id: localProfileVersionId });
              }
              break;
            }
            case "matched": {
              const matching = await getMatching(sid, jCode, localProfileVersionId, runId);
              localMatchResultId = matching.match_result_id ?? null;
              if (localMatchResultId) {
                await updateAnalysisContext(runId, { match_result_id: localMatchResultId });
              }
              setMatchResultId(localMatchResultId);
              break;
            }
            case "pathed": {
              const pathPlan = await getPathPlan(sid, jCode);
              const pId = (pathPlan as Record<string, unknown>).path_id ?? (pathPlan as Record<string, unknown>).id ?? null;
              if (pId && typeof pId === "number") {
                await updateAnalysisContext(runId, { path_recommendation_id: pId });
                setPathRecommendationId(pId);
              }
              break;
            }
            case "reported": {
              const report = await generateReport(sid, jCode, {
                analysis_run_id: runId,
                profile_version_id: localProfileVersionId,
                match_result_id: localMatchResultId,
              });
              await updateAnalysisContext(runId, {
                report_id: report.report_id,
                profile_version_id: report.profile_version_id ?? localProfileVersionId,
                match_result_id: report.match_result_id ?? localMatchResultId,
                path_recommendation_id: report.path_recommendation_id ?? null,
              });
              setReportId(report.report_id);
              setProfileVersionId(report.profile_version_id ?? localProfileVersionId);
              if (report.match_result_id) setMatchResultId(report.match_result_id);
              if (report.path_recommendation_id) setPathRecommendationId(report.path_recommendation_id);
              break;
            }
          }

          await markStepComplete(runId, step);
          setPipelineCompletedSteps((prev) => new Set(prev).add(step));
        }

        await markAnalysisComplete(runId);
        setPipelineDone(true);
      } catch (err: unknown) {
        // Use locally tracked step to avoid stale closure
        setPipelineError(currentStep);
        let detail = "未知错误";
        if (err instanceof APIError) {
          detail = err.message;
        } else if (err instanceof Error) {
          detail = err.message;
        }
        setPipelineErrorDetail(detail);

        // Mark failure in backend
        if (runId) {
          try {
            await markStepFailed(runId, currentStep, detail);
          } catch {
            // Ignore state update failures
          }
        }
      } finally {
        setPipelineRunning(false);
      }
    },
    [profileVersionId, matchResultId],
  );

  const retryPipeline = useCallback((fromStepKey?: string) => {
    const sid = session?.student_id;
    if (!sid || !jobCode) return;
    // Use uploaded files if loaded, fall back to file IDs from the analysis run
    const fileIds = uploadedFiles.length > 0
      ? uploadedFiles.map((f) => f.id)
      : runFileIds;
    if (fileIds.length === 0) return;
    const failedStep = fromStepKey ?? pipelineError;
    const errorIdx = failedStep
      ? PIPELINE_STEP_KEYS.indexOf(failedStep as typeof PIPELINE_STEP_KEYS[number])
      : 0;
    const startKey = PIPELINE_STEP_KEYS[Math.max(0, errorIdx)];

    // Reset completed steps to those before the failed step
    const completed = new Set<string>();
    for (let i = 0; i < errorIdx; i++) {
      completed.add(PIPELINE_STEP_KEYS[i]);
    }
    setPipelineCompletedSteps(completed);
    setPipelineCurrent(startKey);
    setPipelineError(null);
    setPipelineErrorDetail(undefined);
    setRetrying(true);

    // Re-run pipeline from the failed step, reusing the same run.
    // No need to call resetAnalysisRun — markStepRunning already clears failed_step/error_detail
    // and preserves step_results for completed steps.
    runPipeline(sid, jobCode, fileIds, {
      resumeFromStep: startKey,
      existingRunId: analysisRunId ?? undefined,
    }).finally(() => setRetrying(false));
  }, [session, jobCode, uploadedFiles, runFileIds, pipelineError, analysisRunId, runPipeline]);

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
      setUploadSuccess(`${file.name} 上传成功，请选择目标岗位开始分析`);
      setJobSelectorDismissed(false);
      setTimeout(() => setUploadSuccess(""), 5000);

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

  const isFileDrag = (e: React.DragEvent<HTMLElement>) => Array.from(e.dataTransfer.types).includes("Files");

  const handlePageDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    e.stopPropagation();
    if (isUploading || pipelineRunning) return;
    dragDepthRef.current += 1;
    setIsDraggingUpload(true);
  };

  const handlePageDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = isUploading || pipelineRunning ? "none" : "copy";
    if (!isUploading && !pipelineRunning) setIsDraggingUpload(true);
  };

  const handlePageDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    e.stopPropagation();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) setIsDraggingUpload(false);
  };

  const handlePageDrop = (e: React.DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    e.stopPropagation();
    dragDepthRef.current = 0;
    setIsDraggingUpload(false);
    if (isUploading || pipelineRunning) return;
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const handleDeleteFile = async (fileId: number) => {
    if (!window.confirm("确定要删除此文件吗？删除后不可恢复。")) return;
    setDeletingId(fileId);
    try {
      await deleteFile(fileId);
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch {
    } finally {
      setDeletingId(null);
    }
  };

  const handleJobSelect = async (code: string, title: string): Promise<boolean> => {
    setJobSelectError("");
    setJobCode(code);
    setJobTitle(title);
    try {
      const result = await updateTargetJob(code, title);
      if (result.analysis_run_id) {
        setAnalysisRunId(result.analysis_run_id);
      }
      return true;
    } catch (err) {
      const msg = err instanceof APIError
        ? (err.isNetworkError ? "无法连接到服务器，请确认后端服务已启动" : `保存失败：${err.message}`)
        : "目标岗位保存失败，请稍后重试";
      setJobSelectError(msg);
      console.error("[handleJobSelect] Failed to save target job:", msg);
      return false;
    }
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
    if (!pipelineCurrent && !pipelineDone && !pipelineError && !incompleteRunData) return null;

    const steps = buildSteps(
      pipelineDone ? "reported" : pipelineCurrent,
      pipelineError,
      pipelineErrorDetail,
      pipelineCompletedSteps,
    );

    const failedStepLabel = pipelineError ? PIPELINE_STEP_LABELS[pipelineError] : null;

    return (
      <div className="student-main__pipeline-wrap">
        <PipelineProgress
          steps={steps}
          onRetry={retryPipeline}
        />
        {pipelineError && !pipelineRunning && (
          <div className="student-main__pipeline-error-banner">
            <div className="student-main__pipeline-error-banner-header">
              <Icon name="alert-circle" size={18} color="#dc2626" />
              <span className="student-main__pipeline-error-banner-title">
                {failedStepLabel ?? pipelineError} 步骤失败
              </span>
            </div>
            {pipelineErrorDetail && (
              <p className="student-main__pipeline-error-banner-detail">{pipelineErrorDetail}</p>
            )}
            <div className="student-main__pipeline-error-banner-actions">
              <button
                className="student-main__pipeline-error-retry-btn"
                onClick={() => retryPipeline(pipelineError ?? undefined)}
                disabled={pipelineRunning || retrying}
              >
                {retrying ? "重试中…" : "重试失败步骤"}
              </button>
              <button
                className="student-main__pipeline-error-restart-btn"
                onClick={() => {
                  setPipelineError(null);
                  setPipelineErrorDetail(undefined);
                  setPipelineCurrent(null);
                  setPipelineDone(false);
                  setPipelineCompletedSteps(new Set());
                  setAnalysisRunId(null);
                  setReportId(null);
                  setMatchResultId(null);
                  setProfileVersionId(null);
                  setPathRecommendationId(null);
                  setIncompleteRunData(false);
                  setRunFileIds([]);
                  setRetrying(false);
                }}
                disabled={pipelineRunning || retrying}
              >
                重新开始
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderPipelineResult = () => {
    if (!pipelineDone && !incompleteRunData) return null;
    return (
      <div className="student-main__result-area">
        {incompleteRunData ? (
          <p className="student-main__result-title" style={{ color: "#b45309" }}>
            ⚠️ 该次分析数据不完整（未生成报告），建议重新分析
          </p>
        ) : (
          <p className="student-main__result-title">
            🎉 分析完成！以下是你的能力档案和职业规划结果：
          </p>
        )}
        <div className="student-main__result-actions">
          <Link href={profileVersionId ? `/student/profile?version_id=${profileVersionId}` : "/student/profile"} className="btn-primary student-main__result-btn">
            查看能力画像
          </Link>
          <Link href="/student/recommended" className="btn-primary student-main__result-btn student-main__result-btn--red">
            查看推荐岗位
          </Link>
          <Link href={matchResultId ? `/student/matching?match_id=${matchResultId}` : "/student/matching"} className="btn-primary student-main__result-btn student-main__result-btn--purple">
            查看匹配分析
          </Link>
          <Link href={pathRecommendationId ? `/student/path?path_id=${pathRecommendationId}` : "/student/path"} className="btn-primary student-main__result-btn student-main__result-btn--teal">
            查看职业路径
          </Link>
          {reportId ? (
            <Link href={`/results/${reportId}`} className="btn-primary student-main__result-btn student-main__result-btn--green">
              查看完整报告
            </Link>
          ) : (
            <span className="btn-primary student-main__result-btn student-main__result-btn--green" style={{ opacity: 0.5, cursor: "not-allowed" }}>
              报告未生成
            </span>
          )}
        </div>
        {incompleteRunData && (
          <p className="student-main__result-hint" style={{ color: "#92400e" }}>
            💡 可点击 <strong>&quot;开启新话题&quot;</strong> 按钮重新上传简历进行分析
          </p>
        )}
        {!incompleteRunData && (
          <p className="student-main__result-hint">
            💡 所有结果也会保存在<a href="/student/history">历史记录</a>中，随时可以查看
          </p>
        )}
      </div>
    );
  };

  const needsJobSelect = !jobCode && uploadedFiles.length > 0 && !pipelineRunning && !pipelineDone && !jobSelectorDismissed;
  const inputIsCompact = isLoading || pipelineRunning;

  return (
    <div
      className={`student-main${isDraggingUpload ? " is-upload-dragging" : ""}`}
      onDragEnter={handlePageDragEnter}
      onDragOver={handlePageDragOver}
      onDragLeave={handlePageDragLeave}
      onDrop={handlePageDrop}
    >
      {/* Onboarding flow guide */}
      <div className="student-onboarding-guide">
        <div className="student-onboarding-guide__inner">
          <div className="student-onboarding-guide__header">
            <span className="student-onboarding-guide__badge">使用指南</span>
            <button
              className="student-onboarding-guide__toggle"
              onClick={() => setShowGuide(!showGuide)}
            >
              {showGuide ? "收起" : "展开"}
            </button>
          </div>
          {showGuide && (
            <div className="student-onboarding-guide__steps">
              <div className="student-onboarding-guide__step">
                <span className="student-onboarding-guide__step-num">1</span>
                <div className="student-onboarding-guide__step-body">
                  <strong>上传简历</strong>
                  <span>点击下方上传区域或将文件拖拽进来，支持 PDF / Word / 图片格式</span>
                </div>
              </div>
              <div className="student-onboarding-guide__step">
                <span className="student-onboarding-guide__step-num">2</span>
                <div className="student-onboarding-guide__step-body">
                  <strong>选择目标岗位</strong>
                  <span>上传成功后选择你想分析的目标岗位方向</span>
                </div>
              </div>
              <div className="student-onboarding-guide__step">
                <span className="student-onboarding-guide__step-num">3</span>
                <div className="student-onboarding-guide__step-body">
                  <strong>等待分析完成</strong>
                  <span>系统自动完成 OCR 解析、能力画像、岗位匹配、路径规划和报告生成</span>
                </div>
              </div>
              <div className="student-onboarding-guide__step">
                <span className="student-onboarding-guide__step-num">4</span>
                <div className="student-onboarding-guide__step-body">
                  <strong>查看结果</strong>
                  <span>分析完成后可查看能力画像、匹配分析、职业路径和完整报告</span>
                </div>
              </div>
              <div className="student-onboarding-guide__step">
                <span className="student-onboarding-guide__step-num">5</span>
                <div className="student-onboarding-guide__step-body">
                  <strong>回顾历史</strong>
                  <span>所有分析记录保存在历史记录中，可随时通过侧边栏进入查看</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Teacher binding notice for unbound students */}
      {!session?.teacher && (
        <div className="student-teacher-binding-notice">
          <div className="student-teacher-binding-notice__inner">
            <div className="student-teacher-binding-notice__header">
              <Icon name="alert-circle" size={18} />
              <strong>尚未绑定指导老师</strong>
            </div>
            <p className="student-teacher-binding-notice__desc">
              绑定老师后，你可以获得以下功能：
            </p>
            <ul className="student-teacher-binding-notice__features">
              <li><Icon name="check-circle" size={14} color="#16a34a" />老师可以查看你的分析报告并提供个性化指导</li>
              <li><Icon name="check-circle" size={14} color="#16a34a" />接收老师的跟进建议和职业发展反馈</li>
              <li><Icon name="check-circle" size={14} color="#16a34a" />在老师的班级管理中被统一跟踪和辅导</li>
            </ul>
            <Link href="/student/info" className="btn-primary student-teacher-binding-notice__action">
              前往绑定老师
            </Link>
          </div>
        </div>
      )}

      {renderPipeline()}
      {renderPipelineResult()}

      {needsJobSelect && (
        <div style={{ maxWidth: 720, margin: "0 auto 16px" }}>
          <div className="student-main__step-indicator student-main__step-indicator--done">
            <Icon name="check-circle" size={16} color="#16a34a" />
            <span>简历上传成功</span>
            {uploadedFiles.length > 0 && (
              <span className="student-main__step-indicator-file">{uploadedFiles[uploadedFiles.length - 1].file_name}</span>
            )}
          </div>
          <JobSelector
            onSelect={async (code, title) => {
              const saved = await handleJobSelect(code, title);
              if (session?.student_id) {
                const fileIds = uploadedFiles.map((f) => f.id);
                runPipeline(session.student_id, code, fileIds);
              }
            }}
            onCancel={() => {
              setJobSelectorDismissed(true);
              setJobSelectError("");
            }}
          />
          {jobSelectError && <p className="student-main__upload-error">{jobSelectError}</p>}
        </div>
      )}

      {!needsJobSelect && !jobCode && uploadedFiles.length > 0 && !pipelineRunning && !pipelineDone && jobSelectorDismissed && (
        <div style={{ maxWidth: 720, margin: "0 auto 16px", textAlign: "center" }}>
          <div className="student-main__step-indicator student-main__step-indicator--done">
            <Icon name="check-circle" size={16} color="#16a34a" />
            <span>简历已上传</span>
          </div>
          <button
            className="btn-primary"
            style={{ marginTop: 8, fontSize: "0.875rem", padding: "6px 16px" }}
            onClick={() => setJobSelectorDismissed(false)}
          >
            选择目标岗位
          </button>
        </div>
      )}

      {messages.length === 0 ? (
        <div className="student-main__centered">
          <div className="student-main__greeting">
            <h1>{greeting.title}</h1>
            <p>{greeting.sub}</p>
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
                className={`student-main__upload-card${isDraggingUpload ? " is-dragging" : ""}${needsJobSelect ? " is-uploaded" : ""}`}
                onClick={() => { if (!isUploading && !needsJobSelect) fileInputRef.current?.click(); }}
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); if (!needsJobSelect) setIsDraggingUpload(true); }}
                onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingUpload(false); }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  dragDepthRef.current = 0;
                  setIsDraggingUpload(false);
                  if (needsJobSelect) return;
                  const file = e.dataTransfer.files?.[0];
                  if (file) processFile(file);
                }}
                disabled={isUploading || pipelineRunning || needsJobSelect}
              >
                {needsJobSelect ? (
                  <>
                    <span className="student-main__upload-card-icon"><Icon name="check-circle" size={20} color="#16a34a" /></span>
                    <span className="student-main__upload-card-text student-main__upload-card-text--done">简历上传成功</span>
                    <span className="student-main__upload-card-hint">请在上方选择目标岗位开始分析</span>
                  </>
                ) : (
                  <>
                    <span className="student-main__upload-card-icon">{isUploading ? <Icon name="loading" size={20} spin /> : <Icon name="file" size={20} />}</span>
                    <span className="student-main__upload-card-text">{isUploading ? "正在上传…" : pipelineRunning ? "分析进行中…" : "点击上传简历或将文件拖拽到这里"}</span>
                    <span className="student-main__upload-card-hint">支持 PDF / Word / 图片，上传后自动生成你的能力档案和匹配报告</span>
                  </>
                )}
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
                const key = getAccountStorageKey("chat_messages");
                if (key) localStorage.removeItem(key);
                localStorage.removeItem("chat_messages");
                // Clear historical backup if exists
                const backupKey = getAccountStorageKey("chat_messages_current_backup");
                if (backupKey) localStorage.removeItem(backupKey);
                setMessages([]);
                setQuery("");
                setPipelineCurrent(null);
                setPipelineDone(false);
                setPipelineError(null);
                setPipelineErrorDetail(undefined);
                setPipelineCompletedSteps(new Set());
                setAnalysisRunId(null);
                setReportId(null);
                setMatchResultId(null);
                setProfileVersionId(null);
                setPathRecommendationId(null);
                setIncompleteRunData(false);
                setRunFileIds([]);
                setRetrying(false);
                setUploadError("");
                setUploadSuccess("");
                clearFiles().catch(() => {});
                setUploadedFiles([]);
                // If in historical view, navigate to /student to exit
                if (isHistoricalChatView) {
                  router.push("/student");
                }
                loadGreeting();
                getStudentSession()
                  .then((s) => {
                    setSession(s);
                    if (s.target_job_code) {
                      setJobCode(s.target_job_code);
                      setJobTitle(s.target_job_title || "");
                    } else if (s.suggested_job_code) {
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
            {isHistoricalChatView && (
              <div style={{
                padding: "10px 16px",
                marginBottom: "12px",
                background: "#fff3e0",
                borderRadius: "8px",
                fontSize: "0.875rem",
                color: "#e65100",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
              }}>
                <span>⚠️ 正在查看历史对话记录（只读）</span>
                <button
                  onClick={exitHistoricalView}
                  style={{
                    padding: "4px 14px",
                    borderRadius: 6,
                    border: "1px solid #e65100",
                    background: "#fff",
                    color: "#e65100",
                    cursor: "pointer",
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                    minHeight: 28,
                  }}
                >
                  返回当前对话
                </button>
              </div>
            )}
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

          <div className={`student-main__input-area${inputIsCompact ? " is-compact" : ""}`}>
            <div className="student-main__input-wrapper">
              {isHistoricalChatView ? (
                <div style={{
                  padding: "10px 16px",
                  background: "#f5f5f5",
                  borderRadius: "8px",
                  textAlign: "center",
                  color: "#999",
                  fontSize: "0.875rem",
                }}>
                  历史对话为只读模式，如需发送消息请先返回当前对话
                </div>
              ) : (
                <>
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
              {!inputIsCompact && (
                <div className={`student-main__upload-row${isDraggingUpload ? " is-dragging" : ""}`}>
                  <input ref={fileInputRef} hidden type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" onChange={handleFile} />
                  <button className="student-main__upload-btn" onClick={() => { if (!isUploading) fileInputRef.current?.click(); }} disabled={isUploading || pipelineRunning}>
                    {isUploading ? "上传中…" : "上传简历"}
                  </button>
                  <span className="student-main__upload-hint">
                    上传简历，自动生成能力档案和匹配报告
                  </span>
                </div>
              )}
              {uploadError && <p className="student-main__upload-error">{uploadError}</p>}
              {uploadSuccess && <p className="student-main__upload-success">{uploadSuccess}</p>}
              {!inputIsCompact && renderFileList()}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

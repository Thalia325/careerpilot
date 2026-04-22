"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { formatTime } from "@/lib/format";
import Markdown from "react-markdown";
import {
  API_BASE,
  checkReport,
  exportReport,
  getPathResult,
  getReport,
  polishReport,
  saveReport,
  getStudentTeacherFeedback,
  markFeedbackRead,
  type PathPlan,
  type ReportCheckResult,
  type ReportDraft,
  type ReportExportResult,
  type TeacherFeedbackItem,
} from "@/lib/api";
import { SectionCard } from "@/components/SectionCard";
import { StudentShellClient } from "@/components/StudentShellClient";

const SECTIONS = [
  { key: "matching", title: "职业探索与岗位匹配", desc: "人岗匹配度、专业技能与通用素质差距" },
  { key: "path", title: "职业目标与路径规划", desc: "目标岗位、行业趋势、岗位图谱发展路径" },
  { key: "action", title: "行动计划与成果展示", desc: "短期/中期计划、实践安排、评估指标" },
  { key: "export", title: "编辑优化与导出", desc: "润色、检查、编辑、PDF/DOCX 导出" },
];

function exportedUrl(fileName: string): string {
  const root = API_BASE.replace(/\/api\/v1$/, "");
  return `${root}/exports/${encodeURIComponent(fileName)}`;
}

function previewUrl(exportResult: ReportExportResult | null): string | null {
  const fileName = exportResult?.exported.preview_file_name;
  return fileName ? exportedUrl(fileName) : null;
}

async function downloadExportedFile(fileName: string): Promise<void> {
  const url = exportedUrl(fileName);

  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = fileName;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  } catch {
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
}

function readComparison(report: ReportDraft | null) {
  const content = (report?.content ?? {}) as Record<string, unknown>;
  const comparison = (content.job_comparison ?? {}) as Record<string, unknown>;
  const matched = (comparison.matched_job ?? {}) as Record<string, unknown>;
  const ideal = (comparison.ideal_job ?? {}) as Record<string, unknown>;

  return {
    matchedJobTitle: (matched.job_title as string | undefined) || report?.matched_job_title || "未识别",
    matchedJobCode: (matched.job_code as string | undefined) || report?.matched_job_code || "",
    matchedScore: typeof matched.match_score === "number" ? matched.match_score : null,
    idealJobTitle: (ideal.job_title as string | undefined) || report?.ideal_job_title || report?.matched_job_title || "未识别",
    idealJobCode: (ideal.job_code as string | undefined) || report?.ideal_job_code || report?.matched_job_code || "",
    differenceSummary: (comparison.difference_summary as string | undefined) || "",
    focusRecommendation: (comparison.focus_recommendation as string | undefined) || "",
    sameJob: Boolean(comparison.same_job),
    missingSkills: Array.isArray(ideal.missing_skills) ? (ideal.missing_skills as string[]) : [],
  };
}

export default function ResultPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const reportId = Number(params.id);
  const isHistoricalView = searchParams.get("source") === "history";
  const [report, setReport] = useState<ReportDraft | null>(null);
  const [pathPlan, setPathPlan] = useState<PathPlan | null>(null);
  const [draft, setDraft] = useState("");
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [checkResult, setCheckResult] = useState<ReportCheckResult | null>(null);
  const [exportResult, setExportResult] = useState<ReportExportResult | null>(null);
  const [notice, setNotice] = useState("");
  const [teacherFeedback, setTeacherFeedback] = useState<TeacherFeedbackItem[]>([]);
  const [feedbackLoading, setFeedbackLoading] = useState(true);

  useEffect(() => {
    if (!Number.isFinite(reportId) || reportId <= 0) {
      setError("报告编号无效");
      setLoading(false);
      return;
    }

    getReport(reportId)
      .then((data) => {
        setReport(data);
        setDraft(data.markdown_content || "");
        if (data.path_recommendation_id) {
          getPathResult(data.path_recommendation_id).then(setPathPlan).catch(() => {});
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "报告加载失败"))
      .finally(() => setLoading(false));

    // Load teacher feedback for this student
    setFeedbackLoading(true);
    getStudentTeacherFeedback()
      .then((items) => {
        // Filter feedback for current report
        setTeacherFeedback(items.filter((f) => f.report_id === reportId));
        // Auto-mark unread feedback as read
        items.filter((f) => f.report_id === reportId && !f.student_read_at).forEach((f) => {
          markFeedbackRead(f.id).catch(() => {});
        });
      })
      .catch(() => setTeacherFeedback([]))
      .finally(() => setFeedbackLoading(false));
  }, [reportId]);

  const canOperate = useMemo(() => Boolean(report && draft.trim() && !busy), [report, draft, busy]);

  const handlePolish = async () => {
    if (!canOperate) return;
    setBusy("polish");
    setNotice("");
    try {
      const data = await polishReport(reportId, draft);
      setReport(data);
      setDraft(data.markdown_content);
      setEditing(false);
      setNotice("智能润色完成");
    } catch (err) {
      setError(err instanceof Error ? err.message : "润色失败");
    } finally {
      setBusy("");
    }
  };

  const handleSave = async () => {
    if (!canOperate) return;
    setBusy("save");
    setNotice("");
    try {
      const saved = await saveReport(reportId, draft);
      setReport((prev) => prev ? { ...prev, markdown_content: saved.markdown_content, status: saved.status } : prev);
      setEditing(false);
      setNotice("手动编辑已保存");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setBusy("");
    }
  };

  const handleCheck = async () => {
    if (!report || busy) return;
    setBusy("check");
    setNotice("");
    try {
      const result = await checkReport(reportId);
      setCheckResult(result);
      setNotice(result.is_complete ? "内容完整性检查通过" : "内容完整性检查完成，有缺失项");
    } catch (err) {
      setError(err instanceof Error ? err.message : "检查失败");
    } finally {
      setBusy("");
    }
  };

  const handleExport = async (format: "pdf" | "docx") => {
    if (!report || busy) return;
    setBusy(`export-${format}`);
    setNotice("");
    try {
      const result = await exportReport(reportId, format);
      setExportResult(result);
      await downloadExportedFile(result.exported.file_name);
      setNotice(`${format.toUpperCase()} 导出完成，已开始下载`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出失败");
    } finally {
      setBusy("");
    }
  };

  const verticalNodes = (pathPlan?.vertical_graph?.nodes ?? []) as Array<{
    title: string;
    description?: string;
    skills?: string[];
    level?: number;
    stage?: string;
  }>;
  const transitionRoles = (pathPlan?.transition_graph?.role_paths ?? []) as Array<{
    title: string;
    description?: string;
    skills?: string[];
    paths?: Array<{
      steps: string[];
      relation?: string;
      description?: string;
      skill_bridge?: string[];
    }>;
  }>;
  const hasGraphData = verticalNodes.length > 0 || transitionRoles.length > 0;
  const comparison = readComparison(report);

  return (
    <StudentShellClient title="完整报告">
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>完整报告</h1>
              {isHistoricalView ? (
                <span style={{ padding: "2px 10px", borderRadius: 6, background: "rgba(180,83,9,0.1)", color: "#b45309", fontSize: "0.75rem", fontWeight: 600 }}>历史报告</span>
              ) : (
                <span style={{ padding: "2px 10px", borderRadius: 6, background: "rgba(34,197,94,0.1)", color: "#166534", fontSize: "0.75rem", fontWeight: 600 }}>当前最新</span>
              )}
            </div>
            <p style={{ margin: "6px 0 0", color: "var(--subtle)", fontSize: "0.875rem" }}>
              报告覆盖职业探索、目标路径、行动计划、编辑导出四个模块。
            </p>
          </div>
          <Link href="/student" className="btn-secondary" style={{ textDecoration: "none", padding: "8px 14px", flexShrink: 0 }}>
            返回问答页
          </Link>
        </div>

      {loading ? (
        <SectionCard title="加载中">
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        </SectionCard>
      ) : error ? (
        <SectionCard title="提示">
          <p style={{ color: "#b91c1c" }}>{error}</p>
        </SectionCard>
      ) : (
        <>
          {hasGraphData && (
            <>
              <SectionCard title="垂直岗位图谱">
                <p style={{ color: "var(--subtle)", margin: "0 0 20px", lineHeight: 1.7 }}>
                  {pathPlan?.vertical_graph?.description || pathPlan?.rationale || "基于岗位图谱生成晋升链路。"}
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, alignItems: "stretch" }}>
                  {verticalNodes.map((node, index, arr) => (
                    <div key={`${node.title}-${index}`} style={{ display: "flex", gap: 12, alignItems: "stretch" }}>
                      <div style={{ flex: 1, border: "1px solid rgba(15,116,218,0.16)", borderRadius: 8, padding: 16, background: "#fff" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginBottom: 10 }}>
                          <span style={{ color: "#0f74da", fontWeight: 700, fontSize: "0.8125rem" }}>L{node.level ?? index + 1}</span>
                          {node.stage && <span style={{ color: "#0f766e", fontSize: "0.75rem", fontWeight: 700 }}>{node.stage}</span>}
                        </div>
                        <h3 style={{ margin: "0 0 8px", fontSize: "1rem" }}>{node.title}</h3>
                        <p style={{ margin: "0 0 12px", color: "var(--subtle)", fontSize: "0.8125rem", lineHeight: 1.6 }}>{node.description || "围绕岗位要求持续沉淀项目成果。"}</p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {(node.skills ?? []).slice(0, 4).map((skill) => (
                            <span key={skill} style={{ padding: "4px 8px", borderRadius: 8, background: "#eef6ff", color: "#0f4f9a", fontSize: "0.75rem", fontWeight: 600 }}>{skill}</span>
                          ))}
                        </div>
                      </div>
                      {index < arr.length - 1 && (
                        <div style={{ display: "flex", alignItems: "center", color: "#8aa0b8", fontWeight: 700 }}>→</div>
                      )}
                    </div>
                  ))}
                </div>
                {(pathPlan?.vertical_graph?.promotion_paths ?? []).length > 1 && (
                  <div style={{ marginTop: 18 }}>
                    <h3 style={{ margin: "0 0 10px", fontSize: "0.9375rem" }}>其他晋升链路</h3>
                    <div style={{ display: "grid", gap: 8 }}>
                      {(pathPlan?.vertical_graph?.promotion_paths ?? []).map((path: string[]) => (
                        <div key={path.join("-")} style={{ padding: "10px 12px", borderRadius: 8, background: "#f8fafc", color: "var(--ink)" }}>
                          {path.join(" → ")}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </SectionCard>

              <SectionCard title="换岗路径图谱">
                <p style={{ color: "var(--subtle)", margin: "0 0 16px", lineHeight: 1.7 }}>
                  已关联 {transitionRoles.length || 0} 个相关岗位；每个岗位至少给出 2 条换岗路径，便于比较转岗成本和技能桥接点。
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 14 }}>
                  {transitionRoles.map((role) => (
                    <article key={role.title} style={{ border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8, background: "#fff", padding: 16 }}>
                      <h3 style={{ margin: "0 0 8px", fontSize: "1rem" }}>{role.title}</h3>
                      <p style={{ margin: "0 0 12px", color: "var(--subtle)", fontSize: "0.8125rem", lineHeight: 1.6 }}>{role.description}</p>
                      <div style={{ display: "grid", gap: 10 }}>
                        {(role.paths ?? []).slice(0, 3).map((path) => (
                          <div key={path.steps.join("-")} style={{ padding: 12, borderRadius: 8, background: "#f8fafc" }}>
                            <strong style={{ display: "block", marginBottom: 6, fontSize: "0.875rem" }}>{path.steps.join(" → ")}</strong>
                            <p style={{ margin: "0 0 8px", color: "var(--subtle)", fontSize: "0.8125rem", lineHeight: 1.6 }}>{path.description}</p>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                              {(path.skill_bridge ?? []).map((skill) => (
                                <span key={skill} style={{ padding: "4px 8px", borderRadius: 8, background: "#fff4e5", color: "#8a4b00", fontSize: "0.75rem", fontWeight: 600 }}>{skill}</span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </SectionCard>
            </>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginBottom: 16 }}>
            {SECTIONS.map((item) => (
              <div key={item.key} style={{ background: "#fff", border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8, padding: 14 }}>
                <strong style={{ display: "block", marginBottom: 6 }}>{item.title}</strong>
                <span style={{ color: "var(--subtle)", fontSize: "0.8125rem", lineHeight: 1.6 }}>{item.desc}</span>
              </div>
            ))}
          </div>

          <SectionCard title="岗位对照摘要">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
              <div style={{ border: "1px solid rgba(15,116,218,0.16)", borderRadius: 8, padding: 16, background: "#f8fbff" }}>
                <div style={{ color: "#0f74da", fontSize: "0.75rem", fontWeight: 700, marginBottom: 8 }}>当前较匹配岗位</div>
                <div style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 6 }}>{comparison.matchedJobTitle}</div>
                {comparison.matchedJobCode ? (
                  <div style={{ color: "var(--subtle)", fontSize: "0.8125rem", marginBottom: 8 }}>{comparison.matchedJobCode}</div>
                ) : null}
                {typeof comparison.matchedScore === "number" ? (
                  <div style={{ color: "#0f4f9a", fontSize: "0.875rem", fontWeight: 600 }}>匹配得分 {comparison.matchedScore.toFixed(1)}</div>
                ) : null}
              </div>
              <div style={{ border: "1px solid rgba(245,158,11,0.18)", borderRadius: 8, padding: 16, background: "#fffaf2" }}>
                <div style={{ color: "#b45309", fontSize: "0.75rem", fontWeight: 700, marginBottom: 8 }}>理想岗位</div>
                <div style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 6 }}>{comparison.idealJobTitle}</div>
                {comparison.idealJobCode ? (
                  <div style={{ color: "var(--subtle)", fontSize: "0.8125rem", marginBottom: 8 }}>{comparison.idealJobCode}</div>
                ) : null}
                <div style={{ color: "#8a4b00", fontSize: "0.875rem", lineHeight: 1.6 }}>
                  {comparison.sameJob ? "当前匹配岗位与理想岗位一致。" : "当前匹配岗位与理想岗位不一致，需按理想岗位补齐差距。"}
                </div>
              </div>
            </div>
            {comparison.differenceSummary ? (
              <p style={{ margin: "14px 0 0", color: "var(--subtle)", lineHeight: 1.7 }}>{comparison.differenceSummary}</p>
            ) : null}
            {comparison.focusRecommendation ? (
              <p style={{ margin: "8px 0 0", color: "#0f766e", lineHeight: 1.7 }}>{comparison.focusRecommendation}</p>
            ) : null}
            {!comparison.sameJob && comparison.missingSkills.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
                {comparison.missingSkills.slice(0, 6).map((skill) => (
                  <span key={skill} style={{ padding: "4px 8px", borderRadius: 8, background: "#fff4e5", color: "#8a4b00", fontSize: "0.75rem", fontWeight: 600 }}>{skill}</span>
                ))}
              </div>
            ) : null}
          </SectionCard>

          <SectionCard title={`报告 #${report?.report_id ?? reportId}`}>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
              <button className="btn-secondary" onClick={() => setEditing((value) => !value)} disabled={Boolean(busy)}>
                {editing ? "预览报告" : "手动编辑"}
              </button>
              <button className="btn-primary" onClick={handleSave} disabled={!canOperate || !editing}>
                {busy === "save" ? "保存中..." : "保存编辑"}
              </button>
              <button className="btn-secondary" onClick={handlePolish} disabled={!canOperate}>
                {busy === "polish" ? "润色中..." : "智能润色"}
              </button>
              <button className="btn-secondary" onClick={handleCheck} disabled={!report || Boolean(busy)}>
                {busy === "check" ? "检查中..." : "完整性检查"}
              </button>
              <button className="btn-secondary" onClick={() => handleExport("pdf")} disabled={!report || Boolean(busy)}>
                {busy === "export-pdf" ? "导出中..." : "导出 PDF"}
              </button>
              <button className="btn-secondary" onClick={() => handleExport("docx")} disabled={!report || Boolean(busy)}>
                {busy === "export-docx" ? "导出中..." : "导出 DOCX"}
              </button>
            </div>

            {notice && <p style={{ color: "#0f766e", margin: "0 0 12px", fontSize: "0.875rem" }}>{notice}</p>}

            {checkResult && (
              <div style={{ padding: 12, borderRadius: 8, background: checkResult.is_complete ? "#ecfdf5" : "#fff7ed", marginBottom: 12 }}>
                <strong>{checkResult.is_complete ? "结构完整" : "需要补充"}</strong>
                <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
                  {checkResult.suggestions.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            )}

            {exportResult && (
              <div style={{ padding: 12, borderRadius: 8, background: "#eef6ff", marginBottom: 12 }}>
                导出文件：
                <a href={exportedUrl(exportResult.exported.file_name)} download={exportResult.exported.file_name} target="_blank" rel="noreferrer" style={{ marginLeft: 8 }}>
                  {exportResult.exported.file_name}
                </a>
                {previewUrl(exportResult) ? (
                  <a href={previewUrl(exportResult) ?? "#"} target="_blank" rel="noreferrer" style={{ marginLeft: 12 }}>
                    网页版预览
                  </a>
                ) : null}
              </div>
            )}

            {editing ? (
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                style={{ width: "100%", minHeight: 520, resize: "vertical", border: "1px solid rgba(0,0,0,0.12)", borderRadius: 8, padding: 14, fontSize: "0.9375rem", lineHeight: 1.7, fontFamily: "inherit" }}
              />
            ) : (
              <div className="ai-report">
                <Markdown>{draft || "暂无报告内容"}</Markdown>
              </div>
            )}
          </SectionCard>

          {/* Teacher feedback section */}
          <SectionCard title="教师点评">
            {feedbackLoading ? (
              <p style={{ textAlign: "center", padding: "20px", color: "#888" }}>加载中...</p>
            ) : teacherFeedback.length > 0 ? (
              <div style={{ display: "grid", gap: 12 }}>
                {teacherFeedback.map((fb) => (
                  <div
                    key={fb.id}
                    style={{
                      border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8,
                      padding: 14, background: "#f8fafc",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>{fb.teacher_name}</span>
                        {fb.priority && fb.priority !== "normal" && (
                          <span style={{
                            padding: "1px 8px", borderRadius: 10, fontSize: "0.7rem", fontWeight: 600,
                            background: fb.priority === "urgent" ? "rgba(239,68,68,0.1)" : fb.priority === "high" ? "rgba(245,158,11,0.1)" : "rgba(107,114,128,0.1)",
                            color: fb.priority === "urgent" ? "#ef4444" : fb.priority === "high" ? "#f59e0b" : "#6b7280",
                          }}>
                            {fb.priority === "urgent" ? "紧急" : fb.priority === "high" ? "高" : fb.priority === "low" ? "低" : fb.priority}
                          </span>
                        )}
                      </div>
                      {fb.created_at && (
                        <span style={{ fontSize: "0.75rem", color: "var(--subtle)" }}>
                          {formatTime(fb.created_at)}
                        </span>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: "0.875rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{fb.comment}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ textAlign: "center", padding: "20px", color: "#888" }}>暂无教师点评</p>
            )}
          </SectionCard>
        </>
      )}
      </div>
    </StudentShellClient>
  );
}

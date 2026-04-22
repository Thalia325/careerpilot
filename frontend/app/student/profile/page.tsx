"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import {
  getStudentSession,
  getStudentProfile,
  generateStudentProfile,
  getProfileVersions,
  getProfileVersionDetail,
  listFiles,
  type StudentProfile as StudentProfileType,
  type ProfileVersionItem,
  type UploadedFileInfo,
} from "@/lib/api";
import { Icon } from "@/components/Icon";
import { formatTime as formatTimeUtil } from "@/lib/format";

const CAPABILITY_LABELS: Record<string, string> = {
  innovation: "创新能力",
  learning: "学习能力",
  resilience: "抗压能力",
  communication: "沟通能力",
  internship: "实习实践",
};

function formatTime(iso: string): string {
  return formatTimeUtil(iso);
}

function CapabilityBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  let color = "#ef4444";
  if (pct >= 80) color = "#22c55e";
  else if (pct >= 60) color = "#3b82f6";
  else if (pct >= 40) color = "#f59e0b";
  return (
    <div className="profile-score-row">
      <div className="profile-score-row__meta">
        <span>{label}</span>
        <strong>{pct} / 100</strong>
      </div>
      <div className="profile-score-row__track">
        <div className="profile-score-row__fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function StudentProfilePage() {
  const searchParams = useSearchParams();
  const versionParam = searchParams.get("version");
  const isFromHistory = searchParams.get("source") === "history";
  const [profile, setProfile] = useState<StudentProfileType | null>(null);
  const [versions, setVersions] = useState<ProfileVersionItem[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<ProfileVersionItem | null>(null);
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const sess = await getStudentSession();
      if (!sess.student_id) { setLoading(false); return; }
      setStudentId(sess.student_id);

      const [f, p, v] = await Promise.all([
        listFiles(),
        getStudentProfile(sess.student_id).catch(() => null),
        getProfileVersions(sess.student_id).catch(() => []),
      ]);
      setFiles(f);
      setProfile(p);
      setVersions(v);

      // Auto-select version from URL param
      if (versionParam) {
        const vId = parseInt(versionParam, 10);
        if (!isNaN(vId)) {
          const found = v.find((item: ProfileVersionItem) => item.id === vId);
          if (found) {
            setSelectedVersion(found);
          } else if (sess.student_id) {
            // Version not in list, try fetching directly
            try {
              const detail = await getProfileVersionDetail(sess.student_id, vId);
              setSelectedVersion(detail as unknown as ProfileVersionItem);
            } catch { /* ignore */ }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载画像数据失败");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleGenerate = async () => {
    if (!studentId || files.length === 0 || generating) return;
    setGenerating(true);
    setError("");
    try {
      const fileIds = files.map((f) => f.id);
      const result = await generateStudentProfile(studentId, fileIds);
      setProfile(result);
      const v = await getProfileVersions(studentId).catch(() => []);
      setVersions(v);
      setSelectedVersion(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成画像失败");
    } finally {
      setGenerating(false);
    }
  };

  const displayData = selectedVersion ? selectedVersion.snapshot : profile;

  const caps = (displayData?.capability_scores ?? {}) as Record<string, number>;
  const evidence = Array.isArray(displayData?.evidence) ? displayData.evidence : [];
  const skills = Array.isArray(displayData?.skills) ? displayData.skills : [];
  const certificates = Array.isArray(displayData?.certificates) ? displayData.certificates : [];
  const hasCapabilities = Object.keys(caps).length > 0;

  return (
    <div className="profile-page">
      <div className="profile-page__header">
        <div className="profile-page__title">
          <h1>我的能力分析</h1>
          {(selectedVersion || (versionParam && isFromHistory)) ? (
            <span className="profile-page__status profile-page__status--history">历史画像</span>
          ) : hasCapabilities ? (
            <span className="profile-page__status profile-page__status--current">当前最新</span>
          ) : null}
        </div>
        <div className="profile-page__actions">
          <Link href="/student" className="profile-page__secondary-action">
            返回问答页
          </Link>
          <button
            onClick={handleGenerate}
            disabled={generating || files.length === 0 || !studentId}
            className="profile-page__primary-action"
          >
            {generating ? "正在分析..." : "重新分析（OCR + AI）"}
          </button>
        </div>
      </div>

      {error ? (
        <div style={{ marginBottom: 16, padding: 12, borderRadius: 10, border: "1px solid rgba(220,38,38,0.18)", background: "rgba(220,38,38,0.06)", color: "#b91c1c" }}>
          {error}
        </div>
      ) : null}

      {files.length === 0 && (
        <EmptyState
          icon={<Icon name="file" size={32} />}
          title="还没有上传材料"
          description="请先上传简历或相关材料，系统将使用 OCR 识别 + AI 分析生成你的能力画像。"
          actionLabel="上传材料"
          actionHref="/student"
        />
      )}

      {loading ? (
        <p style={{ textAlign: "center", padding: 40, color: "#888" }}>加载中...</p>
      ) : !hasCapabilities ? (
        files.length > 0 && (
          <EmptyState
            icon={<Icon name="star" size={32} />}
            title="还没有能力评分数据"
            description="你已上传文件，点击「重新分析」按钮，系统将使用 OCR + AI 为你生成能力画像。"
          />
        )
      ) : (
        <>
          {selectedVersion && (
            <div className="profile-version-notice">
              正在查看历史版本 v{selectedVersion.version_no}（{formatTime(selectedVersion.created_at)}）
              <button
                onClick={() => setSelectedVersion(null)}
                className="profile-version-notice__button"
              >
                返回当前
              </button>
            </div>
          )}

          <div className="profile-page__summary-grid">
            <SectionCard title="能力评分">
              {Object.entries(caps).map(([key, value]) => (
                <CapabilityBar key={key} label={CAPABILITY_LABELS[key] || key} value={value} />
              ))}
              <div className="profile-metrics">
                {displayData?.completeness_score != null && (
                  <div className="profile-metric">
                    <span>档案完整度</span>
                    <strong>{displayData.completeness_score}%</strong>
                  </div>
                )}
                {displayData?.competitiveness_score != null && (
                  <div className="profile-metric">
                    <span>竞争力</span>
                    <strong>{displayData.competitiveness_score}</strong>
                  </div>
                )}
              </div>
            </SectionCard>

            <div className="profile-page__side-stack">
              {skills.length > 0 && (
                <SectionCard title="技能标签">
                  <div className="profile-tags">
                    {skills.map((s) => (
                      <span key={String(s)} className="profile-tag">
                        {String(s)}
                      </span>
                    ))}
                  </div>
                </SectionCard>
              )}

              {certificates.length > 0 && (
                <SectionCard title="证书资质">
                  <ul className="profile-cert-list">
                    {certificates.map((c) => <li key={String(c)}>{String(c)}</li>)}
                  </ul>
                </SectionCard>
              )}
            </div>
          </div>

          {displayData?.source_summary && (
            <SectionCard title="分析来源">
              <p className="profile-source-text">{displayData.source_summary}</p>
            </SectionCard>
          )}

          {evidence.length > 0 && (
            <SectionCard title="证据链">
              <ul className="profile-evidence-list">
                {evidence.map((item: { source: string; excerpt: string; confidence: number }, i: number) => (
                  <li key={`${item.source}-${i}`}>
                    <span className="profile-evidence-list__source">{item.source}</span>
                    <span className="profile-evidence-list__excerpt">{item.excerpt}</span>
                    <span className="profile-evidence-list__confidence">置信度 {item.confidence}</span>
                  </li>
                ))}
              </ul>
            </SectionCard>
          )}
        </>
      )}

      {versions.length > 0 && (
        <SectionCard title="历史画像版本">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {versions.map((v) => {
              const isSelected = selectedVersion?.id === v.id;
              const summaries = v.file_summaries ?? [];
              return (
                <button
                  key={v.id}
                  onClick={async () => {
                    if (isSelected) {
                      setSelectedVersion(null);
                    } else {
                      // Load full version detail with snapshot
                      if (studentId) {
                        try {
                          const detail = await getProfileVersionDetail(studentId, v.id);
                          setSelectedVersion(detail);
                        } catch {
                          setSelectedVersion(v);
                        }
                      } else {
                        setSelectedVersion(v);
                      }
                    }
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "14px 16px",
                    borderRadius: 10,
                    border: isSelected ? "2px solid var(--brand-2)" : "1px solid rgba(0,0,0,0.08)",
                    background: isSelected ? "rgba(15,116,218,0.06)" : "#fff",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    textAlign: "left",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: summaries.length > 0 ? 8 : 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <strong style={{ fontSize: "0.9375rem" }}>版本 {v.version_no}</strong>
                      {v.source_files && (
                        <span style={{ color: "var(--subtle)", fontSize: "0.8125rem" }}>
                          {v.source_files.length > 50 ? v.source_files.slice(0, 50) + "…" : v.source_files}
                        </span>
                      )}
                    </div>
                    <span style={{ color: "var(--subtle)", fontSize: "0.8125rem", whiteSpace: "nowrap", marginLeft: 12 }}>
                      {formatTime(v.created_at)}
                    </span>
                  </div>
                  {summaries.length > 0 && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
                      {summaries.map((fs, idx) => (
                        <div key={idx} style={{ display: "flex", alignItems: "baseline", gap: 6, fontSize: "0.8125rem", color: "var(--subtle)" }}>
                          <span style={{
                            padding: "1px 6px",
                            borderRadius: 4,
                            background: fs.file_type === "resume" ? "rgba(15,116,218,0.1)" : "rgba(12,179,166,0.1)",
                            color: fs.file_type === "resume" ? "var(--brand)" : "var(--brand-2)",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            whiteSpace: "nowrap",
                          }}>
                            {fs.file_type === "resume" ? "简历" : fs.file_type === "certificate" ? "证书" : fs.file_type === "transcript" ? "成绩单" : fs.file_type}
                          </span>
                          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {fs.summary || fs.file_name}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

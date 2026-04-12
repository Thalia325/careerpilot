"use client";

import { useState, useEffect, useCallback } from "react";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import {
  getStudentSession,
  getStudentProfile,
  generateStudentProfile,
  getProfileVersions,
  listFiles,
  type StudentProfile as StudentProfileType,
  type ProfileVersionItem,
  type UploadedFileInfo,
} from "@/lib/api";
import { Icon } from "@/components/Icon";

const CAPABILITY_LABELS: Record<string, string> = {
  innovation: "创新能力",
  learning: "学习能力",
  resilience: "抗压能力",
  communication: "沟通能力",
  internship: "实习实践",
};

function formatTime(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function CapabilityBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  let color = "#ef4444";
  if (pct >= 80) color = "#22c55e";
  else if (pct >= 60) color = "#3b82f6";
  else if (pct >= 40) color = "#f59e0b";
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: "0.875rem", color: "var(--subtle)" }}>{pct} / 100</span>
      </div>
      <div style={{ height: 10, borderRadius: 5, background: "rgba(0,0,0,0.06)", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", borderRadius: 5, background: color, transition: "width 0.4s ease" }} />
      </div>
    </div>
  );
}

export default function StudentProfilePage() {
  const [profile, setProfile] = useState<StudentProfileType | null>(null);
  const [versions, setVersions] = useState<ProfileVersionItem[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<ProfileVersionItem | null>(null);
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [studentId, setStudentId] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
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
    } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleGenerate = async () => {
    if (!studentId || files.length === 0 || generating) return;
    setGenerating(true);
    try {
      const fileIds = files.map((f) => f.id);
      const result = await generateStudentProfile(studentId, fileIds);
      setProfile(result);
      const v = await getProfileVersions(studentId).catch(() => []);
      setVersions(v);
      setSelectedVersion(null);
    } catch (err) {
      console.error("Generate profile failed:", err);
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
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>我的能力分析</h1>
        <button
          onClick={handleGenerate}
          disabled={generating || files.length === 0 || !studentId}
          style={{
            padding: "10px 20px",
            borderRadius: 10,
            border: "none",
            background: generating ? "#999" : "linear-gradient(135deg, var(--brand), var(--brand-2))",
            color: "#fff",
            fontWeight: 700,
            fontSize: "0.875rem",
            cursor: generating ? "not-allowed" : "pointer",
            opacity: generating ? 0.6 : 1,
          }}
        >
          {generating ? "正在分析..." : "重新分析（OCR + AI）"}
        </button>
      </div>

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
            <div style={{ padding: "10px 16px", background: "rgba(15,116,218,0.06)", borderRadius: 10, marginBottom: 16, fontSize: "0.875rem", color: "var(--brand)" }}>
              正在查看历史版本 v{selectedVersion.version_no}（{formatTime(selectedVersion.created_at)}）
              <button
                onClick={() => setSelectedVersion(null)}
                style={{ marginLeft: 12, background: "none", border: "1px solid var(--brand)", color: "var(--brand)", padding: "2px 10px", borderRadius: 6, cursor: "pointer", fontSize: "0.8125rem", minHeight: 24 }}
              >
                返回当前
              </button>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <SectionCard title="能力评分">
              {Object.entries(caps).map(([key, value]) => (
                <CapabilityBar key={key} label={CAPABILITY_LABELS[key] || key} value={value} />
              ))}
              <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
                {displayData?.completeness_score != null && (
                  <div style={{ padding: "8px 14px", borderRadius: 8, background: "rgba(12,179,166,0.08)", fontSize: "0.8125rem" }}>
                    档案完整度：<strong>{displayData.completeness_score}%</strong>
                  </div>
                )}
                {displayData?.competitiveness_score != null && (
                  <div style={{ padding: "8px 14px", borderRadius: 8, background: "rgba(15,116,218,0.08)", fontSize: "0.8125rem" }}>
                    竞争力：<strong>{displayData.competitiveness_score}</strong>
                  </div>
                )}
              </div>
            </SectionCard>

            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {skills.length > 0 && (
                <SectionCard title="技能标签">
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {skills.map((s) => (
                      <span key={String(s)} style={{ padding: "4px 12px", borderRadius: 20, background: "rgba(15,116,218,0.08)", color: "var(--brand)", fontSize: "0.8125rem", fontWeight: 600 }}>
                        {String(s)}
                      </span>
                    ))}
                  </div>
                </SectionCard>
              )}

              {certificates.length > 0 && (
                <SectionCard title="证书资质">
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {certificates.map((c) => <li key={String(c)} style={{ fontSize: "0.875rem", marginBottom: 4 }}>{String(c)}</li>)}
                  </ul>
                </SectionCard>
              )}
            </div>
          </div>

          {displayData?.source_summary && (
            <SectionCard title="分析来源">
              <p style={{ fontSize: "0.875rem", color: "var(--subtle)", margin: 0 }}>{displayData.source_summary}</p>
            </SectionCard>
          )}

          {evidence.length > 0 && (
            <SectionCard title="证据链">
              <ul className="plain-list">
                {evidence.map((item: { source: string; excerpt: string; confidence: number }, i: number) => (
                  <li key={`${item.source}-${i}`}>
                    <strong>{item.source}</strong>：{item.excerpt}（置信度 {item.confidence}）
                  </li>
                ))}
              </ul>
            </SectionCard>
          )}
        </>
      )}

      {versions.length > 1 && (
        <SectionCard title="历史记录">
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {versions.map((v) => (
              <button
                key={v.id}
                onClick={() => setSelectedVersion(selectedVersion?.id === v.id ? null : v)}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px 16px",
                  borderRadius: 10,
                  border: selectedVersion?.id === v.id ? "2px solid var(--brand-2)" : "1px solid rgba(0,0,0,0.08)",
                  background: selectedVersion?.id === v.id ? "rgba(15,116,218,0.06)" : "#fff",
                  cursor: "pointer",
                  fontSize: "0.875rem",
                  textAlign: "left",
                }}
              >
                <div>
                  <strong>v{v.version_no}</strong>
                  <span style={{ color: "var(--subtle)", marginLeft: 8, fontSize: "0.8125rem" }}>
                    {v.source_files ? v.source_files.slice(0, 60) : "手动录入"}
                  </span>
                </div>
                <span style={{ color: "var(--subtle)", fontSize: "0.8125rem" }}>
                  {formatTime(v.created_at)}
                </span>
              </button>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

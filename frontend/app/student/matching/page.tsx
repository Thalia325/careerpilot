"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getStudentSession, getMatching, getMatchResult } from "@/lib/api";
import { Icon } from "@/components/Icon";

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score)) / 100;
  const offset = circumference * (1 - progress);
  const color =
    score >= 90 ? "#43a047" : score >= 80 ? "#66bb6a" : score >= 70 ? "#ffa726" : score >= 60 ? "#fb8c00" : "#e53935";

  return (
    <div style={{ position: "relative", width: size, height: size, margin: "0 auto" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e0e0e0" strokeWidth="8" />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center"
      }}>
        <span style={{ fontSize: "1.75rem", fontWeight: 700, color }}>{score.toFixed(1)}</span>
        <span style={{ fontSize: "0.75rem", color: "#888" }}>综合得分</span>
      </div>
    </div>
  );
}

function dimensionColor(score: number): string {
  if (score >= 90) return "#43a047";
  if (score >= 80) return "#66bb6a";
  if (score >= 70) return "#ffa726";
  if (score >= 60) return "#fb8c00";
  return "#e53935";
}

export default function StudentMatchingPage() {
  const searchParams = useSearchParams();
  const historyId = searchParams.get("history");
  const [dimensions, setDimensions] = useState<Array<{ dimension: string; score: number; weight: number; reasoning: string }>>([]);
  const [gapItems, setGapItems] = useState<Array<{ name: string; suggestion: string }>>([]);
  const [strengths, setStrengths] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [totalScore, setTotalScore] = useState<number>(0);
  const [summary, setSummary] = useState("暂无数据");
  const [loading, setLoading] = useState(true);
  const [isHistoricalView, setIsHistoricalView] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Extract match ID from history parameter (format: "match-{id}")
        if (historyId && historyId.startsWith("match-")) {
          const matchId = parseInt(historyId.replace("match-", ""), 10);
          if (!isNaN(matchId)) {
            setIsHistoricalView(true);
            const matching = await getMatchResult(matchId);
            applyMatching(matching);
            setLoading(false);
            return;
          }
        }

        // Load latest data
        const sess = await getStudentSession();
        const jobCode = sess.resolved_job_code || sess.target_job_code || sess.suggested_job_code || "";
        if (!sess.student_id || !jobCode) { setLoading(false); return; }
        const matching = await getMatching(sess.student_id, jobCode);
        applyMatching(matching);
      } catch {} finally { setLoading(false); }
    })();
  }, [historyId]);

  function applyMatching(matching: Record<string, unknown> | null | undefined) {
    if (!matching) return;
    setDimensions(Array.isArray(matching?.dimensions) ? matching.dimensions as typeof dimensions : []);
    setGapItems(Array.isArray(matching?.gap_items) ? matching.gap_items as typeof gapItems : []);
    setStrengths(Array.isArray(matching?.strengths) ? matching.strengths as string[] : []);
    setSuggestions(Array.isArray(matching?.suggestions) ? matching.suggestions as string[] : []);
    setTotalScore(typeof matching?.total_score === "number" ? matching.total_score : 0);
    setSummary(typeof matching?.summary === "string" ? matching.summary : "暂无数据");
  }

  const hasAnalysis = dimensions.length > 0;

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>匹配分析</h1>
            {isHistoricalView && (
              <p style={{ fontSize: "0.875rem", color: "#f57c00", margin: "4px 0 0" }}>
                ⚠️ 正在查看历史数据
              </p>
            )}
          </div>
          <Link href="/student" className="btn-secondary" style={{ textDecoration: "none", padding: "10px 14px", fontSize: "0.875rem" }}>
            返回问答页
          </Link>
        </div>
        {loading ? (
          <SectionCard title="加载中">
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          </SectionCard>
        ) : !hasAnalysis ? (
          <EmptyState
            icon={<Icon name="target" size={32} />}
            title="还没有匹配分析结果"
            description="上传简历并指定目标岗位后，系统将进行四维评分分析，识别你的优势和需要提升的能力。"
            actionLabel="开始智能匹配"
            actionHref="/student/upload"
          />
        ) : (
          <>
            {/* Total Score */}
            <SectionCard title="综合匹配得分">
              <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
                <ScoreRing score={totalScore} />
                <div style={{ flex: 1, minWidth: 200 }}>
                  <p style={{ margin: "0 0 8px", fontSize: "0.95rem", color: "#555" }}>
                    {totalScore >= 80
                      ? "你与目标岗位整体契合度较高，建议继续巩固优势并补齐短板。"
                      : totalScore >= 60
                        ? "你与目标岗位有一定差距，建议参照下方差距项和提升建议有针对性地补强。"
                        : "你与目标岗位差距较大，建议重新审视目标或系统性地提升相关能力。"}
                  </p>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    {dimensions.map((d) => (
                      <span key={d.dimension} style={{
                        padding: "4px 10px", borderRadius: 12, fontSize: "0.8rem",
                        background: "#f5f5f5", color: dimensionColor(d.score), fontWeight: 600
                      }}>
                        {d.dimension} {d.score}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </SectionCard>

            <div className="comparison-grid">
              {/* Four-dimension scores */}
              <SectionCard title="四维评分详情">
                <table className="comparison-table" aria-label="四维评分对比表">
                  <thead>
                    <tr>
                      <th>评分方面</th>
                      <th>得分</th>
                      <th>权重</th>
                      <th>评价</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dimensions.map((item) => (
                      <tr key={item.dimension}>
                        <td><strong>{item.dimension}</strong></td>
                        <td>
                          <span style={{ color: dimensionColor(item.score), fontWeight: 600 }}>{item.score}</span> 分
                        </td>
                        <td>{(item.weight * 100).toFixed(0)}%</td>
                        <td>{item.reasoning}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </SectionCard>

              {/* Strengths */}
              <SectionCard title="契合点">
                {strengths.length === 0 ? (
                  <p className="empty-message">暂无契合点数据</p>
                ) : (
                  <ul className="plain-list">
                    {strengths.map((s, i) => (
                      <li key={i} style={{ marginBottom: 6 }}>
                        <span style={{ color: "#43a047", marginRight: 6 }}>&#10003;</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            <div className="comparison-grid">
              {/* Gap items */}
              <SectionCard title="差距项">
                {gapItems.length === 0 ? (
                  <p className="empty-message">完美匹配！</p>
                ) : (
                  <ul className="plain-list">
                    {gapItems.map((gap) => (
                      <li key={gap.name} style={{ marginBottom: 6 }}>
                        <strong style={{ color: "#e53935" }}>{gap.name}</strong>
                        <p style={{ margin: "2px 0 0", color: "#666", fontSize: "0.9rem" }}>{gap.suggestion}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              {/* Suggestions */}
              <SectionCard title="提升建议">
                {suggestions.length === 0 ? (
                  <p className="empty-message">暂无提升建议</p>
                ) : (
                  <ul className="plain-list">
                    {suggestions.map((s, i) => (
                      <li key={i} style={{ marginBottom: 6 }}>
                        <span style={{ color: "#1976d2", marginRight: 6, fontWeight: 700 }}>{i + 1}.</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            <SectionCard title="综合结论">
              <p>{summary}</p>
            </SectionCard>
          </>
        )}
    </div>
  );
}

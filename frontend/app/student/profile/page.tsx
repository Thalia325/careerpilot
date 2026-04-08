"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getStudentProfile } from "@/lib/api";
import { StudentShellClient } from "@/components/StudentShellClient";

export default function StudentProfilePage() {
  const [caps, setCaps] = useState<Record<string, number>>({});
  const [evidence, setEvidence] = useState<Array<{ source: string; excerpt: string; confidence: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStudentProfile()
      .then((profile) => {
        setCaps((profile?.capability_scores ?? {}) as Record<string, number>);
        setEvidence(Array.isArray(profile?.evidence) ? profile.evidence : []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hasCapabilities = Object.keys(caps).length > 0;

  return (
    <StudentShellClient title="我的能力分析">
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <SectionCard title="能力评分">
          {loading ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          ) : !hasCapabilities ? (
            <EmptyState
              icon="⭐"
              title="还没有能力评分数据"
              description="上传简历和相关材料后，系统将智能识别和评估你的专业能力、技能水平和竞争优势。"
              actionLabel="上传材料"
              actionHref="/student/upload"
            />
          ) : (
            <div className="card-grid">
              {Object.entries(caps).map(([key, value]) => (
                <div className="feature-item" key={key}>
                  <strong>{key}</strong>
                  <p>{value} / 100</p>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
        {hasCapabilities && (
          <SectionCard title="证据链">
            {evidence.length === 0 ? (
              <EmptyState
                icon="🔗"
                title="还没有证据链数据"
                description="系统将从你提交的材料中提取能力证据，作为评分的支持依据。"
              />
            ) : (
              <ul className="plain-list">
                {evidence.map((item: { source: string; excerpt: string; confidence: number }) => (
                  <li key={`${item.source}-${item.excerpt}`}>
                    <strong>{item.source}</strong>：{item.excerpt}（置信度 {item.confidence}）
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        )}
      </div>
    </StudentShellClient>
  );
}

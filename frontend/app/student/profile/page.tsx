import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getStudentProfile } from "@/lib/api";

export const metadata: Metadata = {
  title: "就业能力画像 - CareerPilot",
  description: "查看个人能力评分、证书材料和能力证据链"
};

export default async function StudentProfilePage() {
  const profile = await getStudentProfile();
  const caps = (profile?.capability_scores ?? {}) as Record<string, number>;
  const evidence = Array.isArray(profile?.evidence) ? profile.evidence : [];
  const hasCapabilities = Object.keys(caps).length > 0;

  return (
    <AppShell title="学生就业能力画像" subtitle="融合 OCR 结果与手动输入，生成完整度评分、竞争力评分与证据链。">
      <SectionCard title="能力评分">
        {!hasCapabilities ? (
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
    </AppShell>
  );
}


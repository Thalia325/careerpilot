import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getMatching } from "@/lib/api";

export const metadata: Metadata = {
  title: "人岗匹配分析 - CareerPilot",
  description: "基于四维评分分析与目标岗位的匹配度和提升建议"
};

export default async function StudentMatchingPage() {
  const matching = await getMatching();

  const dimensions = Array.isArray(matching?.dimensions) ? matching.dimensions : [];
  const gapItems = Array.isArray(matching?.gap_items) ? matching.gap_items : [];
  const summary = matching?.summary ?? "暂无数据";
  const hasAnalysis = dimensions.length > 0;

  return (
    <AppShell title="人岗匹配分析" subtitle="严格按基础要求、职业技能、职业素养、发展潜力四维打分，并支持岗位权重差异化。">
      {!hasAnalysis ? (
        <EmptyState
          icon="🎯"
          title="还没有匹配分析结果"
          description="上传简历并指定目标岗位后，系统将进行四维评分分析，识别你的优势和需要提升的能力。"
          actionLabel="开始智能匹配"
          actionHref="/student/upload"
        />
      ) : (
        <>
          <div className="comparison-grid">
            <SectionCard title="四维评分">
              <table className="comparison-table" aria-label="四维评分对比表">
                <thead>
                  <tr>
                    <th>评分维度</th>
                    <th>得分</th>
                    <th>权重</th>
                    <th>评价</th>
                  </tr>
                </thead>
                <tbody>
                  {dimensions.map((item: { dimension: string; score: number; weight: number; reasoning: string }) => (
                    <tr key={item.dimension}>
                      <td><strong>{item.dimension}</strong></td>
                      <td>{item.score} 分</td>
                      <td>{item.weight}</td>
                      <td>{item.reasoning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </SectionCard>
            <SectionCard title="差距项与提升建议">
              {gapItems.length === 0 ? (
                <p className="empty-message">完美匹配！</p>
              ) : (
                <ul className="plain-list">
                  {gapItems.map((gap: { name: string; suggestion: string }) => (
                    <li key={gap.name}>
                      <strong>{gap.name}</strong>：{gap.suggestion}
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
    </AppShell>
  );
}


import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getMatching } from "@/lib/api";

export default async function StudentMatchingPage() {
  const matching = await getMatching();

  return (
    <AppShell title="人岗匹配分析" subtitle="严格按基础要求、职业技能、职业素养、发展潜力四维打分，并支持岗位权重差异化。">
      <div className="comparison-grid">
        <SectionCard title="四维评分">
          <ul className="plain-list">
            {matching.dimensions.map((item: { dimension: string; score: number; weight: number; reasoning: string }) => (
              <li key={item.dimension}>
                <strong>{item.dimension}</strong>：{item.score} 分，权重 {item.weight}。{item.reasoning}
              </li>
            ))}
          </ul>
        </SectionCard>
        <SectionCard title="差距项与提升建议">
          <ul className="plain-list">
            {matching.gap_items.map((gap: { name: string; suggestion: string }) => (
              <li key={gap.name}>
                <strong>{gap.name}</strong>：{gap.suggestion}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
      <SectionCard title="综合结论">
        <p>{matching.summary}</p>
      </SectionCard>
    </AppShell>
  );
}


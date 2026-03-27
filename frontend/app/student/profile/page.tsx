import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getStudentProfile } from "@/lib/api";

export default async function StudentProfilePage() {
  const profile = await getStudentProfile();
  const caps = profile.capability_scores as Record<string, number>;

  return (
    <AppShell title="学生就业能力画像" subtitle="融合 OCR 结果与手动输入，生成完整度评分、竞争力评分与证据链。">
      <SectionCard title="能力项评分">
        <div className="card-grid">
          {Object.entries(caps).map(([key, value]) => (
            <div className="feature-item" key={key}>
              <strong>{key}</strong>
              <p>{value} / 100</p>
            </div>
          ))}
        </div>
      </SectionCard>
      <SectionCard title="证据链">
        <ul className="plain-list">
          {profile.evidence.map((item: { source: string; excerpt: string; confidence: number }) => (
            <li key={`${item.source}-${item.excerpt}`}>
              <strong>{item.source}</strong>：{item.excerpt}（置信度 {item.confidence}）
            </li>
          ))}
        </ul>
      </SectionCard>
    </AppShell>
  );
}


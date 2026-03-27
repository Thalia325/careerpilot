import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getJobTemplates } from "@/lib/api";

export default async function StudentJobsPage() {
  const templates = await getJobTemplates();

  return (
    <AppShell title="岗位探索与岗位画像" subtitle="系统内置 10+ 岗位画像模板，可持续导入企业岗位数据并增量构建知识库。">
      <SectionCard title="当前岗位模板">
        <div className="card-grid">
          {templates.map((item: { title: string }) => (
            <div className="feature-item" key={item.title}>
              <strong>{item.title}</strong>
              <p>支持查看技能要求、能力说明、证书要求与图谱路径。</p>
            </div>
          ))}
        </div>
      </SectionCard>
    </AppShell>
  );
}


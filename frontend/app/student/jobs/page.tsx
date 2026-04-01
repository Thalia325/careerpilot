import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getJobTemplates } from "@/lib/api";

export const metadata: Metadata = {
  title: "岗位探索 - CareerPilot",
  description: "浏览岗位画像模板，了解岗位要求和能力要求"
};

export default async function StudentJobsPage() {
  const templates = await getJobTemplates();
  const templateList = Array.isArray(templates) ? templates : [];

  return (
    <AppShell title="岗位探索与岗位画像" subtitle="系统内置 10+ 岗位画像模板，可持续导入企业岗位数据并增量构建知识库。">
      <SectionCard title="当前岗位画像">
        {templateList.length === 0 ? (
          <EmptyState
            icon="📋"
            title="还没有岗位画像数据"
            description="系统内置的岗位画像模板将在这里显示。你可以浏览各类岗位要求，帮助更好地了解职业方向。"
            actionLabel="前往管理后台"
            actionHref="/admin"
          />
        ) : (
          <div className="card-grid">
            {templateList.map((item: { title: string }) => (
              <div className="feature-item" key={item.title}>
                <strong>{item.title}</strong>
                <p>支持查看技能要求、能力说明、证书要求与图谱路径。</p>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </AppShell>
  );
}


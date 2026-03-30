import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { EditableReport } from "@/components/EditableReport";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { generateDemoReport } from "@/lib/api";

export const metadata: Metadata = {
  title: "报告编辑 - CareerPilot",
  description: "编辑和导出职业规划报告"
};

export default async function StudentReportsPage() {
  const report = await generateDemoReport();

  return (
    <AppShell title="报告编辑与导出" subtitle="支持智能润色、完整性检查、手动编辑调整以及 PDF / DOCX 导出。">
      <SectionCard title="报告编辑器">
        {!report?.markdown_content ? (
          <EmptyState
            icon="📄"
            title="还没有分析报告"
            description="完成材料上传和智能分析后，系统将为你生成职业规划报告。你可以在这里编辑、优化和导出报告。"
            actionLabel="开始上传材料"
            actionHref="/student/upload"
          />
        ) : (
          <EditableReport initialMarkdown={report.markdown_content} />
        )}
      </SectionCard>
    </AppShell>
  );
}


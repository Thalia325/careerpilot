import { AppShell } from "@/components/AppShell";
import { EditableReport } from "@/components/EditableReport";
import { SectionCard } from "@/components/SectionCard";
import { generateDemoReport } from "@/lib/api";

export default async function StudentReportsPage() {
  const report = await generateDemoReport();

  return (
    <AppShell title="报告编辑与导出" subtitle="支持智能润色、完整性检查、手动编辑调整以及 PDF / DOCX 导出。">
      <SectionCard title="报告编辑器">
        <EditableReport initialMarkdown={report.markdown_content} />
      </SectionCard>
    </AppShell>
  );
}


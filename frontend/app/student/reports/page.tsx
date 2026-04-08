"use client";

import { useState, useEffect } from "react";
import { EditableReport } from "@/components/EditableReport";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { generateDemoReport } from "@/lib/api";
import { StudentShellClient } from "@/components/StudentShellClient";

export default function StudentReportsPage() {
  const [report, setReport] = useState<{ markdown_content?: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateDemoReport()
      .then((data) => setReport(data))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <StudentShellClient title="职业规划报告">
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <SectionCard title="报告编辑器">
          {loading ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          ) : !report?.markdown_content ? (
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
      </div>
    </StudentShellClient>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SectionCard } from "@/components/SectionCard";
import { generateReport, getRecommendedJobs, getStudentHistory, getStudentSession, type HistoryItem } from "@/lib/api";

export default function StudentReportEntryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("正在读取最新 OCR 简历与推荐岗位...");
  const [error, setError] = useState("");
  const [reports, setReports] = useState<HistoryItem[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function buildCurrentReport() {
      setLoading(true);
      setError("");
      try {
        const [session, jobs, history] = await Promise.all([
          getStudentSession(),
          getRecommendedJobs(),
          getStudentHistory(),
        ]);
        if (cancelled) return;

        const reportItems = history.filter((item) => item.type === "report");
        setReports(reportItems);

        if (!session.student_id) {
          setError("当前账号还没有学生档案，请先回到问答页上传简历并生成能力画像。");
          return;
        }

        const targetJob = jobs.find((job) => job.job_code);
        if (!targetJob) {
          setError("暂时没有基于最新简历算出的推荐岗位，请先完成 OCR 简历解析和岗位推荐。");
          return;
        }

        setMessage(`正在基于最新 OCR 简历生成完整报告：${targetJob.title}`);
        const report = await generateReport(session.student_id, targetJob.job_code);
        if (!cancelled) {
          router.replace(`/results/${report.report_id}`);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "生成完整报告失败，请稍后重试。");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    buildCurrentReport();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const hasReports = reports.length > 0;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px" }}>
      <SectionCard title="完整报告">
        {loading ? (
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <h2 style={{ margin: "0 0 10px", fontSize: "1.125rem" }}>正在生成当前简历报告</h2>
            <p style={{ color: "var(--subtle)", margin: 0 }}>{message}</p>
          </div>
        ) : error ? (
          <div style={{ display: "grid", gap: 16, padding: "24px 0" }}>
            <div style={{ padding: 16, borderRadius: 8, border: "1px solid rgba(220,38,38,0.2)", background: "rgba(220,38,38,0.04)" }}>
              <strong>没有打开旧报告</strong>
              <p style={{ color: "var(--subtle)", margin: "8px 0 0" }}>{error}</p>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link href="/student" className="btn-primary" style={{ textDecoration: "none", padding: "10px 16px" }}>
                回到问答页
              </Link>
              <Link href="/student/recommended" className="btn-secondary" style={{ textDecoration: "none", padding: "10px 16px" }}>
                查看推荐岗位
              </Link>
            </div>
            {hasReports ? <HistoryReportList reports={reports} /> : null}
          </div>
        ) : hasReports ? (
          <HistoryReportList reports={reports} />
        ) : (
          <div style={{ textAlign: "center", padding: "40px 20px" }}>
            <h2 style={{ margin: "0 0 10px", fontSize: "1.125rem" }}>还没有完整报告</h2>
            <p style={{ color: "var(--subtle)", margin: "0 0 18px" }}>先上传简历并完成岗位匹配分析，系统会生成完整职业发展报告。</p>
            <Link href="/student" className="btn-primary" style={{ textDecoration: "none", padding: "10px 16px" }}>
              去生成报告
            </Link>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

function HistoryReportList({ reports }: { reports: HistoryItem[] }) {
  return (
    <div>
      <h3 style={{ margin: "0 0 12px", fontSize: "1rem" }}>历史报告</h3>
      <div style={{ display: "grid", gap: 10 }}>
        {reports.map((report) => (
          <Link
            key={report.id}
            href={`/results/${report.ref_id}`}
            style={{ display: "block", padding: 14, borderRadius: 8, border: "1px solid rgba(0,0,0,0.08)", textDecoration: "none", color: "inherit" }}
          >
            <strong>{report.title}</strong>
            <p style={{ margin: "6px 0 0", color: "var(--subtle)", fontSize: "0.875rem" }}>{report.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

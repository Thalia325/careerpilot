import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getJobTemplates, getSchedulerJobs } from "@/lib/api";

export default async function AdminPage() {
  const templates = await getJobTemplates();
  const schedulerJobs = await getSchedulerJobs();

  return (
    <AppShell title="管理后台" subtitle="管理岗位数据、知识库、图谱、系统配置与调度任务，支撑比赛演示与后续产品化扩展。">
      <SectionCard title="岗位与知识库">
        <ul className="plain-list">
          <li>内置岗位画像模板：{templates.length} 个</li>
          <li>支持岗位数据导入、清洗标准化、RAGFlow 知识入库、Neo4j 图谱同步</li>
          <li>支持 10000 条岗位数据导入脚本与初始化脚本复跑</li>
        </ul>
      </SectionCard>
      <SectionCard title="调度监控">
        <ul className="plain-list">
          {schedulerJobs.map((job: { job_name: string; cron_expr: string; status: string; job_type: string }) => (
            <li key={job.job_name}>
              <strong>{job.job_name}</strong>：{job.job_type} / {job.cron_expr} / {job.status}
            </li>
          ))}
        </ul>
      </SectionCard>
    </AppShell>
  );
}


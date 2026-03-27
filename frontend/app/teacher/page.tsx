import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getMatching, getStudentProfile } from "@/lib/api";

export default async function TeacherPage() {
  const profile = await getStudentProfile();
  const matching = await getMatching();

  return (
    <AppShell title="教师工作台" subtitle="查看学生画像、匹配分析结果和行动建议，提供点评与跟踪方向。">
      <SectionCard title="学生概览">
        <ul className="plain-list">
          <li>目标岗位：前端开发工程师</li>
          <li>画像完整度：{profile.completeness_score}</li>
          <li>竞争力评分：{profile.competitiveness_score}</li>
          <li>当前匹配度：{matching.total_score}</li>
        </ul>
      </SectionCard>
      <SectionCard title="教师点评建议">
        <ul className="plain-list">
          <li>建议学生在 2 周内补齐 HTML/CSS 基础表达与作品展示。</li>
          <li>建议增加一段带业务指标的项目描述，提升简历说服力。</li>
          <li>建议按月复盘成长任务完成率，并同步更新职业目标。</li>
        </ul>
      </SectionCard>
    </AppShell>
  );
}


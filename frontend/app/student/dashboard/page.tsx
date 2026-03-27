import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { getMatching, getPathPlan, getStudentProfile } from "@/lib/api";

export default async function StudentDashboardPage() {
  const profile = await getStudentProfile();
  const matching = await getMatching();
  const pathPlan = await getPathPlan();

  return (
    <AppShell title="学生首页" subtitle="从材料解析到生涯规划闭环，一站式查看当前职业准备情况。">
      <div className="stats-grid">
        <StatCard label="画像完整度" value={`${profile.completeness_score}`} note="基于上传材料与手动输入综合评估" />
        <StatCard label="竞争力评分" value={`${profile.competitiveness_score}`} note="聚焦目标岗位与市场要求" />
        <StatCard label="目标岗位匹配" value={`${matching.total_score}`} note="四维加权综合得分" />
        <StatCard label="主路径长度" value={`${pathPlan.primary_path.length} 阶段`} note="图谱推荐职业成长路径" />
      </div>
      <SectionCard title="当前优势">
        <div className="badge-list">
          {profile.skills.slice(0, 6).map((skill: string) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
      </SectionCard>
      <SectionCard title="近期行动建议">
        <ul className="timeline">
          {matching.suggestions.map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </SectionCard>
    </AppShell>
  );
}


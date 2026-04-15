"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { getStudentSession, getStudentProfile, getMatching, getPathPlan } from "@/lib/api";

export default function DashboardPage() {
  const [profile, setProfile] = useState<{ skills?: string[]; completeness_score?: number; competitiveness_score?: number } | null>(null);
  const [matching, setMatching] = useState<{ suggestions?: string[]; total_score?: number } | null>(null);
  const [pathPlan, setPathPlan] = useState<{ primary_path?: string[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const sess = await getStudentSession();
        const jobCode = sess.target_job_code || sess.suggested_job_code || "";
        if (!sess.student_id || !jobCode) {
          setLoading(false);
          return;
        }
        const [p, m, plan] = await Promise.all([
          getStudentProfile(sess.student_id).catch(() => null),
          getMatching(sess.student_id, jobCode).catch(() => null),
          getPathPlan(sess.student_id, jobCode).catch(() => null),
        ]);
        if (p) setProfile(p);
        if (m) setMatching(m);
        if (plan) setPathPlan(plan);
      } catch {
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const skills = Array.isArray(profile?.skills) ? profile.skills : [];
  const suggestions = Array.isArray(matching?.suggestions) ? matching.suggestions : [];
  const primaryPath = Array.isArray(pathPlan?.primary_path) ? pathPlan.primary_path : [];

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        {loading ? (
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        ) : (
          <>
            <div className="stats-grid">
              <StatCard
                label="档案完整度"
                value={profile?.completeness_score != null ? `${profile.completeness_score}` : "-"}
                note="基于上传材料与手动输入综合评估"
              />
              <StatCard
                label="竞争力评分"
                value={profile?.competitiveness_score != null ? `${profile.competitiveness_score}` : "-"}
                note="聚焦目标岗位与市场要求"
              />
              <StatCard
                label="目标岗位匹配"
                value={matching?.total_score != null ? `${matching.total_score}` : "-"}
                note="四维加权综合得分"
              />
              <StatCard
                label="主路径长度"
                value={primaryPath.length > 0 ? `${primaryPath.length} 阶段` : "-"}
                note="图谱推荐职业成长路径"
              />
            </div>
            <SectionCard title="当前优势">
              <div className="badge-list">
                {skills.slice(0, 6).map((skill: string) => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>
            </SectionCard>
            <SectionCard title="近期行动建议">
              <ul className="timeline">
                {suggestions.map((item: string) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </SectionCard>
          </>
        )}
    </div>
  );
}

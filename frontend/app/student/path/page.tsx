import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getPathPlan } from "@/lib/api";

export const metadata: Metadata = {
  title: "职业路径规划 - CareerPilot",
  description: "查看主路径、备选路径和成长建议"
};

export default async function StudentPathPage() {
  const plan = await getPathPlan();

  const primaryPath = Array.isArray(plan?.primary_path) ? plan.primary_path : [];
  const alternatePaths = Array.isArray(plan?.alternate_paths) ? plan.alternate_paths : [];
  const rationale = plan?.rationale ?? "暂无数据";

  return (
    <AppShell title="职业路径规划" subtitle="结合岗位图谱、晋升路径与转岗路径，为学生生成主路径与备选路径。">
      <SectionCard title="主路径">
        <ul className="timeline">
          {primaryPath.map((step: string) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="备选路径">
        <ul className="plain-list">
          {alternatePaths.map((path: string[]) => (
            <li key={path.join("-")}>{path.join(" -> ")}</li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="路径依据">
        <p>{rationale}</p>
      </SectionCard>
    </AppShell>
  );
}


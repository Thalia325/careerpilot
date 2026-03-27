import { AppShell } from "@/components/AppShell";
import { SectionCard } from "@/components/SectionCard";
import { getPathPlan } from "@/lib/api";

export default async function StudentPathPage() {
  const plan = await getPathPlan();

  return (
    <AppShell title="职业路径规划" subtitle="结合岗位图谱、晋升路径与转岗路径，为学生生成主路径与备选路径。">
      <SectionCard title="主路径">
        <ul className="timeline">
          {plan.primary_path.map((step: string) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="备选路径">
        <ul className="plain-list">
          {plan.alternate_paths.map((path: string[]) => (
            <li key={path.join("-")}>{path.join(" -> ")}</li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="路径依据">
        <p>{plan.rationale}</p>
      </SectionCard>
    </AppShell>
  );
}


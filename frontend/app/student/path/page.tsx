"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { getStudentSession, getPathPlan } from "@/lib/api";

export default function StudentPathPage() {
  const [primaryPath, setPrimaryPath] = useState<string[]>([]);
  const [alternatePaths, setAlternatePaths] = useState<string[][]>([]);
  const [rationale, setRationale] = useState("暂无数据");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const sess = await getStudentSession();
        if (!sess.student_id || !sess.suggested_job_code) { setLoading(false); return; }
        const plan = await getPathPlan(sess.student_id, sess.suggested_job_code);
        setPrimaryPath(Array.isArray(plan?.primary_path) ? plan.primary_path : []);
        setAlternatePaths(Array.isArray(plan?.alternate_paths) ? plan.alternate_paths : []);
        setRationale(plan?.rationale ?? "暂无数据");
      } catch {} finally { setLoading(false); }
    })();
  }, []);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        {loading ? (
          <SectionCard title="加载中">
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          </SectionCard>
        ) : (
          <>
            <SectionCard title="岗位晋升路径">
              <ul className="timeline">
                {primaryPath.map((step: string) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </SectionCard>
            <SectionCard title="岗位转换方向">
              <ul className="plain-list">
                {alternatePaths.map((path: string[]) => (
                  <li key={path.join("-")}>{path.join(" → ")}</li>
                ))}
              </ul>
            </SectionCard>
            <SectionCard title="路径依据">
              <p>{rationale}</p>
            </SectionCard>
          </>
        )}
    </div>
  );
}

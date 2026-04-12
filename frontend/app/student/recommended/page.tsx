"use client";

import { useState, useEffect } from "react";
import { getRecommendedJobs, type RecommendedJob } from "@/lib/api";

export default function RecommendedJobsPage() {
  const [jobs, setJobs] = useState<RecommendedJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecommendedJobs()
      .then((res) => setJobs(res))
      .catch((e) => console.error("Failed to load recommended jobs:", e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 8px" }}>为你推荐的岗位</h1>
      <p style={{ fontSize: "0.875rem", color: "var(--subtle)", margin: "0 0 16px" }}>根据你的能力档案和方向偏好，系统为你推荐以下岗位</p>
      {loading ? (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>加载中...</div>
      ) : jobs.length > 0 ? (
        <div className="recommended-grid">
          {jobs.map((job) => (
            <div key={job.job_code} className="recommended-card">
              <p className="recommended-card__title">{job.title}</p>
              <p className="recommended-card__company">{job.company || "推荐岗位"}</p>
              {job.salary && <p className="recommended-card__salary">{job.salary}</p>}
              {job.match_score != null && (
                <p style={{ fontSize: "0.8125rem", color: "#0b7b72", fontWeight: 600, margin: "4px 0" }}>
                  匹配度 {job.match_score} 分
                </p>
              )}
              <div className="recommended-card__tags">
                {(job.tags || []).map((tag) => (
                  <span key={tag} className="recommended-card__tag">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 32, color: "var(--subtle)" }}>
          暂无推荐岗位，请先上传简历生成能力档案
        </div>
      )}
    </div>
  );
}

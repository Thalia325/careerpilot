"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getJobTemplates } from "@/lib/api";
import { Icon } from "@/components/Icon";
import type { JobDetail, JobCategory } from "@/lib/demo-data";

const categories: ("全部" | JobCategory)[] = [
  "全部", "产品/技术", "设计/创意", "运营/市场", "金融/商务", "人力/行政", "教育/咨询"
];

const categoryColors: Record<string, string> = {
  "产品/技术": "#e8f5e9",
  "设计/创意": "#fce4ec",
  "运营/市场": "#fff3e0",
  "金融/商务": "#e3f2fd",
  "人力/行政": "#f3e5f5",
  "教育/咨询": "#fff8e1",
};

const categoryTextColors: Record<string, string> = {
  "产品/技术": "#2e7d32",
  "设计/创意": "#c62828",
  "运营/市场": "#e65100",
  "金融/商务": "#1565c0",
  "人力/行政": "#6a1b9a",
  "教育/咨询": "#f57f17",
};

export default function StudentJobsPage() {
  const [jobs, setJobs] = useState<JobDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<"全部" | JobCategory>("全部");

  useEffect(() => {
    getJobTemplates()
      .then((data) => setJobs(Array.isArray(data) ? data : []))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredJobs = activeCategory === "全部"
    ? jobs
    : jobs.filter((j) => j.category === activeCategory);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <div style={{
          display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "20px"
        }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => { setActiveCategory(cat); setExpandedJob(null); }}
              style={{
                padding: "6px 16px",
                borderRadius: "20px",
                border: "1px solid",
                borderColor: activeCategory === cat ? "#1a73e8" : "#ddd",
                background: activeCategory === cat ? "#1a73e8" : "#fff",
                color: activeCategory === cat ? "#fff" : "#555",
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.2s",
                fontWeight: activeCategory === cat ? 600 : 400,
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        <p style={{ fontSize: "0.75rem", color: "#aaa", margin: "0 0 16px" }}>
          薪资数据仅供参考，以实际市场行情为准
        </p>

        <SectionCard title="岗位能力要求">
          {loading ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          ) : filteredJobs.length === 0 ? (
            <EmptyState
              icon={<Icon name="clipboard" size={32} />}
              title="暂无该分类下的岗位"
              description="请尝试切换其他分类查看。"
              actionLabel="查看全部"
              actionHref="/student/jobs"
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {filteredJobs.map((job) => {
                const isExpanded = expandedJob === job.title;
                return (
                  <div
                    key={job.title}
                    className="feature-item"
                    style={{ cursor: "pointer", userSelect: "none" }}
                    onClick={() => setExpandedJob(isExpanded ? null : job.title)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <strong style={{ fontSize: "0.9375rem" }}>{job.title}</strong>
                        <span style={{
                          fontSize: "0.6875rem",
                          padding: "2px 8px",
                          borderRadius: "10px",
                          background: categoryColors[job.category] || "#f5f5f5",
                          color: categoryTextColors[job.category] || "#666",
                        }}>
                          {job.category}
                        </span>
                      </div>
                      <span style={{ fontSize: "0.75rem", color: "#888" }}>
                        {isExpanded ? "收起 ▲" : "展开 ▼"}
                      </span>
                    </div>

                    {isExpanded && (
                      <div style={{ marginTop: "16px" }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", color: "#555", lineHeight: 1.6, margin: "0 0 6px" }}>
                            {job.description}
                          </p>
                          <p style={{ fontSize: "0.8125rem", color: "#1a73e8", fontWeight: 600, margin: 0 }}>
                            参考薪资：{job.salary_range}
                          </p>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>核心技能</p>
                          <div className="badge-list">
                            {job.skills.map((s) => (
                              <span key={s}>{s}</span>
                            ))}
                          </div>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>能力要求</p>
                          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "0.8125rem", color: "#555", lineHeight: 1.8 }}>
                            {job.abilities.map((a) => (
                              <li key={a}>{a}</li>
                            ))}
                          </ul>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>证书建议</p>
                          <div className="badge-list">
                            {job.certificates.map((c) => (
                              <span key={c}>{c}</span>
                            ))}
                          </div>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>常用工具</p>
                          <div className="badge-list">
                            {job.tools.map((t) => (
                              <span key={t}>{t}</span>
                            ))}
                          </div>
                        </div>

                        <div style={{ paddingTop: "14px" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>职业路径</p>
                          <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "4px" }}>
                            {job.career_path.map((step, idx) => (
                              <span key={step} style={{ display: "inline-flex", alignItems: "center", fontSize: "0.8125rem" }}>
                                <span style={{
                                  padding: "3px 10px",
                                  borderRadius: "4px",
                                  background: idx === 0 ? "#e8f5e9" : idx === job.career_path.length - 1 ? "#fff3e0" : "#f5f5f5",
                                  color: "#333",
                                  fontWeight: idx === 0 || idx === job.career_path.length - 1 ? 600 : 400,
                                }}>
                                  {step}
                                </span>
                                {idx < job.career_path.length - 1 && (
                                  <span style={{ color: "#bbb", margin: "0 2px" }}>→</span>
                                )}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </SectionCard>
    </div>
  );
}

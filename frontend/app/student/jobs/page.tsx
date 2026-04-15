"use client";

import { useMemo, useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getJobExplorationJobs, type JobExploreItem } from "@/lib/api";
import { Icon } from "@/components/Icon";

type ApiJobTemplate = Partial<JobExploreItem> & {
  job_code?: string;
  industry?: string;
  location?: string;
  company_name?: string;
  company_size?: string;
  ownership_type?: string;
  company_intro?: string;
  summary?: string;
  skill_requirements?: string[];
  certificate_requirements?: string[];
  capabilities?: Record<string, number>;
  dimension_weights?: Record<string, number>;
  weights?: Record<string, number>;
  explanations?: Record<string, string>;
};

const ALL_CATEGORIES = "全部";

const categoryPalette = [
  { background: "#e8f5e9", color: "#2e7d32" },
  { background: "#fce4ec", color: "#c62828" },
  { background: "#fff3e0", color: "#e65100" },
  { background: "#e3f2fd", color: "#1565c0" },
  { background: "#f3e5f5", color: "#6a1b9a" },
  { background: "#fff8e1", color: "#f57f17" },
  { background: "#e0f2f1", color: "#00695c" },
];

const capabilityLabels: Record<string, string> = {
  innovation: "创新能力",
  learning: "学习能力",
  resilience: "抗压能力",
  communication: "沟通能力",
  internship: "实践能力",
};

const weightLabels: Record<string, string> = {
  basic_requirements: "基础要求",
  professional_skills: "专业技能",
  professional_literacy: "职业素养",
  development_potential: "发展潜力",
};

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

function getCategoryStyle(category: string) {
  let hash = 0;
  for (const char of category) {
    hash = (hash + char.charCodeAt(0)) % categoryPalette.length;
  }
  return categoryPalette[hash];
}

function inferCategory(job: ApiJobTemplate): string {
  if (job.industry) return job.industry;
  const title = job.title ?? "";
  const skills = asStringArray(job.skills ?? job.skill_requirements).join(" ");

  if (/UI|UX|设计|Figma|视觉|交互/.test(`${title} ${skills}`)) return "设计/创意";
  if (/运营|市场|内容|增长|营销/.test(title)) return "运营/市场";
  if (/金融|商务|财务|投资|风控/.test(title)) return "金融/商务";
  if (/人力|行政|HR|招聘/.test(title)) return "人力/行政";
  if (/教育|培训|咨询|教师/.test(title)) return "教育/咨询";

  return "产品/技术";
}

function normalizeJob(job: ApiJobTemplate): JobExploreItem {
  const capabilities = job.capabilities ?? {};
  const weights = job.dimension_weights ?? job.weights ?? {};
  const explanations = job.explanations ?? {};
  const skills = asStringArray(job.skills ?? job.skill_requirements);
  const certificates = asStringArray(job.certificates ?? job.certificate_requirements);

  const abilityLines = Object.entries(capabilities).map(([key, value]) => {
    const label = capabilityLabels[key] ?? key;
    return `${label}：${value} 分`;
  });

  const explanationLines = Object.entries(explanations).map(([key, value]) => `${key}：${value}`);
  const weightLines = Object.entries(weights).map(([key, value]) => {
    const label = weightLabels[key] ?? key;
    return `${label}权重 ${Math.round(Number(value) * 100)}%`;
  });

  return {
    job_code: job.job_code,
    title: job.title ?? "未命名岗位",
    category: job.category ?? job.industry ?? inferCategory(job),
    industry: job.industry,
    location: job.location,
    company_name: job.company_name,
    company_size: job.company_size,
    ownership_type: job.ownership_type,
    company_intro: job.company_intro,
    description: job.description ?? job.summary ?? "暂无岗位说明。",
    salary_range: job.salary_range ?? "暂无参考薪资",
    skills,
    abilities: asStringArray(job.abilities).length > 0 ? asStringArray(job.abilities) : [...abilityLines, ...weightLines, ...explanationLines],
    certificates,
    tools: asStringArray(job.tools).length > 0 ? asStringArray(job.tools) : skills.slice(0, 6),
    career_path: asStringArray(job.career_path).length > 0 ? asStringArray(job.career_path) : [job.title ?? "目标岗位"],
  };
}

export default function StudentJobsPage() {
  const [jobs, setJobs] = useState<JobExploreItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState(ALL_CATEGORIES);

  useEffect(() => {
    getJobExplorationJobs()
      .then((data) => setJobs(Array.isArray(data) ? data.map((job) => normalizeJob(job as ApiJobTemplate)) : []))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  const categoryOptions = useMemo(
    () => [ALL_CATEGORIES, ...Array.from(new Set(jobs.map((job) => job.category).filter(Boolean)))],
    [jobs]
  );

  const filteredJobs = activeCategory === ALL_CATEGORIES
    ? jobs
    : jobs.filter((j) => j.category === activeCategory);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <div style={{
          display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "20px"
        }}>
          {categoryOptions.map((cat) => (
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
                const jobKey = job.job_code ?? job.title;
                const isExpanded = expandedJob === jobKey;
                const categoryStyle = getCategoryStyle(job.category);
                return (
                  <div
                    key={jobKey}
                    className="feature-item"
                    style={{ cursor: "pointer", userSelect: "none" }}
                    onClick={() => setExpandedJob(isExpanded ? null : jobKey)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                          <strong style={{ fontSize: "0.9375rem" }}>{job.title}</strong>
                          <span style={{
                            fontSize: "0.6875rem",
                            padding: "2px 8px",
                            borderRadius: "10px",
                            background: categoryStyle.background,
                            color: categoryStyle.color,
                          }}>
                            {job.category}
                          </span>
                          <span style={{ fontSize: "0.8125rem", color: "#1a73e8", fontWeight: 600 }}>
                            {job.salary_range}
                          </span>
                        </div>
                        <p style={{ fontSize: "0.75rem", color: "#888", margin: "6px 0 0" }}>
                          {[job.location, job.company_name, job.company_size, job.ownership_type].filter(Boolean).join(" · ") || "暂无公司信息"}
                        </p>
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
                          <p style={{ fontSize: "0.8125rem", color: "#666", lineHeight: 1.6, margin: "0 0 6px" }}>
                            {[job.location, job.company_name, job.industry, job.company_size, job.ownership_type].filter(Boolean).join(" · ") || "暂无公司信息"}
                          </p>
                          <p style={{ fontSize: "0.8125rem", color: "#1a73e8", fontWeight: 600, margin: 0 }}>
                            参考薪资：{job.salary_range}
                          </p>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>核心技能</p>
                          <div className="badge-list">
                            {job.skills.length > 0 ? (
                              job.skills.map((s) => <span key={s}>{s}</span>)
                            ) : (
                              <span>暂无技能标签</span>
                            )}
                          </div>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>能力要求</p>
                          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "0.8125rem", color: "#555", lineHeight: 1.8 }}>
                            {job.abilities.length > 0 ? (
                              job.abilities.map((a) => <li key={a}>{a}</li>)
                            ) : (
                              <li>暂无能力要求说明</li>
                            )}
                          </ul>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>证书建议</p>
                          <div className="badge-list">
                            {job.certificates.length > 0 ? (
                              job.certificates.map((c) => <span key={c}>{c}</span>)
                            ) : (
                              <span>暂无证书要求</span>
                            )}
                          </div>
                        </div>

                        <div style={{ paddingTop: "14px", paddingBottom: "14px", borderBottom: "1px solid #f0f0f0" }}>
                          <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px", color: "#333" }}>常用工具</p>
                          <div className="badge-list">
                            {job.tools.length > 0 ? (
                              job.tools.map((t) => <span key={t}>{t}</span>)
                            ) : (
                              <span>暂无工具说明</span>
                            )}
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

"use client";

import { useMemo, useState, useEffect, useLayoutEffect, useRef } from "react";
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
  { background: "#fce4ec", color: "#ad1457" },
  { background: "#e8eaf6", color: "#283593" },
  { background: "#f1f8e9", color: "#558b2f" },
  { background: "#fbe9e7", color: "#bf360c" },
  { background: "#e0f7fa", color: "#00838f" },
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

const exploreCategories = [
  "前端开发",
  "Java开发",
  "C/C++开发",
  "软件测试",
  "硬件测试",
  "实施工程师",
  "技术支持",
  "运维工程师",
  "产品经理",
  "项目管理",
  "算法工程师",
  "数据分析",
  "网络安全",
  "网络工程师",
  "硬件工程师",
  "售前工程师",
  "其他岗位",
];

const titleCategoryRules: Array<[string, RegExp]> = [
  ["前端开发", /前端|web前端|web 前端|react|vue|javascript|typescript/],
  ["Java开发", /java|spring/],
  ["C/C++开发", /c\/c\+\+|c\+\+|c语言|嵌入式软件/],
  ["软件测试", /软件测试|测试工程师|质量管理\/测试|质量保证|功能测试|自动化测试|qa/],
  ["硬件测试", /硬件测试|板卡测试|电子测试/],
  ["实施工程师", /实施工程师|实施顾问|erp实施|系统实施|软件实施|项目实施/],
  ["技术支持", /技术支持|售后工程师|客户支持|服务工程师/],
  ["运维工程师", /运维|devops|sre|系统运维/],
  ["产品经理", /产品经理|产品专员|产品助理|需求分析|业务分析/],
  ["项目管理", /项目经理|项目主管|项目专员|项目助理|项目管理|项目招投标|招投标专员/],
  ["算法工程师", /算法|机器学习|深度学习|计算机视觉|自然语言|nlp|cv/],
  ["数据分析", /数据分析|数据挖掘|bi|数据统计|数据运营/],
  ["网络安全", /网络安全|信息安全|安全工程师|渗透|安全运维/],
  ["网络工程师", /网络工程师|网络维护|传输网络|通信工程师/],
  ["硬件工程师", /硬件工程师|计算机硬件维护|硬件维护|嵌入式硬件/],
  ["售前工程师", /售前|解决方案工程师|方案工程师/],
];

const contextCategoryRules: Array<[string, RegExp]> = [
  ...titleCategoryRules,
];

function matchCategory(blob: string, rules: Array<[string, RegExp]>): string | null {
  const loweredBlob = blob.toLowerCase();
  return rules.find(([, pattern]) => pattern.test(loweredBlob))?.[0] ?? null;
}

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
  const explicitCategory = (job.category ?? "").trim();
  if (exploreCategories.includes(explicitCategory)) return explicitCategory;

  const title = job.title ?? "";
  const rawCategory = job.category ?? "";
  const industry = job.industry ?? "";
  return matchCategory(title, titleCategoryRules)
    ?? matchCategory(`${rawCategory} ${industry}`, contextCategoryRules)
    ?? "其他岗位";
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
    category: inferCategory(job),
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
  const [categoriesExpanded, setCategoriesExpanded] = useState(false);
  const [collapsedCategoryHeight, setCollapsedCategoryHeight] = useState<number | null>(null);
  const [searchText, setSearchText] = useState("");
  const categoryListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getJobExplorationJobs()
      .then((data) => setJobs(Array.isArray(data) ? data.map((job) => normalizeJob(job as ApiJobTemplate)) : []))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  const categoryOptions = useMemo(
    () => Array.from(new Set(jobs.map((job) => job.category).filter(Boolean))),
    [jobs]
  );

  const displayCategoryOptions = useMemo(
    () => activeCategory === ALL_CATEGORIES
      ? categoryOptions
      : [activeCategory, ...categoryOptions.filter((cat) => cat !== activeCategory)],
    [activeCategory, categoryOptions]
  );

  useLayoutEffect(() => {
    const calculateHeight = () => {
      const container = categoryListRef.current;
      if (!container) return;

      const buttons = Array.from(container.children).filter((child): child is HTMLElement => child instanceof HTMLElement);
      const rowTops: number[] = [];
      let twoRowBottom = 0;

      for (const button of buttons) {
        const top = button.offsetTop;
        let rowIndex = rowTops.findIndex((rowTop) => Math.abs(rowTop - top) < 2);
        if (rowIndex === -1) {
          rowTops.push(top);
          rowIndex = rowTops.length - 1;
        }
        if (rowIndex < 2) {
          twoRowBottom = Math.max(twoRowBottom, top + button.offsetHeight);
        }
      }

      setCollapsedCategoryHeight(twoRowBottom || null);
    };

    calculateHeight();
    window.addEventListener("resize", calculateHeight);
    return () => window.removeEventListener("resize", calculateHeight);
  }, [displayCategoryOptions]);

  const filteredJobs = jobs.filter((j) => {
    if (activeCategory !== ALL_CATEGORIES && j.category !== activeCategory) return false;
    if (searchText) {
      const q = searchText.toLowerCase();
      return (
        j.title.toLowerCase().includes(q) ||
        (j.job_code ?? "").toLowerCase().includes(q) ||
        (j.skills ?? []).some((s) => s.toLowerCase().includes(q)) ||
        (j.description ?? "").toLowerCase().includes(q) ||
        (j.company_name ?? "").toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <div style={{ marginBottom: "12px" }}>
          <div
            ref={categoryListRef}
            style={{
              display: "flex",
              gap: "8px",
              flexWrap: "wrap",
              maxHeight: categoriesExpanded ? "none" : collapsedCategoryHeight ?? 88,
              overflow: "hidden",
            }}
          >
            {displayCategoryOptions.map((cat) => (
              <button
                key={cat}
                onClick={() => {
                  setActiveCategory((current) => current === cat ? ALL_CATEGORIES : cat);
                  setExpandedJob(null);
                }}
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
          {categoryOptions.length > 18 && (
            <button
              type="button"
              onClick={() => setCategoriesExpanded((expanded) => !expanded)}
              aria-expanded={categoriesExpanded}
              style={{
                marginTop: 10,
                padding: "5px 14px",
                borderRadius: 8,
                border: "1px solid rgba(26, 115, 232, 0.24)",
                background: "#fff",
                color: "#1a73e8",
                fontSize: "0.8125rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {categoriesExpanded ? "收起" : `展开全部 ${categoryOptions.length}`}
            </button>
          )}
        </div>

        {/* 搜索栏 */}
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}>
          <div style={{ flex: 1, position: "relative" }}>
            <input
              type="text"
              placeholder="搜索岗位名称、技能、公司..."
              value={searchText}
              onChange={(e) => { setSearchText(e.target.value); setExpandedJob(null); }}
              style={{
                width: "100%",
                padding: "8px 12px 8px 34px",
                borderRadius: 8,
                border: "1px solid #e0e0e0",
                fontSize: "0.8125rem",
                outline: "none",
                background: "#fff",
                boxSizing: "border-box",
              }}
            />
            <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#bbb", pointerEvents: "none" }}>
              <Icon name="search" size={14} />
            </span>
          </div>
          {searchText && (
            <button
              onClick={() => setSearchText("")}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#999", fontSize: "0.8rem", whiteSpace: "nowrap" }}
            >
              清除
            </button>
          )}
          <span style={{ fontSize: "0.75rem", color: "#aaa", whiteSpace: "nowrap" }}>
            {filteredJobs.length} / {jobs.length}
          </span>
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
                      <div style={{ marginTop: "10px" }} onClick={(e) => e.stopPropagation()}>
                        {/* Row 1: description + skills */}
                        <div style={{ display: "flex", gap: 14, alignItems: "flex-start", flexWrap: "wrap" }}>
                          <div style={{ flex: "1 1 200px", minWidth: 0 }}>
                            <p style={{ fontSize: "0.8rem", color: "#555", lineHeight: 1.5, margin: "0 0 6px", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                              {job.description}
                            </p>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                              {job.skills.slice(0, 6).map((s) => (
                                <span key={s} style={{ padding: "1px 7px", borderRadius: 3, background: "#e3f2fd", color: "#1565c0", fontSize: "0.7rem" }}>{s}</span>
                              ))}
                              {job.skills.length > 6 && <span style={{ fontSize: "0.7rem", color: "#999" }}>+{job.skills.length - 6}</span>}
                            </div>
                          </div>
                          <div style={{ flex: "0 0 auto" }}>
                            {job.certificates.length > 0 && (
                              <div>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                                  {job.certificates.map((c) => (
                                    <span key={c} style={{ padding: "1px 7px", borderRadius: 3, background: "#f3e5f5", color: "#6a1b9a", fontSize: "0.7rem" }}>{c}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {job.career_path.length > 0 && (
                              <div style={{ marginTop: 4, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 2 }}>
                                {job.career_path.slice(0, 4).map((step, idx) => (
                                  <span key={step} style={{ display: "inline-flex", alignItems: "center", fontSize: "0.7rem" }}>
                                    <span style={{ padding: "1px 6px", borderRadius: 3, background: idx === 0 ? "#e8f5e9" : "#f5f5f5" }}>{step}</span>
                                    {idx < Math.min(job.career_path.length, 4) - 1 && <span style={{ color: "#ccc", margin: "0 1px" }}>→</span>}
                                  </span>
                                ))}
                                {job.career_path.length > 4 && <span style={{ fontSize: "0.65rem", color: "#999" }}>→ ...</span>}
                              </div>
                            )}
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

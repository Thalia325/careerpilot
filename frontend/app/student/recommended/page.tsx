"use client";

import { useEffect, useMemo, useState } from "react";
import { getRecommendedJobs, type RecommendedJob } from "@/lib/api";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { Icon } from "@/components/Icon";

type SortKey = "match" | "salary" | "skill";

type JobViewModel = RecommendedJob & {
  industryGroup: string;
  industryDisplay: string;
  locationCity: string;
  salaryValue: number;
  searchBlob: string;
};

const ALL_FILTER = "__ALL__";
const WORK_DAYS_PER_MONTH = 21.75;

const INDUSTRY_GROUP_RULES: Array<{ label: string; keywords: string[] }> = [
  { label: "软件/互联网", keywords: ["计算机软件", "互联网", "IT服务", "电子商务"] },
  { label: "AI/大数据", keywords: ["人工智能", "云计算", "大数据", "数据服务", "数据智能"] },
  { label: "硬件/半导体", keywords: ["半导体", "集成电路", "电子", "计算机硬件", "仪器仪表制造"] },
  { label: "通信/网络", keywords: ["通信", "网络设备", "网络/信息安全", "信息安全", "物联网"] },
  { label: "金融科技/数据", keywords: ["银行", "保险", "证券", "基金", "信托", "期货"] },
  { label: "医疗信息化", keywords: ["医疗设备", "器械", "医药制造", "卫生服务", "生物工程"] },
  { label: "制造业数字化", keywords: ["汽车研发", "制造", "工业自动化", "电气机械", "电力设备", "船舶", "航空", "航天", "火车制造"] },
  { label: "能源/电力数字化", keywords: ["电力", "水利", "热力", "燃气", "环保", "矿产", "采掘"] },
  { label: "教育/科研信息化", keywords: ["学术", "科研", "在线教育"] },
  { label: "企业服务/咨询", keywords: ["专业技术服务", "企业服务", "咨询服务", "人力资源服务"] },
];

function normalizeText(value?: string | null): string {
  return (value ?? "")
    .normalize("NFKC")
    .replace(/\s+/g, " ")
    .trim();
}

function splitIndustryTags(industry?: string | null): string[] {
  return normalizeText(industry)
    .split(/[\/／]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function primaryCity(location?: string | null): string {
  const text = normalizeText(location);
  return text.split(/[-－]/)[0]?.trim() || text;
}

function formatIndustry(industry?: string | null): string {
  const tags = splitIndustryTags(industry);
  return tags.length > 0 ? tags.slice(0, 3).join(" / ") : normalizeText(industry);
}

function deriveIndustryGroup(job: RecommendedJob): string {
  const explicit = normalizeText(job.industry_group);
  if (explicit) return explicit;

  const merged = splitIndustryTags(job.industry).join(" ");
  const matched = INDUSTRY_GROUP_RULES.find(({ keywords }) =>
    keywords.some((keyword) => merged.includes(keyword))
  );
  return matched?.label ?? "其他技术行业";
}

function parseSalaryMidpoint(salary?: string | null): number {
  const text = normalizeText(salary).toLowerCase();
  if (!text || text.includes("面议")) return 0;

  const nums = text.match(/\d+(?:\.\d+)?/g)?.map(Number) ?? [];
  if (nums.length === 0) return 0;

  let low = nums[0];
  let high = nums.length > 1 ? nums[1] : nums[0];

  if (text.includes("万")) {
    low *= 10000;
    high *= 10000;
  } else if (text.includes("k")) {
    low *= 1000;
    high *= 1000;
  }

  let monthlyMid = (low + high) / 2;

  if (text.includes("/天") || text.includes("元/天")) {
    monthlyMid *= WORK_DAYS_PER_MONTH;
  } else if (text.includes("/年") || text.includes("年薪")) {
    monthlyMid /= 12;
  }

  const monthsMatch = text.match(/(\d+)\s*薪/);
  if (monthsMatch) {
    const months = Number(monthsMatch[1]);
    if (months > 0) {
      monthlyMid = (monthlyMid * months) / 12;
    }
  }

  return monthlyMid;
}

function getMatchLevel(score: number | null): { text: string; color: string } {
  if (score == null) return { text: "待分析", color: "#888" };
  if (score >= 85) return { text: "高度匹配", color: "#2e7d32" };
  if (score >= 70) return { text: "值得冲刺", color: "#0d9488" };
  if (score >= 60) return { text: "可作为备选", color: "#0891b2" };
  return { text: "探索方向", color: "#6366f1" };
}

function buildJobView(job: RecommendedJob): JobViewModel {
  const industryGroup = deriveIndustryGroup(job);
  const industryDisplay = formatIndustry(job.industry);
  const locationCity = primaryCity(job.location);
  const salaryValue = parseSalaryMidpoint(job.salary);

  const searchBlob = [
    job.title,
    job.company,
    job.reason,
    industryGroup,
    industryDisplay,
    locationCity,
    ...(job.tags ?? []),
    ...(job.matched_tags ?? []),
    ...(job.missing_tags ?? []),
    ...(job.experience_tags ?? []),
  ]
    .map((item) => normalizeText(item))
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return {
    ...job,
    industryGroup,
    industryDisplay,
    locationCity,
    salaryValue,
    searchBlob,
  };
}

function resetStyles() {
  return {
    padding: "6px 14px",
    borderRadius: "8px",
    border: "1px solid #d2e3fc",
    background: "#fff",
    color: "#1a73e8",
    fontSize: "0.8125rem",
    cursor: "pointer",
    fontWeight: 600,
  } as const;
}

export default function RecommendedJobsPage() {
  const [jobs, setJobs] = useState<RecommendedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [sortKey, setSortKey] = useState<SortKey>("match");
  const [filterIndustry, setFilterIndustry] = useState<string>(ALL_FILTER);
  const [filterLocation, setFilterLocation] = useState<string>(ALL_FILTER);
  const [searchQuery, setSearchQuery] = useState("");

  const loadJobs = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getRecommendedJobs();
      setJobs(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载推荐岗位失败";
      setError(message);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
  }, []);

  const jobViews = useMemo(() => jobs.map(buildJobView), [jobs]);

  const industryOptions = useMemo(() => {
    const counts = new Map<string, number>();
    jobViews.forEach((job) => {
      counts.set(job.industryGroup, (counts.get(job.industryGroup) ?? 0) + 1);
    });
    return [
      { value: ALL_FILTER, label: "全部行业" },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "zh-CN"))
        .map(([group, count]) => ({ value: group, label: `${group} (${count})` })),
    ];
  }, [jobViews]);

  const locationOptions = useMemo(() => {
    const counts = new Map<string, number>();
    jobViews.forEach((job) => {
      if (job.locationCity) {
        counts.set(job.locationCity, (counts.get(job.locationCity) ?? 0) + 1);
      }
    });
    return [
      { value: ALL_FILTER, label: "全部城市" },
      ...Array.from(counts.entries())
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "zh-CN"))
        .map(([city, count]) => ({ value: city, label: `${city} (${count})` })),
    ];
  }, [jobViews]);

  const filteredJobs = useMemo(() => {
    let list = [...jobViews];

    if (filterIndustry !== ALL_FILTER) {
      list = list.filter((job) => job.industryGroup === filterIndustry);
    }
    if (filterLocation !== ALL_FILTER) {
      list = list.filter((job) => job.locationCity === filterLocation);
    }
    if (searchQuery) {
      const query = normalizeText(searchQuery).toLowerCase();
      list = list.filter((job) => job.searchBlob.includes(query));
    }

    if (sortKey === "salary") {
      return list.sort((a, b) => b.salaryValue - a.salaryValue || (b.match_score ?? 0) - (a.match_score ?? 0));
    }
    if (sortKey === "skill") {
      return list.sort((a, b) => (b.skill_score ?? 0) - (a.skill_score ?? 0) || (b.match_score ?? 0) - (a.match_score ?? 0));
    }
    return list.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0) || b.salaryValue - a.salaryValue);
  }, [filterIndustry, filterLocation, jobViews, searchQuery, sortKey]);

  const hasActiveFilters = filterIndustry !== ALL_FILTER || filterLocation !== ALL_FILTER || !!searchQuery.trim();
  const topScore = filteredJobs[0]?.match_score ?? null;
  const focusCount = filteredJobs.filter((job) => (job.match_score ?? 0) >= 60).length;
  const avgScore = filteredJobs.length
    ? Math.round(filteredJobs.reduce((sum, job) => sum + (job.match_score ?? 0), 0) / filteredJobs.length)
    : 0;

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
      <div style={{ marginBottom: "16px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 8px", color: "#333" }}>
          推荐岗位
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#666", margin: 0 }}>
          系统基于简历解析后的项目经历、实习经历和技能画像，为你筛选计算机相关岗位，并按匹配度展示重点候选与探索方向。
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <div style={{ background: "#fff", border: "1px solid #e8eaed", borderRadius: "8px", padding: "16px", textAlign: "center" }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>当前结果</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>{filteredJobs.length}</p>
          <p style={{ fontSize: "0.75rem", color: "#888", margin: "6px 0 0" }}>总推荐 {jobViews.length}</p>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8eaed", borderRadius: "8px", padding: "16px", textAlign: "center" }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>最高匹配度</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>
            {topScore == null ? "--" : `${topScore} 分`}
          </p>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8eaed", borderRadius: "8px", padding: "16px", textAlign: "center" }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>重点候选</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>{focusCount} 个</p>
        </div>
        <div style={{ background: "#fff", border: "1px solid #e8eaed", borderRadius: "8px", padding: "16px", textAlign: "center" }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>平均匹配</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>{avgScore || "--"}</p>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: "8px",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: "0.8125rem", color: "#666", fontWeight: 500 }}>排序</span>
        {[
          { key: "match" as const, label: "综合匹配" },
          { key: "skill" as const, label: "技能覆盖" },
          { key: "salary" as const, label: "薪资优先" },
        ].map((option) => (
          <button
            key={option.key}
            style={{
              padding: "6px 16px",
              borderRadius: "20px",
              border: "1px solid",
              borderColor: sortKey === option.key ? "#1a73e8" : "#ddd",
              background: sortKey === option.key ? "#1a73e8" : "#fff",
              color: sortKey === option.key ? "#fff" : "#555",
              fontSize: "0.8125rem",
              cursor: "pointer",
              fontWeight: sortKey === option.key ? 600 : 400,
            }}
            onClick={() => setSortKey(option.key)}
          >
            {option.label}
          </button>
        ))}

        <span style={{ fontSize: "0.8125rem", color: "#666", fontWeight: 500, marginLeft: "16px" }}>筛选</span>
        <select
          value={filterIndustry}
          onChange={(e) => setFilterIndustry(e.target.value)}
          style={{
            padding: "6px 12px",
            borderRadius: "6px",
            border: "1px solid #ddd",
            background: "#fff",
            color: "#555",
            fontSize: "0.8125rem",
            cursor: "pointer",
          }}
        >
          {industryOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          value={filterLocation}
          onChange={(e) => setFilterLocation(e.target.value)}
          style={{
            padding: "6px 12px",
            borderRadius: "6px",
            border: "1px solid #ddd",
            background: "#fff",
            color: "#555",
            fontSize: "0.8125rem",
            cursor: "pointer",
          }}
        >
          {locationOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="搜索岗位、公司、技能或行业..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            padding: "6px 12px",
            borderRadius: "6px",
            border: "1px solid #ddd",
            fontSize: "0.8125rem",
            color: "#333",
            outline: "none",
            marginLeft: "auto",
            minWidth: "220px",
          }}
        />

        {hasActiveFilters && (
          <button
            type="button"
            onClick={() => {
              setFilterIndustry(ALL_FILTER);
              setFilterLocation(ALL_FILTER);
              setSearchQuery("");
            }}
            style={resetStyles()}
          >
            清空筛选
          </button>
        )}
      </div>

      {hasActiveFilters && !loading && !error && (
        <p style={{ fontSize: "0.8125rem", color: "#666", margin: "0 0 12px" }}>
          当前显示 {filteredJobs.length} / {jobViews.length} 个岗位
        </p>
      )}

      <SectionCard title="推荐岗位列表">
        {loading ? (
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        ) : error ? (
          <div style={{ padding: "28px 20px", textAlign: "center" }}>
            <p style={{ margin: "0 0 12px", color: "#c62828", fontWeight: 600 }}>推荐岗位加载失败</p>
            <p style={{ margin: "0 0 16px", color: "#666", fontSize: "0.875rem" }}>{error}</p>
            <button type="button" onClick={() => void loadJobs()} style={resetStyles()}>
              重新加载
            </button>
          </div>
        ) : jobViews.length === 0 ? (
          <EmptyState
            icon={<Icon name="briefcase" size={32} />}
            title="暂无推荐岗位"
            description="当前还没有可用推荐结果。请先上传简历并完成分析，系统才会根据项目、实习和技能画像生成推荐。"
            actionLabel="返回学生首页"
            actionHref="/student"
          />
        ) : filteredJobs.length === 0 ? (
          <div style={{ padding: "28px 20px", textAlign: "center" }}>
            <p style={{ margin: "0 0 10px", color: "#333", fontWeight: 600 }}>当前筛选条件下没有匹配结果</p>
            <p style={{ margin: "0 0 16px", color: "#666", fontSize: "0.875rem" }}>
              你可以切换行业、城市，或者清空搜索词后再试。
            </p>
            <button
              type="button"
              onClick={() => {
                setFilterIndustry(ALL_FILTER);
                setFilterLocation(ALL_FILTER);
                setSearchQuery("");
              }}
              style={resetStyles()}
            >
              清空筛选
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {filteredJobs.map((job, index) => {
              const score = job.match_score ?? 0;
              const matched = job.matched_tags ?? [];
              const missing = job.missing_tags ?? [];
              const experienceTags = job.experience_tags ?? [];
              const levelInfo = getMatchLevel(job.match_score);

              return (
                <div
                  key={job.job_code}
                  className="feature-item"
                  style={{ cursor: "default", userSelect: "auto" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap", marginBottom: "6px" }}>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            color: "#1a73e8",
                            background: "#e8f0fe",
                            padding: "2px 8px",
                            borderRadius: "4px",
                          }}
                        >
                          #{index + 1}
                        </span>
                        <strong style={{ fontSize: "0.9375rem", color: "#333" }}>{job.title}</strong>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            background: "#f5f5f5",
                            color: levelInfo.color,
                          }}
                        >
                          {levelInfo.text}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.8125rem", color: "#888", margin: "0 0 6px" }}>
                        {[job.company || "推荐岗位", job.location, `${job.industryGroup} · ${job.industryDisplay}`].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                    <div style={{ textAlign: "right", minWidth: "80px" }}>
                      <p
                        style={{
                          fontSize: "1.5rem",
                          fontWeight: 700,
                          margin: 0,
                          color: job.match_score != null && job.match_score >= 60 ? "#1a73e8" : "#666",
                        }}
                      >
                        {job.match_score == null ? "--" : job.match_score}
                      </p>
                      <p style={{ fontSize: "0.75rem", color: "#888", margin: "2px 0 0" }}>匹配度</p>
                    </div>
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <div
                      style={{
                        height: "6px",
                        background: "#e8eaed",
                        borderRadius: "3px",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${Math.max(4, Math.min(100, score))}%`,
                          background: job.match_score != null && job.match_score >= 60 ? "#1a73e8" : "#9aa0a6",
                          borderRadius: "3px",
                          transition: "width 0.3s",
                        }}
                      />
                    </div>
                  </div>

                  <div
                    style={{
                      background: "#f8f9fa",
                      padding: "10px 12px",
                      borderRadius: "6px",
                      marginBottom: "12px",
                    }}
                  >
                    <p style={{ fontSize: "0.8125rem", color: "#555", margin: 0, lineHeight: 1.5 }}>
                      {job.reason || "系统根据简历中的项目、实习和技能证据给出推荐。"}
                    </p>
                  </div>

                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        background: "#e8f0fe",
                        color: "#1a73e8",
                        fontWeight: 500,
                      }}
                    >
                      {job.industryGroup}
                    </span>
                    {job.salary && (
                      <span
                        style={{
                          fontSize: "0.75rem",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          background: "#e8f5e9",
                          color: "#2e7d32",
                          fontWeight: 500,
                        }}
                      >
                        薪资 {job.salary}
                      </span>
                    )}
                    {job.company_size && (
                      <span
                        style={{
                          fontSize: "0.75rem",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          background: "#f5f5f5",
                          color: "#555",
                        }}
                      >
                        {job.company_size}
                      </span>
                    )}
                    {job.ownership_type && (
                      <span
                        style={{
                          fontSize: "0.75rem",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          background: "#f5f5f5",
                          color: "#555",
                        }}
                      >
                        {job.ownership_type}
                      </span>
                    )}
                  </div>

                  {experienceTags.length > 0 && (
                    <div style={{ marginBottom: "12px" }}>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        项目/实习命中
                        {job.experience_score != null && (
                          <span style={{ color: "#888", fontWeight: 400 }}> · {job.experience_score} 分</span>
                        )}
                      </p>
                      <div className="badge-list">
                        {experienceTags.map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: "0.8125rem",
                              padding: "4px 10px",
                              borderRadius: "4px",
                              background: "#e0f2fe",
                              color: "#075985",
                              fontWeight: 500,
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {matched.length > 0 && (
                    <div style={{ marginBottom: missing.length > 0 ? "12px" : "0" }}>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        已匹配技能
                      </p>
                      <div className="badge-list">
                        {matched.map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: "0.8125rem",
                              padding: "4px 10px",
                              borderRadius: "4px",
                              background: "#e8f5e9",
                              color: "#2e7d32",
                              fontWeight: 500,
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {missing.length > 0 && (
                    <div style={{ marginBottom: (job.tags || []).length > 0 ? "12px" : "0" }}>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        可补强技能
                      </p>
                      <div className="badge-list">
                        {missing.map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: "0.8125rem",
                              padding: "4px 10px",
                              borderRadius: "4px",
                              background: "#fff8e1",
                              color: "#8a4b00",
                              fontWeight: 500,
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {(job.tags || []).length > 0 && (
                    <div>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        岗位关键词
                      </p>
                      <div className="badge-list">
                        {(job.tags || []).slice(0, 8).map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: "0.8125rem",
                              padding: "4px 10px",
                              borderRadius: "4px",
                              background: "#e8f0fe",
                              color: "#1a73e8",
                              fontWeight: 500,
                            }}
                          >
                            {tag}
                          </span>
                        ))}
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

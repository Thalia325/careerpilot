"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getRecommendedJobs, type RecommendedJob } from "@/lib/api";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { Icon } from "@/components/Icon";

type SortKey = "match" | "salary" | "skill";

function parseSalaryMidpoint(salary: string): number {
  const nums = salary.match(/\d+(?:\.\d+)?/g)?.map(Number) ?? [];
  if (nums.length === 0) return 0;
  if (nums.length === 1) return nums[0];
  return (nums[0] + nums[1]) / 2;
}

function getMatchLevel(score: number | null): { text: string; color: string } {
  if (score == null) return { text: "待分析", color: "#888" };
  if (score >= 85) return { text: "高度匹配", color: "#2e7d32" };
  if (score >= 70) return { text: "值得冲刺", color: "#0d9488" };
  if (score >= 60) return { text: "可作为备选", color: "#0891b2" };
  return { text: "探索方向", color: "#6366f1" };
}

export default function RecommendedJobsPage() {
  const [jobs, setJobs] = useState<RecommendedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("match");
  const [filterIndustry, setFilterIndustry] = useState<string>("全部");
  const [filterLocation, setFilterLocation] = useState<string>("全部");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    getRecommendedJobs()
      .then((res) => setJobs(res))
      .catch((e) => console.error("Failed to load recommended jobs:", e))
      .finally(() => setLoading(false));
  }, []);

  const sortedJobs = useMemo(() => {
    let list = [...jobs];

    if (filterIndustry !== "全部") {
      list = list.filter((job) => job.industry === filterIndustry);
    }
    if (filterLocation !== "全部") {
      list = list.filter((job) => job.location === filterLocation);
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      list = list.filter((job) =>
        job.title.toLowerCase().includes(query) ||
        job.company?.toLowerCase().includes(query) ||
        job.tags?.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    if (sortKey === "salary") {
      return list.sort((a, b) => parseSalaryMidpoint(b.salary || "") - parseSalaryMidpoint(a.salary || ""));
    }
    if (sortKey === "skill") {
      return list.sort((a, b) => (b.skill_score ?? 0) - (a.skill_score ?? 0));
    }
    return list.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));
  }, [jobs, sortKey, filterIndustry, filterLocation, searchQuery]);

  const industries = useMemo(() => {
    const inds = new Set(jobs.map((j) => j.industry).filter(Boolean));
    return ["全部", ...Array.from(inds).sort()];
  }, [jobs]);

  const locations = useMemo(() => {
    const locs = new Set(jobs.map((j) => j.location).filter(Boolean));
    return ["全部", ...Array.from(locs).sort()];
  }, [jobs]);

  const topScore = sortedJobs[0]?.match_score ?? null;
  const focusCount = jobs.filter((job) => (job.match_score ?? 0) >= 60).length;
  const avgScore = jobs.length
    ? Math.round(jobs.reduce((sum, job) => sum + (job.match_score ?? 0), 0) / jobs.length)
    : 0;

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "16px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 8px", color: "#333" }}>
          推荐岗位
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#666", margin: 0 }}>
          系统基于 OCR 解析后的项目经历、实习经历和技能画像，按匹配度展示重点候选与探索方向
        </p>
      </div>

      {/* Summary Stats */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
        gap: "12px",
        marginBottom: "16px",
      }}>
        <div style={{
          background: "#fff",
          border: "1px solid #e8eaed",
          borderRadius: "8px",
          padding: "16px",
          textAlign: "center",
        }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>推荐岗位</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>{sortedJobs.length}</p>
        </div>
        <div style={{
          background: "#fff",
          border: "1px solid #e8eaed",
          borderRadius: "8px",
          padding: "16px",
          textAlign: "center",
        }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>最高匹配度</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>
            {topScore == null ? "--" : `${topScore} 分`}
          </p>
        </div>
        <div style={{
          background: "#fff",
          border: "1px solid #e8eaed",
          borderRadius: "8px",
          padding: "16px",
          textAlign: "center",
        }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>重点候选</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>{focusCount} 个</p>
        </div>
        <div style={{
          background: "#fff",
          border: "1px solid #e8eaed",
          borderRadius: "8px",
          padding: "16px",
          textAlign: "center",
        }}>
          <p style={{ fontSize: "0.75rem", color: "#666", margin: "0 0 8px" }}>平均匹配</p>
          <p style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#1a73e8" }}>
            {avgScore || "--"}
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <div style={{
        display: "flex",
        gap: "8px",
        alignItems: "center",
        marginBottom: "16px",
        flexWrap: "wrap",
      }}>
        <span style={{ fontSize: "0.8125rem", color: "#666", fontWeight: 500 }}>排序</span>
        <button
          style={{
            padding: "6px 16px",
            borderRadius: "20px",
            border: "1px solid",
            borderColor: sortKey === "match" ? "#1a73e8" : "#ddd",
            background: sortKey === "match" ? "#1a73e8" : "#fff",
            color: sortKey === "match" ? "#fff" : "#555",
            fontSize: "0.8125rem",
            cursor: "pointer",
            transition: "all 0.2s",
            fontWeight: sortKey === "match" ? 600 : 400,
          }}
          onClick={() => setSortKey("match")}
        >
          综合匹配
        </button>
        <button
          style={{
            padding: "6px 16px",
            borderRadius: "20px",
            border: "1px solid",
            borderColor: sortKey === "skill" ? "#1a73e8" : "#ddd",
            background: sortKey === "skill" ? "#1a73e8" : "#fff",
            color: sortKey === "skill" ? "#fff" : "#555",
            fontSize: "0.8125rem",
            cursor: "pointer",
            transition: "all 0.2s",
            fontWeight: sortKey === "skill" ? 600 : 400,
          }}
          onClick={() => setSortKey("skill")}
        >
          技能覆盖
        </button>
        <button
          style={{
            padding: "6px 16px",
            borderRadius: "20px",
            border: "1px solid",
            borderColor: sortKey === "salary" ? "#1a73e8" : "#ddd",
            background: sortKey === "salary" ? "#1a73e8" : "#fff",
            color: sortKey === "salary" ? "#fff" : "#555",
            fontSize: "0.8125rem",
            cursor: "pointer",
            transition: "all 0.2s",
            fontWeight: sortKey === "salary" ? 600 : 400,
          }}
          onClick={() => setSortKey("salary")}
        >
          薪资优先
        </button>

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
          {industries.map((ind) => (
            <option key={ind} value={ind}>{ind === "全部" ? "全部行业" : ind}</option>
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
          {locations.map((loc) => (
            <option key={loc} value={loc}>{loc === "全部" ? "全部城市" : loc}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="搜索岗位、公司或技能..."
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
          }}
        />
      </div>

      {/* Job Cards */}
      <SectionCard title="推荐岗位列表">
        {loading ? (
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        ) : sortedJobs.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {sortedJobs.map((job, index) => {
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
                        <span style={{
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          color: "#1a73e8",
                          background: "#e8f0fe",
                          padding: "2px 8px",
                          borderRadius: "4px",
                        }}>
                          #{index + 1}
                        </span>
                        <strong style={{ fontSize: "0.9375rem", color: "#333" }}>{job.title}</strong>
                        <span style={{
                          fontSize: "0.75rem",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "#f5f5f5",
                          color: levelInfo.color,
                        }}>
                          {levelInfo.text}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.8125rem", color: "#888", margin: "0 0 6px" }}>
                        {[job.company || "推荐岗位", job.location, job.industry].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                    <div style={{ textAlign: "right", minWidth: "80px" }}>
                      <p style={{
                        fontSize: "1.5rem",
                        fontWeight: 700,
                        margin: 0,
                        color: job.match_score != null && job.match_score >= 60 ? "#1a73e8" : "#666",
                      }}>
                        {job.match_score == null ? "--" : job.match_score}
                      </p>
                      <p style={{ fontSize: "0.75rem", color: "#888", margin: "2px 0 0" }}>匹配度</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div style={{ marginBottom: "12px" }}>
                    <div style={{
                      height: "6px",
                      background: "#e8eaed",
                      borderRadius: "3px",
                      overflow: "hidden",
                    }}>
                      <div style={{
                        height: "100%",
                        width: `${Math.max(4, Math.min(100, score))}%`,
                        background: job.match_score != null && job.match_score >= 60 ? "#1a73e8" : "#9aa0a6",
                        borderRadius: "3px",
                        transition: "width 0.3s",
                      }} />
                    </div>
                  </div>

                  {/* Reason */}
                  <div style={{
                    background: "#f8f9fa",
                    padding: "10px 12px",
                    borderRadius: "6px",
                    marginBottom: "12px",
                  }}>
                    <p style={{ fontSize: "0.8125rem", color: "#555", margin: 0, lineHeight: 1.5 }}>
                      {job.reason || "基于 OCR 项目/实习经历和能力画像推荐"}
                    </p>
                  </div>

                  {/* Meta Info */}
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                    {job.salary && (
                      <span style={{
                        fontSize: "0.75rem",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        background: "#e8f5e9",
                        color: "#2e7d32",
                        fontWeight: 500,
                      }}>
                        薪资 {job.salary}
                      </span>
                    )}
                    {job.company_size && (
                      <span style={{
                        fontSize: "0.75rem",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        background: "#f5f5f5",
                        color: "#555",
                      }}>
                        {job.company_size}
                      </span>
                    )}
                    {job.ownership_type && (
                      <span style={{
                        fontSize: "0.75rem",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        background: "#f5f5f5",
                        color: "#555",
                      }}>
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
                          <span key={tag} style={{
                            fontSize: "0.8125rem",
                            padding: "4px 10px",
                            borderRadius: "4px",
                            background: "#e0f2fe",
                            color: "#075985",
                            fontWeight: 500,
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Matched Skills */}
                  {matched.length > 0 && (
                    <div style={{ marginBottom: missing.length > 0 ? "12px" : "0" }}>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        已匹配技能
                      </p>
                      <div className="badge-list">
                        {matched.map((tag) => (
                          <span key={tag} style={{
                            fontSize: "0.8125rem",
                            padding: "4px 10px",
                            borderRadius: "4px",
                            background: "#e8f5e9",
                            color: "#2e7d32",
                            fontWeight: 500,
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {missing.length > 0 && (
                    <div style={{ marginBottom: (job.tags || []).length > 0 ? "12px" : "0" }}>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        + 可补强技能
                      </p>
                      <div className="badge-list">
                        {missing.map((tag) => (
                          <span key={tag} style={{
                            fontSize: "0.8125rem",
                            padding: "4px 10px",
                            borderRadius: "4px",
                            background: "#fff8e1",
                            color: "#8a4b00",
                            fontWeight: 500,
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tags */}
                  {(job.tags || []).length > 0 && (
                    <div>
                      <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#333", margin: "0 0 8px" }}>
                        岗位关键词
                      </p>
                      <div className="badge-list">
                        {(job.tags || []).slice(0, 8).map((tag) => (
                          <span key={tag} style={{
                            fontSize: "0.8125rem",
                            padding: "4px 10px",
                            borderRadius: "4px",
                            background: "#e8f0fe",
                            color: "#1a73e8",
                            fontWeight: 500,
                          }}>
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
        ) : (
          <EmptyState
            icon={<Icon name="briefcase" size={32} />}
            title="暂无推荐岗位"
            description="当前还没有可用岗位推荐。请先上传或重新分析简历，系统会基于 OCR 项目/实习经历重新匹配。"
            actionLabel="前往上传简历"
            actionHref="/student"
          />
        )}
      </SectionCard>
    </div>
  );
}

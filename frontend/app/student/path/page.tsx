"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { SectionCard } from "@/components/SectionCard";
import { getStudentSession, getPathPlan, getPathResult, type PathPlan } from "@/lib/api";

type VerticalNode = {
  title: string;
  description?: string;
  skills?: string[];
  level?: number;
  stage?: string;
};

type TransitionRole = {
  title: string;
  description?: string;
  skills?: string[];
  paths?: Array<{
    steps: string[];
    relation?: string;
    description?: string;
    skill_bridge?: string[];
  }>;
};

export default function StudentPathPage() {
  const searchParams = useSearchParams();
  const historyId = searchParams.get("history");
  const [plan, setPlan] = useState<PathPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [isHistoricalView, setIsHistoricalView] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Load specific path result from active run via path_id param
        const pathIdParam = searchParams.get("path_id");
        if (pathIdParam) {
          const pathId = parseInt(pathIdParam, 10);
          if (!Number.isNaN(pathId)) {
            setPlan(await getPathResult(pathId));
            setLoading(false);
            return;
          }
        }

        if (historyId && historyId.startsWith("path-")) {
          const pathId = parseInt(historyId.replace("path-", ""), 10);
          if (!Number.isNaN(pathId)) {
            setIsHistoricalView(true);
            setPlan(await getPathResult(pathId));
            setLoading(false);
            return;
          }
        }

        const sess = await getStudentSession();
        const jobCode = sess.resolved_job_code || sess.target_job_code || sess.suggested_job_code || "";
        if (!sess.student_id || !jobCode) {
          setLoading(false);
          return;
        }
        setPlan(await getPathPlan(sess.student_id, jobCode));
      } catch {
      } finally {
        setLoading(false);
      }
    })();
  }, [historyId, searchParams]);

  const verticalNodes = (plan?.vertical_graph?.nodes ?? []) as VerticalNode[];
  const transitionRoles = (plan?.transition_graph?.role_paths ?? []) as TransitionRole[];
  const currentAbility = (plan?.current_ability ?? {}) as Partial<PathPlan["current_ability"]>;
  const abilitySkills = currentAbility.skills ?? [];
  const matchedSkills = currentAbility.matched_skills ?? [];
  const missingSkills = currentAbility.missing_skills ?? [];
  const certificates = currentAbility.certificates ?? [];
  const projects = currentAbility.projects ?? [];
  const internships = currentAbility.internships ?? [];
  const hasEvidence = certificates.length > 0 || projects.length > 0 || internships.length > 0;
  const pathTheme = {
    primary: "#0f74da",
    primaryDark: "#0f4f9a",
    primarySoft: "#eef6ff",
    surface: "#f7fbff",
    border: "#cfe0f5",
    mutedBorder: "#dce8f6",
    rail: "#dce8f6",
  };

  return (
    <div style={{ maxWidth: 1120, margin: "0 auto", padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>职业路径规划</h1>
            {isHistoricalView ? (
              <span style={{ padding: "2px 10px", borderRadius: 6, background: "rgba(180,83,9,0.1)", color: "#b45309", fontSize: "0.75rem", fontWeight: 600 }}>历史数据</span>
            ) : plan ? (
              <span style={{ padding: "2px 10px", borderRadius: 6, background: "rgba(34,197,94,0.1)", color: "#166534", fontSize: "0.75rem", fontWeight: 600 }}>当前最新</span>
            ) : null}
          </div>
          <p style={{ margin: "6px 0 0", color: "var(--subtle)", fontSize: "0.875rem" }}>
            垂直晋升路径与相关岗位换岗路径图谱
          </p>
        </div>
        <Link href="/student" className="btn-secondary" style={{ textDecoration: "none", padding: "10px 14px", fontSize: "0.875rem" }}>
          返回问答页
        </Link>
      </div>

      {loading ? (
        <SectionCard title="加载中">
          <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
        </SectionCard>
      ) : !plan ? (
        <SectionCard title="暂无路径数据">
          <div style={{ textAlign: "center", padding: "40px 0", color: "#888" }}>
            <p style={{ margin: "0 0 8px", fontSize: "1rem" }}>请先完成画像生成和目标岗位确认</p>
            <p style={{ margin: 0, fontSize: "0.875rem" }}>路径规划需要基于画像和目标岗位生成</p>
          </div>
        </SectionCard>
      ) : (
        <>
          <SectionCard title="当前能力起点">
            <div className="path-ability-grid">
              <div className="path-ability-column">
                <h4 className="path-ability-heading">已掌握技能</h4>
                <div className="path-chip-list">
                  {abilitySkills.map((skill: string) => (
                    <span key={skill} className="path-chip path-chip--known">{skill}</span>
                  ))}
                </div>
                {abilitySkills.length === 0 && (
                  <span className="path-empty-text">暂无技能数据</span>
                )}
              </div>
              <div className="path-ability-column">
                <h4 className="path-ability-heading">技能差距</h4>
                <div className="path-chip-list">
                  {matchedSkills.map((skill: string) => (
                    <span key={skill} className="path-chip path-chip--matched">{skill}</span>
                  ))}
                  {missingSkills.map((skill: string) => (
                    <span key={skill} className="path-chip path-chip--missing">{skill}</span>
                  ))}
                </div>
                {matchedSkills.length === 0 && missingSkills.length === 0 && (
                  <span className="path-empty-text">暂无匹配数据</span>
                )}
              </div>
              <div className="path-ability-column path-ability-column--wide">
                <h4 className="path-ability-heading">证书 / 项目 / 实习</h4>
                <div className="path-evidence-list">
                  {certificates.length > 0 && (
                    <div className="path-evidence-row">
                      <span className="path-evidence-label">证书</span>
                      <p>{certificates.join("、")}</p>
                    </div>
                  )}
                  {projects.length > 0 && (
                    <div className="path-evidence-row">
                      <span className="path-evidence-label">项目</span>
                      <div className="path-evidence-items">
                        {projects.map((project: string) => (
                          <span key={project}>{project}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {internships.length > 0 && (
                    <div className="path-evidence-row">
                      <span className="path-evidence-label">实习</span>
                      <div className="path-evidence-items">
                        {internships.map((internship: string) => (
                          <span key={internship}>{internship}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {!hasEvidence && (
                    <span className="path-empty-text">暂无数据</span>
                  )}
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="垂直岗位图谱">
            <p className="path-map-intro">
              {plan?.vertical_graph?.description || plan?.rationale || "基于岗位图谱生成晋升链路。"}
            </p>
            {verticalNodes.length > 0 ? (
            <div className="path-timeline">
              {verticalNodes.map((node, index, arr) => {
                return (
                  <div key={`${node.title}-${index}`} className="path-timeline-row">
                    <div className="path-timeline-rail">
                      <div className="path-timeline-dot" />
                      {index < arr.length - 1 && (
                        <div className="path-timeline-line" />
                      )}
                    </div>
                    <div className="path-node-card">
                      <div className="path-node-card__top">
                        <span className="path-node-card__level">L{node.level ?? index + 1}</span>
                        {node.stage && (
                          <span className="path-node-card__stage">{node.stage}</span>
                        )}
                      </div>
                      <h3 className="path-node-card__title">{node.title}</h3>
                      <p className="path-node-card__desc">{node.description || "围绕岗位要求持续沉淀项目成果。"}</p>
                      {(node.skills ?? []).length > 0 && (
                      <div className="path-node-card__skills">
                        {(node.skills ?? []).slice(0, 4).map((skill) => (
                          <span key={skill} className="path-chip path-chip--known">{skill}</span>
                        ))}
                      </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            ) : (
              <div style={{ textAlign: "center", padding: "32px 0", color: "#888" }}>
                <p style={{ margin: 0 }}>暂无垂直岗位图谱数据</p>
              </div>
            )}
            {(plan?.vertical_graph?.promotion_paths ?? []).length > 1 && (
              <div className="path-promotion-paths">
                <h3>其他晋升链路</h3>
                <div className="path-promotion-paths__list">
                  {(plan?.vertical_graph?.promotion_paths ?? []).map((path: string[]) => (
                    <div key={path.join("-")} className="path-promotion-item">
                      {path.join(" → ")}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard title="换岗路径图谱">
            <p style={{ color: "var(--subtle)", margin: "0 0 20px", lineHeight: 1.7 }}>
              以 <strong style={{ color: "var(--ink)" }}>{plan?.transition_graph?.target || "当前岗位"}</strong> 为中心，已关联{" "}
              {transitionRoles.length || 0} 个相关岗位，每个岗位提供多条换岗路径及技能桥接点。
            </p>
            {transitionRoles.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {transitionRoles.map((role, roleIdx) => {
                  return (
                    <div
                      key={role.title}
                      style={{
                        display: "flex",
                        gap: 16,
                        alignItems: "flex-start",
                      }}
                    >
                      {/* Role node */}
                      <div
                        style={{
                          width: 140,
                          flexShrink: 0,
                          padding: "12px 14px",
                          borderRadius: 8,
                          border: `1px solid ${pathTheme.border}`,
                          background: pathTheme.surface,
                          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                          textAlign: "center",
                        }}
                      >
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: "50%",
                            background: pathTheme.primarySoft,
                            color: pathTheme.primaryDark,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            margin: "0 auto 8px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                          }}
                        >
                          {roleIdx + 1}
                        </div>
                        <h3 style={{ margin: "0 0 4px", fontSize: "0.875rem", fontWeight: 700 }}>{role.title}</h3>
                        <p style={{ margin: 0, color: "var(--subtle)", fontSize: "0.75rem", lineHeight: 1.4 }}>{role.description}</p>
                        {(role.skills?.length ?? 0) > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, justifyContent: "center", marginTop: 8 }}>
                            {(role.skills ?? []).slice(0, 3).map((skill) => (
                              <span
                                key={skill}
                                style={{
                                  padding: "2px 6px",
                                  borderRadius: 6,
                                  background: pathTheme.primarySoft,
                                  color: pathTheme.primaryDark,
                                  fontSize: "0.6875rem",
                                  fontWeight: 600,
                                }}
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Connector + paths */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                          <div style={{ width: 24, height: 2, background: pathTheme.rail }} />
                          <span style={{ fontSize: "0.75rem", color: "var(--subtle)", fontWeight: 600 }}>
                            {role.paths?.length || 0} 条换岗路径
                          </span>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          {(role.paths ?? []).slice(0, 3).map((path, pathIdx) => (
                            <div
                              key={path.steps.join("-")}
                              style={{
                                padding: 14,
                                borderRadius: 8,
                                background: pathTheme.surface,
                                border: `1px solid ${pathTheme.border}`,
                              }}
                            >
                              {/* Step flow */}
                              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8, flexWrap: "wrap" }}>
                                {path.steps.map((step, stepIdx) => (
                                  <span key={step} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <span
                                      style={{
                                        padding: "3px 10px",
                                        borderRadius: 6,
                                        background: "#fff",
                                        color: "var(--ink)",
                                        fontSize: "0.8125rem",
                                        fontWeight: 600,
                                        border: `1px solid ${pathTheme.mutedBorder}`,
                                      }}
                                    >
                                      {step}
                                    </span>
                                    {stepIdx < path.steps.length - 1 && (
                                      <span style={{ color: "#94a3b8", fontSize: "0.75rem" }}>→</span>
                                    )}
                                  </span>
                                ))}
                              </div>

                              {/* Description */}
                              <p style={{ margin: "0 0 8px", color: "var(--subtle)", fontSize: "0.8125rem", lineHeight: 1.6 }}>
                                {path.description || `${path.steps[0]} 可通过补齐 ${path.steps[path.steps.length - 1]} 的核心技能完成转换。`}
                              </p>

                              {/* Skill bridge */}
                              {(path.skill_bridge ?? []).length > 0 && (
                                <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                                  <span style={{ fontSize: "0.75rem", color: pathTheme.primaryDark, fontWeight: 600 }}>技能桥接：</span>
                                  {(path.skill_bridge ?? []).map((skill) => (
                                    <span
                                      key={skill}
                                      style={{
                                        padding: "3px 8px",
                                        borderRadius: 6,
                                        background: pathTheme.primarySoft,
                                        color: pathTheme.primaryDark,
                                        fontSize: "0.75rem",
                                        fontWeight: 600,
                                      }}
                                    >
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "32px 0", color: "#888" }}>
                <p style={{ margin: 0 }}>暂无换岗路径数据</p>
              </div>
            )}
          </SectionCard>

          {(plan?.recommendations ?? []).length > 0 && (
          <SectionCard title="成长建议与行动计划">
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {(plan?.recommendations ?? []).map((rec: { phase?: string; focus?: string; items?: string[] }, idx: number) => (
                <div key={idx} style={{ padding: 16, borderRadius: 8, background: pathTheme.surface, border: `1px solid ${pathTheme.border}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <span style={{
                      padding: "3px 10px",
                      borderRadius: 6,
                      background: pathTheme.primary,
                      color: "#fff",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                    }}>{rec.phase || "计划"}</span>
                    <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--ink)" }}>{rec.focus}</span>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(rec.items ?? []).map((item) => (
                      <span key={item} style={{
                        padding: "4px 10px",
                        borderRadius: 8,
                        background: "#fff",
                        color: "var(--ink)",
                        fontSize: "0.8125rem",
                        fontWeight: 500,
                        border: "1px solid #e2e8f0",
                      }}>{item}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
          )}

          <SectionCard title="路径依据">
            <p style={{ lineHeight: 1.8 }}>{plan?.rationale || "基于岗位图谱的晋升链路和转岗链路，结合学生当前技能覆盖情况生成主路径与备选路径。"}</p>
          </SectionCard>
        </>
      )}
    </div>
  );
}

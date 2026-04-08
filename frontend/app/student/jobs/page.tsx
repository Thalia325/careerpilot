"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { EmptyState } from "@/components/EmptyState";
import { getJobTemplates } from "@/lib/api";
import { StudentShellClient } from "@/components/StudentShellClient";

const jobDetails: Record<string, string[]> = {
  "产品经理": ["需求分析", "原型设计", "数据驱动", "项目管理", "用户调研", "沟通协调"],
  "UI/UX 设计师": ["Figma/Sketch", "视觉设计", "交互设计", "用户研究", "设计系统", "动效设计"],
  "运营专员": ["内容运营", "活动策划", "数据分析", "用户增长", "社区运营", "新媒体运营"],
  "市场营销专员": ["品牌策划", "市场调研", "文案撰写", "数字营销", "渠道推广", "活动执行"],
  "数据分析师": ["SQL", "Python/R", "数据可视化", "统计分析", "Excel", "商业洞察"],
  "人力资源专员": ["招聘管理", "培训发展", "绩效管理", "薪酬福利", "员工关系", "劳动法规"],
  "项目经理": ["PMP/敏捷管理", "跨部门协调", "风险管理", "进度控制", "需求管理", "沟通汇报"],
  "金融分析师": ["财务建模", "行业研究", "估值分析", "Excel建模", "报告撰写", "数据收集"],
  "教育培训师": ["课程设计", "教学表达", "学习理论", "教育技术", "评估设计", "学员管理"],
  "内容策划": ["创意写作", "用户洞察", "选题策划", "内容运营", "数据分析", "多平台运营"],
};

export default function StudentJobsPage() {
  const [templates, setTemplates] = useState<Array<{ title: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  useEffect(() => {
    getJobTemplates()
      .then((data) => setTemplates(Array.isArray(data) ? data : []))
      .catch(() => setTemplates([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <StudentShellClient title="岗位探索">
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <SectionCard title="岗位能力要求">
          {loading ? (
            <p style={{ textAlign: "center", padding: "40px", color: "#888" }}>加载中...</p>
          ) : templates.length === 0 ? (
            <EmptyState
              icon="📋"
              title="还没有岗位能力要求数据"
              description="系统内置的岗位能力要求模板将在这里显示。你可以浏览各类岗位要求，帮助更好地了解职业方向。"
              actionLabel="前往管理后台"
              actionHref="/admin"
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {templates.map((item: { title: string }) => {
                const isExpanded = expandedJob === item.title;
                const skills = jobDetails[item.title] || ["暂无详细数据"];
                return (
                  <div
                    key={item.title}
                    className="feature-item"
                    style={{ cursor: "pointer", userSelect: "none" }}
                    onClick={() => setExpandedJob(isExpanded ? null : item.title)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "0.9375rem" }}>{item.title}</strong>
                      <span style={{ fontSize: "0.75rem", color: "#888" }}>{isExpanded ? "收起 ▲" : "展开 ▼"}</span>
                    </div>
                    <p style={{ fontSize: "0.8125rem", margin: "4px 0 0" }}>查看技能要求、能力说明、证书要求与图谱路径</p>
                    {isExpanded && (
                      <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #eee" }}>
                        <p style={{ fontSize: "0.8125rem", fontWeight: 600, marginBottom: "8px" }}>核心技能要求：</p>
                        <div className="badge-list">
                          {skills.map((skill) => (
                            <span key={skill}>{skill}</span>
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
    </StudentShellClient>
  );
}

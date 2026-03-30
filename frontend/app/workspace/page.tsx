"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useRef } from "react";

const stages = [
  {
    title: "材料上传",
    description: "上传简历、证书等材料供系统分析。",
    icon: "📄",
    link: "/student/upload"
  },
  {
    title: "能力分析",
    description: "系统智能识别你的技能、证书和经历。",
    icon: "⭐",
    link: "/student/profile"
  },
  {
    title: "岗位匹配",
    description: "与目标岗位进行四维评分和匹配分析。",
    icon: "🎯",
    link: "/student/matching"
  },
  {
    title: "职业路径",
    description: "获得个性化的职业发展建议和行动计划。",
    icon: "🗺️",
    link: "/student/path"
  },
  {
    title: "报告导出",
    description: "编辑、优化并导出专业的职业规划报告。",
    icon: "📋",
    link: "/student/reports"
  }
];

export default function WorkspacePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isDirty, setIsDirty] = useState(false);
  const [query, setQuery] = useState(searchParams.get("query") || "前端开发工程师");
  const [resume, setResume] = useState(searchParams.get("resume") || "未上传简历");
  const pendingNavigationRef = useRef<string | null>(null);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  const handleNavigationStart = (href: string) => {
    if (isDirty) {
      const confirmed = confirm("你有未保存的内容，确定要离开吗？");
      if (!confirmed) {
        return;
      }
    }
    router.push(href);
  };

  const handleQueryChange = (newQuery: string) => {
    setQuery(newQuery);
    setIsDirty(true);
  };

  const handleResumeChange = (newResume: string) => {
    setResume(newResume);
    setIsDirty(true);
  };

  return (
    <div className="workspace-page">
      <div className="workspace-page__container">
        <header className="workspace-hero">
          <span className="section-kicker">任务工作台</span>
          <h1>职业规划分析进行中</h1>
          <p>按照以下步骤完成职业能力分析和规划报告生成。</p>
        </header>

        <section className="workspace-grid">
          <article className="workspace-card">
            <h2>当前任务</h2>
            <ul className="workspace-summary">
              <li>
                <span>目标岗位</span>
                <strong>{query}</strong>
              </li>
              <li>
                <span>简历文件</span>
                <strong>{resume}</strong>
              </li>
              <li>
                <span>当前状态</span>
                <strong style={{ color: "var(--accent)" }}>准备开始</strong>
              </li>
            </ul>
            <div style={{ marginTop: "20px" }}>
              <p style={{ margin: "0 0 12px", fontSize: "0.9rem", color: "var(--subtle)" }}>
                💡 提示：按照下方步骤指引，逐步完成职业规划分析。
              </p>
            </div>
          </article>

          <article className="workspace-card">
            <h2>分析步骤</h2>
            <div className="workspace-stage-list">
              {stages.map((stage, index) => (
                <a
                  key={stage.title}
                  href={stage.link}
                  className="workspace-stage-item workspace-stage-link"
                  title={`前往${stage.title}`}
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigationStart(stage.link);
                  }}
                >
                  <span title={stage.icon}>{stage.icon}</span>
                  <div>
                    <strong>{stage.title}</strong>
                    <p>{stage.description}</p>
                  </div>
                </a>
              ))}
            </div>
          </article>
        </section>

        <section className="workspace-actions">
          <a
            href="/student/upload"
            className="app-header__button"
            onClick={(e) => {
              e.preventDefault();
              handleNavigationStart("/student/upload");
            }}
          >
            开始上传材料
          </a>
          <a
            href="/results/report-sample"
            className="app-header__button app-header__button--ghost"
            onClick={(e) => {
              e.preventDefault();
              handleNavigationStart("/results/report-sample");
            }}
          >
            查看示例结果
          </a>
          <a
            href="/"
            className="workspace-backlink"
            onClick={(e) => {
              e.preventDefault();
              handleNavigationStart("/");
            }}
          >
            返回首页
          </a>
        </section>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { SidebarDrawer } from "@/components/SidebarDrawer";
import { PipelineProgress, type PipelineStep, type PipelineStepStatus } from "@/components/PipelineProgress";
import { Icon } from "@/components/Icon";
import {
  getStudentSession,
  getStudentProfile,
  getMatching,
  generateReport,
  listFiles,
  type StudentSession,
  type UploadedFileInfo,
} from "@/lib/api";

const studentNavItems = [
  { href: "/student", label: "首页", icon: <Icon name="home" size={18} /> },
  { href: "/student/jobs", label: "岗位探索", icon: <Icon name="search" size={18} /> },
  { href: "/student/profile", label: "我的能力分析", icon: <Icon name="chart" size={18} /> },
  { href: "/student/dashboard", label: "个人概览", icon: <Icon name="user" size={18} /> },
  { href: "/student/recommended", label: "推荐岗位", icon: <Icon name="briefcase" size={18} /> },
  { href: "/student/history", label: "历史记录", icon: <Icon name="clock" size={18} /> },
];

type StageStatus = "pending" | "done" | "running";

const stageConfig = [
  { key: "upload", title: "材料上传", description: "上传简历、证书等材料供系统分析。", link: "/student/upload" },
  { key: "profile", title: "能力分析", description: "系统智能识别你的技能、证书和经历。", link: "/student/profile" },
  { key: "matching", title: "岗位匹配", description: "与目标岗位进行四维评分和匹配分析。", link: "/student/matching" },
  { key: "path", title: "职业路径", description: "获得个性化的职业发展建议和行动计划。", link: "/student/path" },
];

export default function WorkspacePage() {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [session, setSession] = useState<StudentSession | null>(null);
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [hasProfile, setHasProfile] = useState(false);
  const [hasMatching, setHasMatching] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadStatus = useCallback(async () => {
    try {
      const sess = await getStudentSession();
      setSession(sess);
      const fileList = await listFiles();
      setFiles(fileList);

      if (sess.student_id && sess.suggested_job_code) {
        try {
          const profile = await getStudentProfile(sess.student_id);
          if (profile && (profile as Record<string, unknown>).skills) {
            setHasProfile(true);
          }
        } catch {}
        try {
          await getMatching(sess.student_id, sess.suggested_job_code);
          setHasMatching(true);
        } catch {}
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const getStageStatus = (key: string): StageStatus => {
    if (key === "upload") return files.length > 0 ? "done" : "pending";
    if (key === "profile") return hasProfile ? "done" : files.length > 0 ? "running" : "pending";
    if (key === "matching") return hasMatching ? "done" : hasProfile ? "running" : "pending";
    if (key === "path") return hasMatching ? "done" : "pending";
    return "pending";
  };

  const pipelineSteps: PipelineStep[] = stageConfig.map((s) => ({
    key: s.key,
    label: s.title,
    status: getStageStatus(s.key) === "done" ? "done" : getStageStatus(s.key) === "running" ? "running" : "pending",
  }));

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "user_role=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
  };

  const handleNavigationStart = (href: string) => {
    router.push(href);
  };

  return (
    <div className="workspace-bg">
      <SidebarDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        navItems={studentNavItems}
        label="学生功能"
        footer={
          <button
            className="sidebar-drawer__link"
            onClick={handleLogout}
            style={{ background: "none", border: "none", cursor: "pointer", width: "100%", color: "var(--color-error)" }}
          >
            <span className="sidebar-drawer__link-icon"><Icon name="logout" size={18} /></span>
            退出登录
          </button>
        }
      />
      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单"><Icon name="menu" size={20} /></button>
          <span className="workspace-topbar__title">任务工作台</span>
        </div>
        <div className="workspace-topbar__right">
          <span className="workspace-topbar__user">{session?.career_goal ? `${session.career_goal}方向` : "同学"}</span>
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>

      <div className="workspace-page">
        <div className="workspace-page__container">
          <header className="workspace-hero">
            <span className="section-kicker">任务工作台</span>
            <h1>职业规划分析</h1>
            <p>按照以下步骤完成职业能力分析和规划报告生成。</p>
          </header>

          {loading ? (
            <p style={{ textAlign: "center", padding: 40, color: "#888" }}>加载中...</p>
          ) : (
            <>
              <PipelineProgress steps={pipelineSteps} />

              <section className="workspace-grid">
                <article className="workspace-card">
                  <h2>当前状态</h2>
                  <ul className="workspace-summary">
                    <li><span>目标岗位</span><strong>{session?.suggested_job_title || session?.career_goal || "未设置"}</strong></li>
                    <li><span>已上传文件</span><strong>{files.length} 个</strong></li>
                    <li>
                      <span>能力画像</span>
                      <strong style={{ color: hasProfile ? "var(--accent)" : "#888" }}>
                        {hasProfile ? "已生成" : "未生成"}
                      </strong>
                    </li>
                    <li>
                      <span>匹配分析</span>
                      <strong style={{ color: hasMatching ? "var(--accent)" : "#888" }}>
                        {hasMatching ? "已完成" : "未完成"}
                      </strong>
                    </li>
                  </ul>
                </article>
                <article className="workspace-card">
                  <h2>分析步骤</h2>
                  <div className="workspace-stage-list">
                    {stageConfig.map((stage) => {
                      const status = getStageStatus(stage.key);
                      return (
                        <a
                          key={stage.key}
                          href={stage.link}
                          className="workspace-stage-item workspace-stage-link"
                          onClick={(e) => { e.preventDefault(); handleNavigationStart(stage.link); }}
                        >
                          <span>{status === "done" ? <Icon name="chart" size={16} color="#22c55e" /> : status === "running" ? <Icon name="loading" size={16} spin /> : <Icon name="clock" size={16} color="#ccc" />}</span>
                          <div>
                            <strong>{stage.title}</strong>
                            <p>{stage.description}</p>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </article>
              </section>
            </>
          )}

          <section className="workspace-actions">
            <Link href="/student" className="btn-primary" style={{ textDecoration: "none", display: "inline-flex" }}>
              {files.length === 0 ? "开始上传材料" : "前往分析主页"}
            </Link>
            <Link href="/student" className="workspace-backlink">返回首页</Link>
          </section>
        </div>
      </div>
    </div>
  );
}

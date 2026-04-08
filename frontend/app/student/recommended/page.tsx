"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarDrawer } from "@/components/SidebarDrawer";

const studentNavItems = [
  { href: "/student", label: "首页", icon: "🏠" },
  { href: "/student/jobs", label: "岗位探索", icon: "🔍" },
  { href: "/student/profile", label: "我的能力分析", icon: "📊" },
  { href: "/student/reports", label: "制定我的职业规划", icon: "📋", subtitle: "含岗位匹配 + 发展路径 + 行动计划" },
  { href: "/student/history", label: "历史记录", icon: "🕐" },
  { href: "/student/recommended", label: "推荐岗位", icon: "💼" },
  { href: "/student/dashboard", label: "个人概览", icon: "👤" }
];

const recommendedJobs = [
  { id: "1", title: "产品经理", company: "某互联网科技有限公司", salary: "15K-25K", tags: ["需求分析", "原型设计", "数据驱动"] },
  { id: "2", title: "运营专员", company: "某新媒体文化传媒公司", salary: "8K-14K", tags: ["内容运营", "活动策划", "数据分析"] },
  { id: "3", title: "UI设计师", company: "某设计咨询公司", salary: "12K-20K", tags: ["Figma", "视觉设计", "交互设计"] },
  { id: "4", title: "数据分析师", company: "某金融科技公司", salary: "14K-22K", tags: ["SQL", "Python", "数据可视化"] },
  { id: "5", title: "市场营销专员", company: "某消费品集团", salary: "10K-18K", tags: ["品牌策划", "市场调研", "文案撰写"] },
  { id: "6", title: "人力资源专员", company: "某大型企业集团", salary: "8K-15K", tags: ["招聘", "培训", "绩效管理"] },
  { id: "7", title: "项目经理", company: "某信息技术公司", salary: "18K-30K", tags: ["PMP", "敏捷管理", "跨部门协调"] },
  { id: "8", title: "内容策划", company: "某内容平台公司", salary: "10K-16K", tags: ["创意写作", "用户洞察", "选题策划"] },
  { id: "9", title: "金融分析师", company: "某证券投资公司", salary: "20K-35K", tags: ["财务建模", "行业研究", "估值分析"] },
  { id: "10", title: "教育培训师", company: "某教育科技公司", salary: "10K-18K", tags: ["课程设计", "教学表达", "学习理论"] }
];

export default function RecommendedJobsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_role");
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/login");
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
            <span className="sidebar-drawer__link-icon">🚪</span>
            退出登录
          </button>
        }
      />
      <div className="workspace-topbar">
        <div className="workspace-topbar__left">
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="打开菜单">☰</button>
          <span className="workspace-topbar__title">推荐岗位</span>
        </div>
        <div className="workspace-topbar__right">
          <button className="workspace-topbar__logout" onClick={handleLogout}>退出</button>
        </div>
      </div>
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 8px" }}>为你推荐的岗位</h1>
        <p style={{ fontSize: "0.875rem", color: "var(--subtle)", margin: "0 0 16px" }}>根据你的能力档案和方向偏好，系统为你推荐以下岗位</p>
        <div className="recommended-grid">
          {recommendedJobs.map((job) => (
            <div key={job.id} className="recommended-card">
              <p className="recommended-card__title">{job.title}</p>
              <p className="recommended-card__company">{job.company}</p>
              <p className="recommended-card__salary">{job.salary}</p>
              <div className="recommended-card__tags">
                {job.tags.map((tag) => (
                  <span key={tag} className="recommended-card__tag">{tag}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

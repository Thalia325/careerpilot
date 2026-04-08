"use client";

import Link from "next/link";
import { useState } from "react";
import { samplePreviews, sampleResultMap, workflowSteps } from "@/lib/home-data";

export default function HomePage() {
  const [selectedSample, setSelectedSample] = useState<string | null>(null);

  const sampleData = selectedSample ? sampleResultMap[selectedSample] : null;

  return (
    <div className="landing-bg">
      <header className="landing-header">
        <div className="landing-header__left">
          <Link href="/" className="landing-header__brand">
            <span className="landing-header__logo">CP</span>
            <span>
              <strong>职航智策</strong>
              <small>AI 职业规划助手</small>
            </span>
          </Link>
        </div>
        <div className="landing-header__right">
          <Link href="/login" className="landing-header__login-btn">
            登录 / 注册
          </Link>
        </div>
      </header>

      <section className="landing-hero-section">
        <span className="landing-hero-section__badge">AI 职业规划助手</span>
        <h1>三步开始一轮职业规划</h1>
        <p className="landing-hero-section__subtitle">
          上传简历或录入信息，系统帮你分析岗位匹配度，生成完整的职业发展报告。
        </p>
        <div className="landing-steps">
          {workflowSteps.map((step, i) => (
            <div key={step.step} className="landing-step-card">
              <div className="landing-step-card__number">{i + 1}</div>
              <p className="landing-step-card__title">{step.title}</p>
              <p className="landing-step-card__desc">{step.description}</p>
              {i < workflowSteps.length - 1 && (
                <span className="landing-step-card__arrow" aria-hidden="true">→</span>
              )}
            </div>
          ))}
        </div>
        <div style={{ textAlign: "center", marginTop: 12 }}>
          <Link
            href="/login"
            className="btn-primary"
            style={{
              textDecoration: "none",
              display: "inline-flex",
              fontSize: "1rem",
              padding: "14px 32px",
              borderRadius: 12
            }}
          >
            立即开始，免费使用
          </Link>
        </div>
      </section>

      <section className="landing-samples">
        <div className="landing-samples__heading">
          <h2>看看真实分析结果</h2>
          <p>以下是系统为不同方向同学生成的分析示例，点击卡片可查看详情</p>
        </div>
        <div className="landing-samples__grid">
          {samplePreviews.map((item) => (
            <button
              key={item.id}
              className="landing-sample-card"
              onClick={() => setSelectedSample(item.id)}
              type="button"
            >
              <span className="landing-sample-card__type">{item.type}</span>
              <p className="landing-sample-card__title">{item.title}</p>
              <p className="landing-sample-card__desc">{item.summary}</p>
              <div className="landing-sample-card__metrics">
                {item.metrics.map((m) => (
                  <span key={m} className="landing-sample-card__metric">{m}</span>
                ))}
              </div>
            </button>
          ))}
        </div>
      </section>

      {sampleData && (
        <div className="sample-modal-overlay" onClick={() => setSelectedSample(null)}>
          <div className="sample-modal" onClick={(e) => e.stopPropagation()}>
            <span className="sample-modal__eyebrow">{sampleData.eyebrow}</span>
            <h2>{sampleData.title}</h2>
            <p className="sample-modal__summary">{sampleData.summary}</p>
            <div className="sample-modal__highlights">
              {sampleData.highlights.map((h: string) => (
                <span key={h} className="sample-modal__highlight">{h}</span>
              ))}
            </div>
            {sampleData.sections.map((section: { title: string; items: string[] }) => (
              <div key={section.title} className="sample-modal__section">
                <h3>{section.title}</h3>
                <ul>
                  {section.items.map((item: string) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
            <div className="sample-modal__actions">
              <Link
                href="/login"
                className="sample-modal__btn-primary"
                onClick={() => setSelectedSample(null)}
              >
                登录后使用完整功能
              </Link>
              <button
                className="sample-modal__btn-secondary"
                onClick={() => setSelectedSample(null)}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="landing-footer">
        <span className="landing-footer__brand">职航智策 CareerPilot</span>
        <div className="landing-footer__meta">
          <span>隐私保护</span>
          <span>帮助与支持</span>
        </div>
      </footer>
    </div>
  );
}

import Link from "next/link";

import { sampleResultMap } from "@/lib/home-data";

export default async function ResultPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = await params;
  const result = sampleResultMap[resolvedParams.id] || sampleResultMap["report-sample"];

  return (
    <div className="result-page">
      <div className="result-page__container">
        <header className="result-hero">
          <span className="section-kicker">{result.eyebrow}</span>
          <h1>{result.title}</h1>
          <p>{result.summary}</p>
          <div className="result-highlight-row">
            {result.highlights.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </header>

        <section className="result-section-grid">
          {result.sections.map((section) => (
            <article key={section.title} className="result-card">
              <h2>{section.title}</h2>
              <ul className="plain-list">
                {section.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <section className="workspace-actions">
          <Link href="/student/reports" className="app-header__button">
            打开完整报告页
          </Link>
          <Link href="/student/dashboard" className="app-header__button app-header__button--ghost">
            进入学生工作台
          </Link>
          <Link href="/" className="workspace-backlink">
            返回首页
          </Link>
        </section>
      </div>
    </div>
  );
}

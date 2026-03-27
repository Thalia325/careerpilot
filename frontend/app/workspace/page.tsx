import Link from "next/link";

const stages = [
  { title: "材料读取", description: "确认已上传的简历和补充信息。" },
  { title: "能力识别", description: "分析技能、证书、项目和实习经历。" },
  { title: "岗位匹配", description: "对比目标岗位要求，识别差距项。" },
  { title: "路径规划", description: "生成主路径、备选路径与行动计划。" },
  { title: "报告输出", description: "整理为可编辑、可导出的职业规划报告。" }
];

export default async function WorkspacePage({
  searchParams
}: {
  searchParams: Promise<{ query?: string; resume?: string }>;
}) {
  const resolvedSearchParams = await searchParams;
  const query = resolvedSearchParams.query || "前端开发工程师";
  const resume = resolvedSearchParams.resume || "未上传简历";

  return (
    <div className="workspace-page">
      <div className="workspace-page__container">
        <header className="workspace-hero">
          <span className="section-kicker">任务工作台</span>
          <h1>已开始新的职业规划任务</h1>
          <p>你可以继续补充目标岗位或材料信息，系统会按当前任务流完成分析并生成结果。</p>
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
                <strong>准备分析</strong>
              </li>
            </ul>
          </article>

          <article className="workspace-card">
            <h2>分析步骤</h2>
            <div className="workspace-stage-list">
              {stages.map((stage, index) => (
                <div key={stage.title} className="workspace-stage-item">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{stage.title}</strong>
                    <p>{stage.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="workspace-actions">
          <Link href="/student/upload" className="app-header__button app-header__button--ghost">
            继续上传材料
          </Link>
          <Link href="/results/report-sample" className="app-header__button">
            查看示例结果
          </Link>
          <Link href="/" className="workspace-backlink">
            返回首页
          </Link>
        </section>
      </div>
    </div>
  );
}

type WorkflowSectionProps = {
  items: Array<{
    step: string;
    title: string;
    description: string;
  }>;
};

export function WorkflowSection({ items }: WorkflowSectionProps) {
  return (
    <section id="help" className="home-section">
      <div className="home-section__heading">
        <div>
          <span className="section-kicker">使用流程</span>
          <h2>三步开始一轮职业规划</h2>
        </div>
      </div>
      <div className="workflow-grid">
        {items.map((item) => (
          <article key={item.step} className="workflow-card">
            <span className="workflow-card__step">{item.step}</span>
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}


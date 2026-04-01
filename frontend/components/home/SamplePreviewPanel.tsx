import Link from "next/link";

type SamplePreviewPanelProps = {
  items: Array<{
    id: string;
    type: string;
    title: string;
    summary: string;
    metrics: string[];
  }>;
};

export function SamplePreviewPanel({ items }: SamplePreviewPanelProps) {
  return (
    <section id="examples" className="dashboard-panel">
      <div className="dashboard-panel__header">
        <div>
          <span className="section-kicker">示例结果</span>
          <h3>先看看你会得到什么</h3>
        </div>
      </div>
      <div className="sample-preview-list">
        {items.map((item) => (
          <Link key={item.id} href={`/results/${item.id}`} className="sample-preview-card">
            <span className="sample-preview-card__type">{item.type}</span>
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
            <div className="sample-preview-card__metrics">
              {item.metrics.map((metric) => (
                <span key={metric}>{metric}</span>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}


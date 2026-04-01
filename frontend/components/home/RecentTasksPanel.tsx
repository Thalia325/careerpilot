import Link from "next/link";

type RecentTasksPanelProps = {
  items: Array<{
    id: string;
    title: string;
    subtitle: string;
    status: string;
    time: string;
    href: string;
  }>;
};

export function RecentTasksPanel({ items }: RecentTasksPanelProps) {
  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel__header">
        <div>
          <span className="section-kicker">最近任务</span>
          <h3>继续你上次的分析</h3>
        </div>
      </div>
      <div className="recent-task-list">
        {items.map((item) => (
          <Link key={item.id} href={item.href} className="recent-task-item">
            <div>
              <strong>{item.title}</strong>
              <p>{item.subtitle}</p>
            </div>
            <div className="recent-task-item__meta">
              <span className={`status-pill status-pill--${item.status === "已完成" ? "done" : "pending"}`}>{item.status}</span>
              <small>{item.time}</small>
              <span className="recent-task-item__cta">点击继续 <span aria-hidden="true">→</span></span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}


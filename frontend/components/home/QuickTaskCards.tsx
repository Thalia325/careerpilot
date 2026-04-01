import Link from "next/link";

type QuickTaskCardsProps = {
  items: Array<{
    id: string;
    icon: string;
    title: string;
    description: string;
    href: string;
  }>;
};

export function QuickTaskCards({ items }: QuickTaskCardsProps) {
  return (
    <section id="tasks" className="home-section">
      <div className="home-section__heading">
        <div>
          <span className="section-kicker">快捷任务</span>
          <h2>选择一种方式开始</h2>
        </div>
      </div>
      <div className="quick-task-grid">
        {items.map((item) => (
          <Link key={item.id} href={item.href} className="quick-task-card">
            <span className="quick-task-card__icon">{item.icon}</span>
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}


import Link from "next/link";

type SecondaryAccessSectionProps = {
  items: Array<{
    id: string;
    title: string;
    description: string;
    href: string;
  }>;
};

export function SecondaryAccessSection({ items }: SecondaryAccessSectionProps) {
  return (
    <section className="home-section home-section--secondary">
      <div className="home-section__heading">
        <div>
          <span className="section-kicker">更多工作台入口</span>
          <h2>面向教师与运营团队的次级入口</h2>
        </div>
      </div>
      <div className="secondary-access-grid">
        {items.map((item) => (
          <Link key={item.id} href={item.href} className="secondary-access-card">
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}


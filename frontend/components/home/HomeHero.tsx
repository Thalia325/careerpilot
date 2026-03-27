import { AgentComposer } from "./AgentComposer";

type HomeHeroProps = {
  roleTags: string[];
};

export function HomeHero({ roleTags }: HomeHeroProps) {
  return (
    <section className="home-hero">
      <div className="home-hero__copy">
        <span className="section-kicker">AI 职业规划助手</span>
        <h1>让职业规划从一份简历开始</h1>
        <p>
          上传简历或输入目标岗位，系统将生成能力画像、岗位匹配分析、成长路径建议，并输出职业规划报告。
        </p>
      </div>
      <AgentComposer roleTags={roleTags} />
    </section>
  );
}


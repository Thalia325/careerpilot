import Link from "next/link";
import styles from "./home.module.css";

const heroSteps = [
  {
    step: "01",
    title: "上传简历",
    description: "支持 PDF、DOC、DOCX、PNG、JPG、JPEG，先把你的经历交给 AI。",
  },
  {
    step: "02",
    title: "生成能力档案",
    description: "从技能、证书、项目、学习能力等维度拆解你的真实基础。",
  },
  {
    step: "03",
    title: "匹配合适岗位",
    description: "基于四维匹配模型判断你和目标岗位的契合度与差距。",
  },
  {
    step: "04",
    title: "导出规划报告",
    description: "输出发展路径、分阶段行动计划和可编辑可导出的完整报告。",
  },
];

const resonanceScenarios = [
  "快毕业了，还不知道自己到底适合什么岗位？",
  "考研、考公、进大厂，方向太多，反而更难做决定。",
  "感觉自己什么都会一点，又什么都不够拿得出手。",
  "刷了很多经验贴，还是不知道下一步该补什么、投什么。",
];

const featureCards = [
  {
    title: "岗位能力要求",
    description:
      "解析信息化相关行业 100+ 岗位画像，查看技能要求、晋升路径和转换方向。",
    caption: "岗位探索",
    chips: ["岗位要求", "薪资范围", "转换方向"],
    lines: ["数据分析师", "核心技能：SQL / Python / Tableau", "晋升路径：初级 → 资深 → 负责人"],
  },
  {
    title: "我的能力档案",
    description:
      "上传简历或手动录入后，AI 会从专业技能、证书、创新力、学习力等方面整理你的能力画像。",
    caption: "能力分析",
    chips: ["完整度", "竞争力", "证据链"],
    lines: ["技能覆盖 8 项", "竞争力评分 86", "证据链 7 条"],
  },
  {
    title: "制定我的职业规划",
    description:
      "把岗位匹配、发展路径和短中期行动计划串成一份可以持续迭代的职业规划报告。",
    caption: "职业规划",
    chips: ["岗位匹配", "行动计划", "一键导出"],
    lines: ["目标岗位：产品经理", "短期计划：补齐项目表达", "支持 PDF / DOCX 导出"],
  },
];

const sampleFlow = [
  { label: "输入", value: "一份简历（脱敏）" },
  { label: "输出 1", value: "能力分析结果：七维能力评分 + 证据链" },
  { label: "输出 2", value: "岗位匹配结果：匹配度分数 + 差距项" },
  { label: "输出 3", value: "职业规划报告：路径建议 + 短中期行动计划" },
];

const roleExamples = [
  { title: "产品经理", note: "能力档案 + 目标岗位建议" },
  { title: "UI 设计师", note: "岗位匹配 + 作品集补强方向" },
  { title: "数据分析师", note: "四维匹配 + 项目证据缺口" },
  { title: "市场营销", note: "职业规划报告 + 行动计划" },
  { title: "金融分析师", note: "路径建议 + 能力补强节奏" },
];

const chatMessages = [
  {
    role: "assistant",
    content:
      "你好！我是职航智策，你的 AI 职业规划助手。上传简历或告诉我你的情况，我来帮你分析能力、匹配岗位、制定职业规划。",
  },
  {
    role: "user",
    content: "我学的是软件工程，想看看自己更适合前端、产品还是数据分析。",
  },
  {
    role: "assistant",
    content:
      "可以。我会先拆解你的技能、项目和实习经历，再给出岗位匹配度、差距项和下一步行动建议。",
  },
];

const chatPrompts = [
  "帮我分析我的简历",
  "我和这个岗位的匹配度",
  "适合我的职业发展路径",
  "我下一步该补什么项目",
];

const highlightGroups = [
  {
    title: "AI 驱动",
    bubbles: ["自动解析简历", "生成画像", "匹配岗位", "生成报告"],
  },
  {
    title: "6800+ 清洗岗位数据",
    bubbles: ["100+ 岗位画像", "产品经理", "UI 设计师", "数据分析师", "金融分析师", "市场营销"],
  },
  {
    title: "四维匹配模型",
    bubbles: ["基础要求", "职业技能", "职业素养", "发展潜力"],
  },
  {
    title: "分析可落地",
    bubbles: ["短期计划", "中期计划", "报告导出", "教师跟进"],
  },
  {
    title: "可信结果",
    bubbles: ["匹配准确率 ≥ 80%", "关键信息准确率超 90%", "本地化数据集", "受控存储"],
  },
];

const promotionPath = [
  "UI 设计师",
  "资深设计师",
  "设计组长",
  "设计总监",
];

const transitionPaths = [
  { role: "产品经理", paths: ["运营专员 → 产品经理", "数据分析师 → 产品经理"] },
  { role: "UI 设计师", paths: ["平面设计 → UI 设计师", "交互设计 → UI 设计师"] },
  { role: "数据分析师", paths: ["运营专员 → 数据分析师", "财务分析 → 数据分析师"] },
  { role: "项目经理", paths: ["测试工程师 → 项目经理", "实施顾问 → 项目经理"] },
  { role: "金融分析师", paths: ["会计 → 金融分析师", "数据分析师 → 金融分析师"] },
];

const innovationPoints = [
  "岗位图谱把岗位要求、晋升路径和转换方向放到同一张图里看。",
  "四维匹配模型不只看技能命中，还会考虑职业素养和发展潜力。",
  "本地化清洗岗位数据和学生画像链路打通，不是只做静态问卷推荐。",
];

const architectureLayers = [
  { title: "前端交互层", detail: "对话式主页、上传入口、结果页、教师端反馈" },
  { title: "智能体编排层", detail: "简历解析、画像生成、岗位匹配、职业规划报告" },
  { title: "模型与规则层", detail: "大模型 + OCR + 匹配规则 + 报告导出" },
  { title: "数据与知识层", detail: "岗位数据集、岗位画像、学生档案、本地知识库" },
];

const faqs = [
  {
    question: "支持哪些行业的岗位？",
    answer: "当前重点覆盖信息化相关行业的 100+ 岗位画像，包含产品、设计、测试、数据、运营等方向。",
  },
  {
    question: "我的简历安全吗？",
    answer: "数据仅用于当前分析和报告生成，不会用于无关用途；页面也会明确提示“简历仅用于分析”。",
  },
  {
    question: "分析结果准确吗？",
    answer: "系统基于四维匹配模型给出建议，试运行样本中关键匹配信息准确率超过 80%，但仍建议结合老师或导师意见使用。",
  },
  {
    question: "需要付费吗？",
    answer: "当前演示版本可免费使用。",
  },
  {
    question: "上传文件支持哪些格式？",
    answer: "支持 PDF、DOC、DOCX、PNG、JPG、JPEG。",
  },
  {
    question: "分析一次时长大概多久？",
    answer: "通常几十秒可以返回初步结果，材料较多或内容较复杂时会稍长一些。",
  },
];

export default function HomePage() {
  return (
    <main className={styles.page}>
      <div className={styles.backgroundGlow} aria-hidden="true" />

      <header className={styles.header}>
        <Link href="/" className={styles.brand}>
          <span className={styles.brandLogo}>CP</span>
          <span>
            <strong>职航智策</strong>
            <small>AI 职业规划助手</small>
          </span>
        </Link>
        <div className={styles.headerActions}>
          <Link href="/login" className={styles.headerButton}>
            登录
          </Link>
          <Link href="/register" className={styles.headerButtonPrimary}>
            注册
          </Link>
        </div>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.badge}>AI 职业规划助手</span>
          <p className={styles.kicker}>第一份职业规划，从这里开始</p>
          <h1>找工作之前，先找到自己</h1>
          <p className={styles.lead}>
            职航智策面向大学生，把“能力分析、岗位匹配、职业规划报告”串成一条清晰路径。
            你负责努力，AI 负责帮你把方向和下一步拆明白。
          </p>
          <div className={styles.heroActions}>
            <Link href="/login" className={styles.primaryButton}>
              立即体验
            </Link>
            <a href="#features" className={styles.secondaryButton}>
              先看功能
            </a>
          </div>
          <p className={styles.heroHint}>
            简历仅用于分析。支持 PDF、DOC、DOCX、PNG、JPG、JPEG。
          </p>
        </div>

        <div className={styles.flowPanel}>
          <div className={styles.flowHeader}>
            <p>核心引导</p>
            <h2>四步开始一轮职业规划</h2>
          </div>
          <div className={styles.flowGrid}>
            {heroSteps.map((item, index) => (
              <div key={item.step} className={styles.flowItem}>
                <span className={styles.flowNumber}>{item.step}</span>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
                {index < heroSteps.length - 1 && (
                  <span className={styles.flowArrow} aria-hidden="true">
                    →
                  </span>
                )}
              </div>
            ))}
          </div>
          <div className={styles.heroStats}>
            <span>6800+ 清洗岗位数据</span>
            <span>100+ 岗位画像</span>
            <span>四维匹配模型</span>
            <span>支持报告导出</span>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>场景共鸣区</span>
          <h2>这些问题，很多同学都遇到过</h2>
          <p>先别急着投简历。先把自己适合什么、缺什么、下一步该做什么想明白。</p>
        </div>
        <div className={styles.resonanceGrid}>
          {resonanceScenarios.map((item) => (
            <article key={item} className={styles.resonanceCard}>
              <span className={styles.resonanceMark}>“</span>
              <p>{item}</p>
            </article>
          ))}
        </div>
        <div className={styles.centerAction}>
          <Link href="/login" className={styles.primaryButton}>
            开始我的职业规划
          </Link>
        </div>
      </section>

      <section id="features" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>核心功能</span>
          <h2>把看不清的职业问题，拆成三个能执行的模块</h2>
          <p>功能名、说明和结果样式都尽量说人话，不堆概念词。</p>
        </div>
        <div className={styles.featureGrid}>
          {featureCards.map((item) => (
            <article key={item.title} className={styles.featureCard}>
              <div className={styles.featureTop}>
                <span className={styles.featureCaption}>{item.caption}</span>
                <div className={styles.featureChips}>
                  {item.chips.map((chip) => (
                    <span key={chip}>{chip}</span>
                  ))}
                </div>
              </div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <div className={styles.featureMock}>
                {item.lines.map((line) => (
                  <span key={line}>{line}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section id="examples" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>真实效果</span>
          <h2>不是只给一句结论，而是把整个分析链路摆出来</h2>
          <p>示例岗位尽量多样化，让用户先看到自己可能拿到什么结果。</p>
        </div>

        <div className={styles.exampleGrid}>
          <article className={styles.caseFlowCard}>
            <div className={styles.cardHeader}>
              <span>完整案例流程</span>
              <strong>从一份简历到一份规划报告</strong>
            </div>
            <div className={styles.caseFlowList}>
              {sampleFlow.map((item) => (
                <div key={item.label} className={styles.caseFlowItem}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </article>

          <article className={styles.chatCard}>
            <div className={styles.cardHeader}>
              <span>对话式交互预览</span>
              <strong>主页就先展示它会怎么和你说话</strong>
            </div>
            <div className={styles.chatWindow}>
              {chatMessages.map((item, index) => (
                <div
                  key={`${item.role}-${index}`}
                  className={item.role === "assistant" ? styles.chatAssistant : styles.chatUser}
                >
                  {item.content}
                </div>
              ))}
            </div>
            <div className={styles.promptRow}>
              {chatPrompts.map((prompt) => (
                <span key={prompt}>{prompt}</span>
              ))}
            </div>
          </article>
        </div>

        <div className={styles.roleExampleRow}>
          {roleExamples.map((item) => (
            <article key={item.title} className={styles.roleCard}>
              <strong>{item.title}</strong>
              <span>{item.note}</span>
            </article>
          ))}
        </div>

        <div className={styles.centerAction}>
          <Link href="/login" className={styles.primaryButton}>
            我也要试试
          </Link>
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>产品亮点</span>
          <h2>亮点别写成长段说明，做成一眼能扫到的泡泡</h2>
          <p>让评委和用户在几秒内抓到这套系统最值得记住的点。</p>
        </div>
        <div className={styles.highlightGrid}>
          {highlightGroups.map((group) => (
            <article key={group.title} className={styles.highlightCard}>
              <h3>{group.title}</h3>
              <div className={styles.bubbleCloud}>
                {group.bubbles.map((bubble) => (
                  <span key={bubble}>{bubble}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.graphGrid}>
          <article className={styles.pathCard}>
            <div className={styles.sectionHeaderLeft}>
              <span>岗位图谱</span>
              <h2>先看一条晋升路径，再看多条可转方向</h2>
            </div>
            <div className={styles.pathTrack}>
              {promotionPath.map((item, index) => (
                <div key={item} className={styles.pathNode}>
                  <strong>{item}</strong>
                  {index < promotionPath.length - 1 && <span aria-hidden="true">→</span>}
                </div>
              ))}
            </div>
            <div className={styles.transitionList}>
              {transitionPaths.map((item) => (
                <div key={item.role} className={styles.transitionItem}>
                  <strong>{item.role}</strong>
                  <div>
                    {item.paths.map((path) => (
                      <span key={path}>{path}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className={styles.innovationCard}>
            <div className={styles.sectionHeaderLeft}>
              <span>创新点与技术架构</span>
              <h2>让评委快速知道你和普通职业测评工具有什么不同</h2>
            </div>
            <ul className={styles.innovationList}>
              {innovationPoints.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <div className={styles.architectureStack}>
              {architectureLayers.map((item) => (
                <div key={item.title} className={styles.architectureLayer}>
                  <strong>{item.title}</strong>
                  <span>{item.detail}</span>
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>

      <section id="faq" className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>常见问题</span>
          <h2>标准着陆页该回答的问题，这里一次讲清楚</h2>
          <p>把用户最关心的岗位范围、隐私、准确性、格式和时长提前说清楚。</p>
        </div>
        <div className={styles.faqList}>
          {faqs.map((item, index) => (
            <details key={item.question} className={styles.faqItem} open={index === 0}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
        <div className={styles.centerAction}>
          <Link href="/login" className={styles.primaryButton}>
            免费开始使用
          </Link>
        </div>
      </section>

      <footer id="privacy" className={styles.footer}>
        <div>
          <strong>职航智策 CareerPilot</strong>
          <p>第十七届服创大赛 A 类企业命题参赛作品</p>
        </div>
        <div className={styles.footerMeta}>
          <span>AI 分析结果仅供参考，不构成唯一职业决策依据。</span>
          <span>版本 v0.1.0 · 更新于 2026-04-21</span>
        </div>
        <div className={styles.footerLinks}>
          <a href="#faq">常见问题</a>
          <a href="#features">功能介绍</a>
          <a href="#examples">示例展示</a>
          <span id="support">帮助与支持</span>
          <span>用户协议 / 隐私说明</span>
        </div>
      </footer>
    </main>
  );
}

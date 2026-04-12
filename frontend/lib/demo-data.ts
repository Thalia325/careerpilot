export const demoStudentProfile = {
  student_id: 1,
  source_summary: "简历、证书、手动录入",
  skills: ["需求分析", "原型设计", "SQL", "Python", "Excel", "PPT", "数据可视化", "沟通协调"],
  certificates: ["英语六级", "PMP 项目管理认证"],
  capability_scores: {
    专业技能: 82,
    创新能力: 79,
    学习能力: 85,
    抗压能力: 74,
    沟通能力: 88,
    实习能力: 76
  },
  completeness_score: 88,
  competitiveness_score: 84,
  willingness: {
    target_job: "产品经理",
    preferred_city: "北京"
  },
  evidence: [
    { source: "resume.pdf", excerpt: "实习经历：某互联网公司产品实习生，负责需求分析和原型设计", confidence: 0.92 },
    { source: "手动录入", excerpt: "补充项目：校园电商平台产品设计方案", confidence: 0.95 }
  ]
};

export const demoMatching = {
  student_id: 1,
  job_code: "J-PM-001",
  total_score: 85.6,
  weights: {
    basic_requirements: 0.15,
    professional_skills: 0.45,
    professional_literacy: 0.2,
    development_potential: 0.2
  },
  dimensions: [
    { dimension: "基础要求", score: 78, weight: 0.15, reasoning: "证书部分满足，实习经历匹配度高", evidence: {} },
    { dimension: "职业技能", score: 87, weight: 0.45, reasoning: "需求分析和原型设计能力覆盖较高", evidence: {} },
    { dimension: "职业素养", score: 86, weight: 0.2, reasoning: "沟通与抗压表现稳定", evidence: {} },
    { dimension: "发展潜力", score: 88, weight: 0.2, reasoning: "学习能力与创新能力较强", evidence: {} }
  ],
  gap_items: [
    { type: "skill", name: "数据分析", suggestion: "加强 SQL 和数据可视化工具的实践应用。" },
    { type: "skill", name: "技术理解力", suggestion: "建议了解基础的前端和后端技术架构。" }
  ],
  suggestions: ["完善 1 个完整的产品从 0 到 1 案例", "加强跨部门协作经验表达", "定期复盘产品方法论积累"],
  summary: "适合优先冲刺产品经理岗位，优势在于需求分析和沟通协调能力，短板在数据分析深度与技术理解力。"
};

export const demoPath = {
  primary_path: ["产品助理/初级产品经理", "产品经理", "高级产品经理/产品总监"],
  alternate_paths: [
    ["产品助理", "运营经理"],
    ["产品助理", "项目经理"]
  ],
  rationale: "依据岗位图谱、技能相邻度与学生当前能力结构推荐。",
  recommendations: [
    { phase: "短期", focus: "补齐数据分析与技术理解能力", items: ["SQL", "数据可视化", "基础技术架构"] },
    { phase: "中期", focus: "形成完整产品案例和跨部门协作经验", items: ["实习", "产品案例", "复盘"] }
  ]
};

export type JobCategory = "产品/技术" | "设计/创意" | "运营/市场" | "金融/商务" | "人力/行政" | "教育/咨询";

export interface JobDetail {
  title: string;
  category: JobCategory;
  description: string;
  salary_range: string;
  skills: string[];
  abilities: string[];
  certificates: string[];
  tools: string[];
  career_path: string[];
}

export const demoJobTemplates: JobDetail[] = [
  {
    title: "产品经理",
    category: "产品/技术",
    description: "负责产品的全生命周期管理，从需求调研到上线迭代，连接用户需求与商业目标。",
    salary_range: "15K-30K",
    skills: ["需求分析", "原型设计", "数据驱动决策", "项目管理", "用户调研", "竞品分析", "沟通协调", "产品战略"],
    abilities: ["逻辑思维能力", "跨部门协作能力", "用户同理心", "商业敏感度", "抗压能力", "快速学习能力"],
    certificates: ["NPDP 产品经理认证", "PMP 项目管理认证"],
    tools: ["Axure", "Figma", "Jira", "SQL", "ProcessOn"],
    career_path: ["产品助理", "产品经理", "高级产品经理", "产品总监", "VP/首席产品官"]
  },
  {
    title: "数据分析师",
    category: "产品/技术",
    description: "通过数据采集、清洗、建模和可视化，为业务决策提供量化依据和洞察。",
    salary_range: "12K-25K",
    skills: ["SQL", "Python/R", "数据可视化", "统计分析", "ETL处理", "A/B测试", "指标体系搭建", "报表自动化"],
    abilities: ["逻辑推理能力", "业务理解能力", "数据敏感度", "细节把控能力", "跨团队沟通能力", "结构化思维"],
    certificates: ["CDA 数据分析师认证", "Google Data Analytics Certificate"],
    tools: ["Python", "SQL", "Tableau", "Power BI", "Excel", "Pandas"],
    career_path: ["数据分析师", "高级数据分析师", "数据科学家", "数据分析总监"]
  },
  {
    title: "项目经理",
    category: "产品/技术",
    description: "统筹项目资源、进度和风险，协调多方团队确保项目按时按质交付。",
    salary_range: "15K-30K",
    skills: ["项目计划制定", "风险管理", "敏捷/Scrum", "资源协调", "需求管理", "进度控制", "质量保障", "沟通汇报"],
    abilities: ["领导力", "压力管理能力", "决策能力", "多任务并行处理", "谈判与冲突解决", "系统性思维"],
    certificates: ["PMP 项目管理认证", "PRINCE2 认证", "Scrum Master"],
    tools: ["Jira", "Confluence", "Microsoft Project", "Notion", "飞书"],
    career_path: ["项目助理", "项目经理", "高级项目经理", "项目总监", "PMO负责人"]
  },
  {
    title: "UI/UX 设计师",
    category: "设计/创意",
    description: "通过用户研究和视觉设计，打造美观、易用的数字产品界面与交互体验。",
    salary_range: "12K-25K",
    skills: ["视觉设计", "交互设计", "用户研究", "设计系统搭建", "信息架构", "动效设计", "可用性测试", "品牌设计"],
    abilities: ["审美能力", "用户同理心", "创造性思维", "细节把控", "跨端适配思维", "设计表达能力"],
    certificates: ["NN/g UX 认证", "Adobe Certified Professional"],
    tools: ["Figma", "Sketch", "Adobe XD", "Principle", "Illustrator", "Photoshop"],
    career_path: ["初级设计师", "UI/UX 设计师", "高级设计师", "设计主管", "设计总监"]
  },
  {
    title: "内容策划",
    category: "设计/创意",
    description: "制定内容策略与创意方案，通过文字、视频、图文等形式传递品牌价值。",
    salary_range: "10K-20K",
    skills: ["创意写作", "选题策划", "内容运营", "用户洞察", "多平台分发", "数据复盘", "视频脚本", "品牌叙事"],
    abilities: ["创造力", "文字表达能力", "热点敏感度", "用户洞察力", "多线程执行", "审美能力"],
    certificates: ["新媒体运营师", "内容营销认证"],
    tools: ["135编辑器", "Canva", "剪映", "Notion", "飞书文档"],
    career_path: ["内容编辑", "内容策划", "高级策划", "内容运营经理", "品牌总监"]
  },
  {
    title: "运营专员",
    category: "运营/市场",
    description: "通过内容运营、活动策划和用户增长手段，提升产品活跃度和用户留存。",
    salary_range: "8K-18K",
    skills: ["内容运营", "活动策划", "数据分析", "用户增长", "社区运营", "新媒体运营", "渠道推广", "复盘优化"],
    abilities: ["执行能力", "数据敏感度", "创意策划能力", "用户服务意识", "抗压能力", "沟通协调能力"],
    certificates: ["新媒体运营师", "Google Analytics 认证"],
    tools: ["飞书", "微信公众号后台", "小红书", "抖音企业号", "神策数据"],
    career_path: ["运营专员", "运营主管", "运营经理", "运营总监", "COO"]
  },
  {
    title: "市场营销专员",
    category: "运营/市场",
    description: "负责品牌推广、市场调研与营销活动执行，提升品牌知名度和市场占有率。",
    salary_range: "10K-22K",
    skills: ["品牌策划", "市场调研", "文案撰写", "数字营销", "渠道推广", "活动执行", "SEO/SEM", "竞品分析"],
    abilities: ["市场洞察力", "创意思维", "谈判能力", "数据分析能力", "品牌意识", "跨部门协调"],
    certificates: ["Google Ads 认证", "HubSpot Inbound Marketing"],
    tools: ["Google Analytics", "百度推广", "SEMrush", "飞书", "Excel"],
    career_path: ["市场专员", "市场主管", "市场经理", "市场总监", "CMO"]
  },
  {
    title: "金融分析师",
    category: "金融/商务",
    description: "通过财务建模、行业研究和估值分析，为投资决策和企业经营提供专业建议。",
    salary_range: "18K-40K",
    skills: ["财务建模", "行业研究", "估值分析", "Excel高级建模", "数据收集与处理", "报告撰写", "风险控制", "投资分析"],
    abilities: ["数字敏感度", "逻辑分析能力", "研究深度", "抗压能力", "决策判断力", "商业洞察力"],
    certificates: ["CFA 特许金融分析师", "FRM 金融风险管理", "CPA 注册会计师"],
    tools: ["Excel", "Wind", "Bloomberg", "Python", "SQL", "Tableau"],
    career_path: ["助理分析师", "金融分析师", "高级分析师", "投资经理", "投资总监"]
  },
  {
    title: "人力资源专员",
    category: "人力/行政",
    description: "负责招聘、培训、绩效、薪酬等模块，搭建和管理企业人才体系。",
    salary_range: "8K-16K",
    skills: ["招聘管理", "培训发展", "绩效管理", "薪酬福利", "员工关系", "劳动法规", "组织发展", "HRBP"],
    abilities: ["沟通能力", "人际关系处理", "判断力", "保密意识", "抗压能力", "制度执行能力"],
    certificates: ["人力资源管理师", "心理咨询师基础培训"],
    tools: ["北森", "Moka", "钉钉", "飞书人事", "Excel"],
    career_path: ["人事专员", "人事主管", "人事经理", "HRD", "CHO"]
  },
  {
    title: "教育培训师",
    category: "教育/咨询",
    description: "设计并实施教学方案，通过课程开发和面授/在线教学帮助学员提升能力。",
    salary_range: "8K-20K",
    skills: ["课程设计", "教学表达", "学习理论应用", "教育技术", "评估设计", "学员管理", "在线教学", "项目制学习"],
    abilities: ["表达能力", "耐心", "共情能力", "知识体系化能力", "课堂控场能力", "持续学习能力"],
    certificates: ["教师资格证", "TTT 培训师认证", "心理咨询师"],
    tools: ["PPT", "Zoom/腾讯会议", "Canvas", "Notion", "问卷星"],
    career_path: ["助教/培训助理", "培训师", "高级培训师", "培训经理", "培训总监/教学总监"]
  }
];

export const demoReportMarkdown = `# 职业发展报告

## 一、职业探索与岗位匹配
当前综合匹配度 85.6 分，建议优先冲刺产品经理岗位。

## 二、职业目标与路径规划
- 岗位晋升路径：产品助理 → 产品经理 → 高级产品经理/产品总监
- 岗位转换方向：产品助理 → 运营经理 / 项目经理

## 三、行动计划
- 短期：补齐 SQL/数据分析技能、提升技术理解力、完成一份完整产品方案
- 中期：完成产品实习、每月复盘一次成长指标

## 四、依据说明
- 已综合岗位能力要求、我的能力档案、图谱路径与四维匹配结果
`;

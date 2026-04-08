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

export const demoJobTemplates = [
  "产品经理",
  "UI/UX 设计师",
  "运营专员",
  "市场营销专员",
  "数据分析师",
  "人力资源专员",
  "项目经理",
  "金融分析师",
  "教育培训师",
  "内容策划"
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

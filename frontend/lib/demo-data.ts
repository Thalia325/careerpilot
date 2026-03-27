export const demoStudentProfile = {
  student_id: 1,
  source_summary: "简历、证书、手动录入",
  skills: ["JavaScript", "TypeScript", "React", "Next.js", "Python", "FastAPI"],
  certificates: ["英语四级", "计算机二级"],
  capability_scores: {
    innovation: 79,
    learning: 85,
    resilience: 74,
    communication: 81,
    internship: 76
  },
  completeness_score: 88,
  competitiveness_score: 84,
  willingness: {
    target_job: "前端开发工程师",
    preferred_city: "西安"
  },
  evidence: [
    { source: "demo_resume.txt", excerpt: "OCR 提取技能：React", confidence: 0.92 },
    { source: "手动录入", excerpt: "补充项目：CareerPilot 职业规划系统", confidence: 0.95 }
  ]
};

export const demoMatching = {
  student_id: 1,
  job_code: "J-FE-001",
  total_score: 82.4,
  weights: {
    basic_requirements: 0.15,
    professional_skills: 0.45,
    professional_literacy: 0.2,
    development_potential: 0.2
  },
  dimensions: [
    { dimension: "基础要求", score: 72, weight: 0.15, reasoning: "证书部分满足，实习能力较好", evidence: {} },
    { dimension: "职业技能", score: 85, weight: 0.45, reasoning: "核心前端技能覆盖较高", evidence: {} },
    { dimension: "职业素养", score: 81, weight: 0.2, reasoning: "沟通与抗压表现较稳定", evidence: {} },
    { dimension: "发展潜力", score: 86, weight: 0.2, reasoning: "学习能力与创新能力较强", evidence: {} }
  ],
  gap_items: [
    { type: "skill", name: "HTML", suggestion: "补齐语义化与可访问性实践。" },
    { type: "skill", name: "CSS", suggestion: "提升响应式与动画实现能力。" }
  ],
  suggestions: ["完善 1 个真实前端项目", "加强跨团队协作表达", "定期复盘技能覆盖率"],
  summary: "适合优先冲刺前端开发工程师，优势在于 React / Next.js 体系，短板在基础样式能力与实战深度。"
};

export const demoPath = {
  primary_path: ["前端开发工程师", "高级前端工程师", "前端架构师"],
  alternate_paths: [
    ["前端开发工程师", "全栈工程师"],
    ["前端开发工程师", "产品经理"]
  ],
  rationale: "依据岗位图谱、技能相邻度与学生当前能力结构推荐。",
  recommendations: [
    { phase: "短期", focus: "补齐 HTML / CSS 与工程化能力", items: ["HTML", "CSS", "性能优化"] },
    { phase: "中期", focus: "形成完整业务闭环项目经验", items: ["实习", "项目", "复盘"] }
  ]
};

export const demoJobTemplates = [
  "前端开发工程师",
  "后端开发工程师",
  "全栈工程师",
  "测试工程师",
  "测试开发工程师",
  "数据分析师",
  "数据工程师",
  "数据产品经理",
  "AI 算法工程师",
  "运维工程师",
  "UI/UX 设计师",
  "产品经理"
];

export const demoReportMarkdown = `# CareerPilot 职业发展报告

## 一、职业探索与岗位匹配
当前综合匹配度 82.4 分，建议优先冲刺前端开发工程师。

## 二、职业目标与路径规划
- 主路径：前端开发工程师 -> 高级前端工程师 -> 前端架构师
- 备选路径：前端开发工程师 -> 全栈工程师

## 三、行动计划
- 短期：补齐 HTML/CSS、优化项目表达、完成一次模拟面试
- 中期：完成实习或竞赛项目，每月复盘一次成长指标

## 四、依据说明
- 已综合岗位画像、学生画像、图谱路径与四维匹配结果
`;


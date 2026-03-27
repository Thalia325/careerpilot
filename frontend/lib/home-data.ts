export const composerRoleTags = ["数据分析", "Java 开发", "产品经理", "新媒体运营"];

export const quickTaskTemplates = [
  {
    id: "resume-analysis",
    icon: "RA",
    title: "简历分析",
    description: "提取技能、项目、实习经历，生成个人画像。",
    href: "/workspace?task=resume-analysis"
  },
  {
    id: "job-matching",
    icon: "JM",
    title: "岗位匹配",
    description: "查看目标岗位适配度与能力缺口。",
    href: "/workspace?task=job-matching"
  },
  {
    id: "path-planning",
    icon: "PP",
    title: "路径规划",
    description: "生成主路径、备选路径和阶段任务。",
    href: "/workspace?task=path-planning"
  },
  {
    id: "report-generation",
    icon: "RG",
    title: "报告生成",
    description: "输出可编辑、可导出的职业规划报告。",
    href: "/results/report-sample"
  }
];

export const recentTasks = [
  {
    id: "recent-resume",
    title: "简历分析",
    subtitle: "校园项目与实习经历已识别，可继续补充目标岗位。",
    status: "待补充",
    time: "10 分钟前",
    href: "/workspace?task=resume-analysis&resume=careerpilot_resume.pdf"
  },
  {
    id: "recent-matching",
    title: "岗位匹配",
    subtitle: "前端开发工程师匹配已完成，可查看差距项。",
    status: "已完成",
    time: "今天 14:20",
    href: "/results/matching-sample"
  },
  {
    id: "recent-report",
    title: "职业规划报告",
    subtitle: "已生成可编辑报告，支持 PDF / DOCX 导出。",
    status: "已完成",
    time: "昨天 18:40",
    href: "/results/report-sample"
  }
];

export const samplePreviews = [
  {
    id: "profile-sample",
    type: "能力画像",
    title: "前端方向画像预览",
    summary: "技能结构、证书情况、学习能力与实习能力一页可见。",
    metrics: ["技能覆盖 7 项", "竞争力 84", "证据链 6 条"]
  },
  {
    id: "matching-sample",
    type: "岗位匹配",
    title: "岗位适配度示例",
    summary: "从基础要求、职业技能、职业素养、发展潜力四维分析。",
    metrics: ["匹配度 87.6", "差距项 1 个", "建议 3 条"]
  },
  {
    id: "report-sample",
    type: "规划报告",
    title: "职业报告样例",
    summary: "主路径、备选路径、行动计划与评估指标完整输出。",
    metrics: ["主路径 3 阶段", "短中期计划", "支持导出"]
  }
];

export const workflowSteps = [
  {
    step: "01",
    title: "上传或输入",
    description: "上传简历，或直接输入目标岗位与想咨询的问题。"
  },
  {
    step: "02",
    title: "AI 分析",
    description: "系统生成能力画像、岗位匹配与成长路径建议。"
  },
  {
    step: "03",
    title: "获得结果",
    description: "查看报告、继续补充材料，并持续跟踪职业规划进展。"
  }
];

export const secondaryAccessCards = [
  {
    id: "teacher",
    title: "教师工作台",
    description: "查看班级画像、批量报告与复核管理。",
    href: "/teacher"
  },
  {
    id: "admin",
    title: "管理后台",
    description: "进行岗位运营、评测中心与系统监控。",
    href: "/admin"
  }
];

export const sampleResultMap: Record<
  string,
  {
    eyebrow: string;
    title: string;
    summary: string;
    highlights: string[];
    sections: Array<{ title: string; items: string[] }>;
  }
> = {
  "profile-sample": {
    eyebrow: "能力画像示例",
    title: "从简历中看到你的职业基础",
    summary: "系统会将技能、证书、项目与实习经历整理成可解释的能力画像，作为后续岗位匹配与路径规划的基础。",
    highlights: ["技能覆盖 7 项", "竞争力评分 84", "证据链 6 条"],
    sections: [
      {
        title: "已识别优势",
        items: ["React / Next.js 工程经验", "有真实项目表达", "学习能力与执行能力稳定"]
      },
      {
        title: "建议补充",
        items: ["补充目标岗位意向", "上传更多证书或成绩单材料", "增加项目结果量化表达"]
      }
    ]
  },
  "matching-sample": {
    eyebrow: "岗位匹配示例",
    title: "看清你和目标岗位的契合度",
    summary: "系统会按基础要求、职业技能、职业素养、发展潜力四个维度完成对比，并给出差距项和建议。",
    highlights: ["匹配度 87.6", "技能命中 7/7", "差距项 1 个"],
    sections: [
      {
        title: "契合点",
        items: ["核心前端技能完整", "项目经历与目标岗位方向一致", "学习能力较强，具备成长潜力"]
      },
      {
        title: "差距项",
        items: ["可补充前端专项证书", "建议增加复杂业务场景项目", "进一步提升接口联调案例深度"]
      }
    ]
  },
  "report-sample": {
    eyebrow: "职业报告示例",
    title: "获得一份可执行的职业规划建议",
    summary: "系统将画像、匹配、路径建议和行动计划汇总成可编辑报告，便于你持续更新和导出。",
    highlights: ["主路径 3 阶段", "短中期任务齐全", "支持 PDF / DOCX"],
    sections: [
      {
        title: "推荐路径",
        items: ["前端开发工程师", "高级前端工程师", "前端架构师"]
      },
      {
        title: "行动计划",
        items: ["2 周内补齐薄弱技能", "4 周内沉淀 1 个高质量项目", "每月复盘一次职业目标与进展"]
      }
    ]
  }
};


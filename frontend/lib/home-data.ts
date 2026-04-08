export const composerRoleTags = ["产品经理", "UI设计师", "运营专员", "市场营销", "数据分析师", "人力资源", "项目经理", "金融分析师", "教育培训师", "内容策划"];

export const quickTaskTemplates = [
  {
    id: "resume-analysis",
    icon: "RA",
    title: "分析我的简历",
    description: "提取技能、项目、实习经历，生成我的能力档案。",
    href: "/login"
  },
  {
    id: "job-matching",
    icon: "JM",
    title: "我和这个岗位的匹配度",
    description: "查看目标岗位适配度与能力缺口。",
    href: "/login"
  },
  {
    id: "path-planning",
    icon: "PP",
    title: "制定我的职业规划",
    description: "含岗位匹配 + 发展路径 + 行动计划。",
    href: "/login"
  },
  {
    id: "report-generation",
    icon: "RG",
    title: "生成职业规划报告",
    description: "输出可编辑、可导出的职业规划报告。",
    href: "/login"
  }
];

export const samplePreviews = [
  {
    id: "profile-sample",
    type: "我的能力分析",
    title: "产品经理方向能力档案",
    summary: "技能结构、证书情况、学习能力与沟通能力一页可见。",
    metrics: ["技能覆盖 8 项", "竞争力 86", "证据链 7 条"]
  },
  {
    id: "matching-sample",
    type: "我和这个岗位的匹配度",
    title: "数据分析师岗位适配度",
    summary: "从基础要求、职业技能、职业素养、发展潜力四维分析。",
    metrics: ["匹配度 89.2", "差距项 2 个", "建议 4 条"]
  },
  {
    id: "report-sample",
    type: "职业规划报告",
    title: "市场营销专员发展报告",
    summary: "主路径、备选路径、行动计划与评估指标完整输出。",
    metrics: ["主路径 3 阶段", "短中期计划", "支持导出"]
  },
  {
    id: "ui-designer-sample",
    type: "我的能力分析",
    title: "UI设计师方向能力档案",
    summary: "视觉设计、交互原型、创意表达与工具技能全面评估。",
    metrics: ["技能覆盖 7 项", "竞争力 82", "证据链 5 条"]
  },
  {
    id: "hr-sample",
    type: "我和这个岗位的匹配度",
    title: "人力资源专员岗位适配度",
    summary: "沟通能力、组织协调、招聘培训能力全面分析。",
    metrics: ["匹配度 91.5", "差距项 1 个", "建议 3 条"]
  },
  {
    id: "finance-sample",
    type: "职业规划报告",
    title: "金融分析师发展路径",
    summary: "从金融基础到行业研究、投资分析的完整成长路径。",
    metrics: ["主路径 3 阶段", "短中期计划", "支持导出"]
  }
];

export const workflowSteps = [
  {
    step: "01",
    title: "上传简历/录入信息",
    description: "上传你的简历，或直接手动输入个人信息、技能和经历。"
  },
  {
    step: "02",
    title: "岗位匹配分析",
    description: "系统从四个能力方面分析你与目标岗位的匹配情况。"
  },
  {
    step: "03",
    title: "生成职业规划报告",
    description: "获得完整的职业发展路径、行动计划和可导出报告。"
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
    eyebrow: "我的能力分析",
    title: "从简历中看到你的职业基础",
    summary: "系统会将技能、证书、项目与实习经历整理成可解释的能力档案，作为后续岗位匹配与路径规划的基础。",
    highlights: ["技能覆盖 8 项", "竞争力评分 86", "证据链 7 条"],
    sections: [
      {
        title: "已识别优势",
        items: ["产品原型设计与 Axure/Figma 熟练", "有真实互联网产品实习经历", "沟通能力与学习能力突出", "数据驱动思维良好"]
      },
      {
        title: "建议补充",
        items: ["补充目标岗位意向（如 B 端或 C 端产品方向）", "上传更多证书或成绩单材料", "增加项目结果量化表达"]
      }
    ]
  },
  "matching-sample": {
    eyebrow: "我和这个岗位的匹配度",
    title: "我和数据分析师岗位的匹配度",
    summary: "系统会按基础要求、职业技能、职业素养、发展潜力四个能力方面完成对比，并给出差距项和建议。",
    highlights: ["匹配度 89.2", "技能命中 8/9", "差距项 2 个"],
    sections: [
      {
        title: "契合点",
        items: ["Python 与 SQL 数据处理技能完整", "有数据分析竞赛获奖经历", "学习能力与逻辑分析能力较强"]
      },
      {
        title: "差距项",
        items: ["建议补充 Tableau/PowerBI 可视化工具经验", "可加强大数据场景下的分析项目实践"]
      }
    ]
  },
  "report-sample": {
    eyebrow: "职业规划报告示例",
    title: "市场营销专员发展路径",
    summary: "系统将能力分析、匹配结果、路径建议和行动计划汇总成可编辑报告，便于你持续更新和导出。",
    highlights: ["主路径 3 阶段", "短中期任务齐全", "支持 PDF / DOCX"],
    sections: [
      {
        title: "岗位晋升路径",
        items: ["市场营销专员", "市场经理/品牌经理", "市场总监/CMO"]
      },
      {
        title: "行动计划",
        items: ["2 周内补齐数据分析与营销工具技能", "4 周内完成一份完整的市场推广方案", "每月复盘一次职业目标与进展"]
      }
    ]
  },
  "ui-designer-sample": {
    eyebrow: "我的能力分析",
    title: "UI设计师方向的能力全貌",
    summary: "涵盖视觉设计、交互原型、创意思维和工具掌握度的综合评估，帮助你了解自己在设计领域的准备情况。",
    highlights: ["技能覆盖 7 项", "竞争力评分 82", "证据链 5 条"],
    sections: [
      {
        title: "已识别优势",
        items: ["Figma/Sketch 熟练使用，有完整作品集", "色彩与排版基础扎实", "有 2 段设计实习经历", "用户思维与创意表达突出"]
      },
      {
        title: "建议补充",
        items: ["补充动效设计与原型工具经验（如 Principle）", "增加 B 端企业级产品界面设计案例", "完善设计规范文档能力"]
      }
    ]
  },
  "hr-sample": {
    eyebrow: "我和这个岗位的匹配度",
    title: "我和人力资源专员岗位的匹配度",
    summary: "从沟通能力、组织协调、招聘培训等核心能力方面完成对比分析，明确优势与提升方向。",
    highlights: ["匹配度 91.5", "能力方面全达标", "差距项 1 个"],
    sections: [
      {
        title: "契合点",
        items: ["沟通协调能力突出，有学生会组织经验", "招聘与培训流程了解透彻", "亲和力和执行力强"]
      },
      {
        title: "差距项",
        items: ["建议补充人力资源相关的实习经历", "可学习劳动法和薪酬管理基础知识"]
      }
    ]
  },
  "finance-sample": {
    eyebrow: "职业规划报告示例",
    title: "金融分析师发展路径",
    summary: "基于金融行业需求和你的能力结构，规划从初级分析师到投资经理的完整成长路径。",
    highlights: ["主路径 3 阶段", "短中期计划", "支持 PDF / DOCX"],
    sections: [
      {
        title: "岗位晋升路径",
        items: ["金融分析师（初级）", "高级金融分析师/投资经理", "投资总监/首席分析师"]
      },
      {
        title: "行动计划",
        items: ["3 个月内通过 CFA 一级考试", "6 个月内完成 2 份行业研究报告", "每月跟踪市场动态并做复盘笔记"]
      }
    ]
  }
};

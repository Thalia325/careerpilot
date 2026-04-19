"""Seed 35 realistic simulated students for teacher dashboard demonstration.

Covers 7 majors, 8+ target jobs, 4 grade levels, varied match scores,
different report statuses, different growth task states, and different
resume completeness levels.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AnalysisRun,
    CareerReport,
    GrowthTask,
    JobProfile,
    MatchDimensionScore,
    MatchResult,
    Student,
    StudentProfile,
    Teacher,
    TeacherStudentLink,
    UploadedFile,
    User,
)
from app.services.auth_service import hash_password

# --- Configuration ---

MAJORS = [
    "软件工程",
    "计算机科学与技术",
    "数据科学与大数据技术",
    "人工智能",
    "信息安全",
    "电子信息工程",
    "通信工程",
    "金融学",
    "会计学",
    "法学",
    "教育学",
    "市场营销",
    "工商管理",
    "机械工程",
    "土木工程",
    "建筑学",
    "电气工程及其自动化",
    "药学",
    "新闻学",
    "人力资源管理",
    "英语",
    "国际经济与贸易",
    "社会工作",
    "体育教育",
    "农学",
    "食品科学与工程",
]

GRADES = ["大一", "大二", "大三", "大四"]

TARGET_JOBS = [
    ("J-FE-001", "前端开发工程师"),
    ("J-BE-001", "后端开发工程师"),
    ("J-FS-001", "全栈工程师"),
    ("J-QA-001", "测试工程师"),
    ("J-DA-001", "数据分析师"),
    ("J-AI-001", "AI算法工程师"),
    ("J-OPS-001", "运维工程师"),
    ("J-PM-001", "产品经理"),
    ("J-FIN-001", "金融分析师"),
    ("J-ACC-001", "财务会计"),
    ("J-LAW-001", "法务专员"),
    ("J-EDU-001", "培训讲师"),
    ("J-MKT-001", "市场营销专员"),
    ("J-SAL-001", "销售代表"),
    ("J-HR-001", "人力资源专员"),
    ("J-ADM-001", "行政专员"),
    ("J-MECH-001", "机械工程师"),
    ("J-CIV-001", "土木工程师"),
    ("J-ARC-001", "建筑设计师"),
    ("J-ELE-001", "电气工程师"),
    ("J-PHA-001", "医药代表"),
    ("J-SPL-001", "供应链专员"),
    ("J-JOU-001", "记者/编辑"),
    ("J-NMD-001", "新媒体运营"),
    ("J-CON-001", "管理咨询顾问"),
]

SCHOOLS = [
    "计算机学院",
    "软件学院",
    "人工智能学院",
    "信息工程学院",
    "电子与通信工程学院",
    "金融学院",
    "商学院",
    "法学院",
    "教育学院",
    "传媒学院",
    "机械工程学院",
    "土木工程学院",
    "建筑与城规学院",
    "电气工程学院",
    "药学院",
    "外国语学院",
    "公共管理学院",
    "体育学院",
    "农学院",
    "化学与材料学院",
]

REPORT_STATUSES = ["draft", "edited", "completed"]

GROWTH_TASK_STATUSES = ["pending", "in_progress", "completed", "overdue"]

# --- Student template data (35 students) ---
# Each entry: (name, major, grade, school, target_job_code, target_job_title,
#              match_score_bucket, has_resume, has_profile, report_status,
#              growth_task_status, completeness)

_STUDENT_TEMPLATES = [
    # --- 软件工程 (8 students) ---
    ("张明轩", "软件工程", "大三", "计算机学院", "J-FE-001", "前端开发工程师", 92, True, True, "completed", "completed", 95),
    ("李思涵", "软件工程", "大三", "计算机学院", "J-BE-001", "后端开发工程师", 87, True, True, "completed", "in_progress", 88),
    ("王浩宇", "软件工程", "大二", "计算机学院", "J-FS-001", "全栈工程师", 78, True, True, "edited", "pending", 75),
    ("赵雨萱", "软件工程", "大四", "软件学院", "J-FE-001", "前端开发工程师", 95, True, True, "completed", "completed", 98),
    ("陈志远", "软件工程", "大三", "计算机学院", "J-QA-001", "测试工程师", 65, True, True, "draft", "pending", 60),
    ("刘佳怡", "软件工程", "大一", "计算机学院", "J-PM-001", "产品经理", 55, True, False, None, None, 30),
    ("周天翔", "软件工程", "大四", "软件学院", "J-BE-001", "后端开发工程师", 83, True, True, "edited", "in_progress", 80),
    ("吴思琪", "软件工程", "大二", "计算机学院", "J-FE-001", "前端开发工程师", 72, True, True, "draft", "overdue", 68),
    # --- 计算机科学与技术 (7 students) ---
    ("孙浩然", "计算机科学与技术", "大三", "计算机学院", "J-AI-001", "AI算法工程师", 88, True, True, "completed", "completed", 90),
    ("黄诗涵", "计算机科学与技术", "大四", "计算机学院", "J-BE-001", "后端开发工程师", 91, True, True, "completed", "completed", 93),
    ("林宇轩", "计算机科学与技术", "大二", "计算机学院", "J-DA-001", "数据分析师", 74, True, True, "edited", "pending", 70),
    ("杨雨桐", "计算机科学与技术", "大三", "信息工程学院", "J-OPS-001", "运维工程师", 68, True, True, "draft", "in_progress", 65),
    ("郑凯文", "计算机科学与技术", "大一", "计算机学院", "J-FE-001", "前端开发工程师", 45, True, False, None, None, 25),
    ("马晨曦", "计算机科学与技术", "大四", "计算机学院", "J-FS-001", "全栈工程师", 85, True, True, "completed", "in_progress", 82),
    ("徐梦瑶", "计算机科学与技术", "大三", "计算机学院", "J-BE-001", "后端开发工程师", 79, True, True, "edited", "pending", 76),
    # --- 数据科学与大数据技术 (5 students) ---
    ("胡嘉豪", "数据科学与大数据技术", "大三", "人工智能学院", "J-DA-001", "数据分析师", 90, True, True, "completed", "completed", 92),
    ("朱晓燕", "数据科学与大数据技术", "大四", "人工智能学院", "J-AI-001", "AI算法工程师", 86, True, True, "completed", "in_progress", 85),
    ("何俊逸", "数据科学与大数据技术", "大二", "人工智能学院", "J-DA-001", "数据分析师", 70, True, True, "draft", "pending", 65),
    ("罗雅琪", "数据科学与大数据技术", "大三", "人工智能学院", "J-BE-001", "后端开发工程师", 76, True, True, "edited", "overdue", 72),
    ("谢文博", "数据科学与大数据技术", "大一", "人工智能学院", "J-AI-001", "AI算法工程师", 52, True, False, None, None, 35),
    # --- 人工智能 (5 students) ---
    ("韩志豪", "人工智能", "大三", "人工智能学院", "J-AI-001", "AI算法工程师", 93, True, True, "completed", "completed", 95),
    ("唐诗雨", "人工智能", "大四", "人工智能学院", "J-DA-001", "数据分析师", 84, True, True, "completed", "completed", 82),
    ("冯宇翔", "人工智能", "大二", "人工智能学院", "J-FE-001", "前端开发工程师", 62, True, True, "draft", "pending", 58),
    ("曹思远", "人工智能", "大三", "人工智能学院", "J-AI-001", "AI算法工程师", 81, True, True, "edited", "in_progress", 78),
    ("邓欣怡", "人工智能", "大一", "人工智能学院", "J-PM-001", "产品经理", 48, False, False, None, None, 15),
    # --- 信息安全 (4 students) ---
    ("彭浩宇", "信息安全", "大三", "信息工程学院", "J-OPS-001", "运维工程师", 82, True, True, "completed", "in_progress", 80),
    ("蒋雨涵", "信息安全", "大四", "信息工程学院", "J-BE-001", "后端开发工程师", 77, True, True, "edited", "completed", 75),
    ("蔡文轩", "信息安全", "大二", "信息工程学院", "J-QA-001", "测试工程师", 66, True, True, "draft", "pending", 62),
    ("潘思琪", "信息安全", "大三", "信息工程学院", "J-OPS-001", "运维工程师", 71, True, True, "draft", "overdue", 68),
    # --- 电子信息工程 (3 students) ---
    ("余天赐", "电子信息工程", "大四", "电子与通信工程学院", "J-DA-001", "数据分析师", 75, True, True, "edited", "pending", 72),
    ("叶梦洁", "电子信息工程", "大三", "电子与通信工程学院", "J-FE-001", "前端开发工程师", 69, True, True, "draft", "in_progress", 65),
    ("钟浩然", "电子信息工程", "大二", "电子与通信工程学院", "J-BE-001", "后端开发工程师", 58, True, True, "draft", "pending", 40),
    # --- 通信工程 (3 students) ---
    ("段志鹏", "通信工程", "大四", "电子与通信工程学院", "J-OPS-001", "运维工程师", 80, True, True, "completed", "completed", 78),
    ("贺雅婷", "通信工程", "大三", "电子与通信工程学院", "J-PM-001", "产品经理", 73, True, True, "edited", "pending", 70),
    ("姜文博", "通信工程", "大二", "电子与通信工程学院", "J-QA-001", "测试工程师", 56, True, True, "draft", "overdue", 38),
    # --- 金融学 (2 students) ---
    ("陆嘉铭", "金融学", "大三", "金融学院", "J-FIN-001", "金融分析师", 88, True, True, "completed", "completed", 90),
    ("唐婉清", "金融学", "大二", "金融学院", "J-ACC-001", "财务会计", 72, True, True, "draft", "pending", 68),
    # --- 会计学 (2 students) ---
    ("孙瑾瑜", "会计学", "大三", "商学院", "J-ACC-001", "财务会计", 85, True, True, "completed", "in_progress", 82),
    ("方子涵", "会计学", "大一", "商学院", "J-FIN-001", "金融分析师", 50, True, False, None, None, 28),
    # --- 法学 (2 students) ---
    ("宋明远", "法学", "大三", "法学院", "J-LAW-001", "法务专员", 76, True, True, "edited", "pending", 74),
    ("程雨薇", "法学", "大四", "法学院", "J-LAW-001", "法务专员", 83, True, True, "completed", "completed", 80),
    # --- 教育学 (2 students) ---
    ("沈文博", "教育学", "大三", "教育学院", "J-EDU-001", "培训讲师", 78, True, True, "edited", "in_progress", 76),
    ("顾思琪", "教育学", "大二", "教育学院", "J-EDU-001", "培训讲师", 65, True, True, "draft", "pending", 60),
    # --- 市场营销 (2 students) ---
    ("侯宇翔", "市场营销", "大三", "商学院", "J-MKT-001", "市场营销专员", 82, True, True, "completed", "completed", 80),
    ("龚梦瑶", "市场营销", "大二", "商学院", "J-NMD-001", "新媒体运营", 70, True, True, "draft", "overdue", 66),
    # --- 工商管理 (1 student) ---
    ("田浩然", "工商管理", "大四", "商学院", "J-HR-001", "人力资源专员", 79, True, True, "completed", "in_progress", 76),
    # --- 机械工程 (2 students) ---
    ("崔志强", "机械工程", "大三", "机械工程学院", "J-MECH-001", "机械工程师", 84, True, True, "completed", "completed", 82),
    ("贾思涵", "机械工程", "大二", "机械工程学院", "J-MECH-001", "机械工程师", 68, True, True, "draft", "pending", 64),
    # --- 土木工程 (2 students) ---
    ("邹铭轩", "土木工程", "大三", "土木工程学院", "J-CIV-001", "土木工程师", 80, True, True, "edited", "in_progress", 78),
    ("尹雨桐", "土木工程", "大四", "土木工程学院", "J-CIV-001", "土木工程师", 86, True, True, "completed", "completed", 84),
    # --- 建筑学 (1 student) ---
    ("范晓阳", "建筑学", "大三", "建筑与城规学院", "J-ARC-001", "建筑设计师", 77, True, True, "edited", "pending", 74),
    # --- 电气工程 (1 student) ---
    ("熊伟杰", "电气工程及其自动化", "大三", "电气工程学院", "J-ELE-001", "电气工程师", 81, True, True, "completed", "completed", 78),
    # --- 药学 (2 students) ---
    ("石静雯", "药学", "大三", "药学院", "J-PHA-001", "医药代表", 75, True, True, "edited", "in_progress", 72),
    ("潘子豪", "药学", "大四", "药学院", "J-PHA-001", "医药代表", 82, True, True, "completed", "completed", 80),
    # --- 新闻学 (2 students) ---
    ("高晨曦", "新闻学", "大三", "传媒学院", "J-JOU-001", "记者/编辑", 73, True, True, "draft", "pending", 70),
    ("柳诗涵", "新闻学", "大二", "传媒学院", "J-NMD-001", "新媒体运营", 66, True, True, "draft", "overdue", 62),
    # --- 人力资源管理 (1 student) ---
    ("郝文轩", "人力资源管理", "大三", "公共管理学院", "J-HR-001", "人力资源专员", 78, True, True, "edited", "pending", 76),
    # --- 英语 (1 student) ---
    ("乔雅琪", "英语", "大三", "外国语学院", "J-TRL-001", "翻译/本地化", 74, True, True, "draft", "pending", 70),
    # --- 国际经济与贸易 (1 student) ---
    ("于浩宇", "国际经济与贸易", "大三", "商学院", "J-TRD-001", "外贸专员", 71, True, True, "edited", "pending", 68),
    # --- 社会工作 (1 student) ---
    ("秦思远", "社会工作", "大三", "公共管理学院", "J-PSY-001", "心理咨询师", 69, True, True, "draft", "in_progress", 66),
    # --- 体育教育 (1 student) ---
    ("武天翔", "体育教育", "大三", "体育学院", "J-FIT-001", "健身教练", 77, True, True, "edited", "completed", 74),
    # --- 农学 (1 student) ---
    ("袁秋实", "农学", "大三", "农学院", "J-AGR-001", "农业技术员", 64, True, True, "draft", "pending", 60),
    # --- 食品科学与工程 (1 student) ---
    ("夏雨萱", "食品科学与工程", "大三", "化学与材料学院", "J-FDQ-001", "食品安全/质量管理", 72, True, True, "edited", "in_progress", 70),
]

# Skills pool per major direction
_SKILLS_POOL = {
    "J-FE-001": ["JavaScript", "TypeScript", "React", "Vue.js", "HTML", "CSS", "Webpack", "Next.js", "Node.js", "小程序开发"],
    "J-BE-001": ["Python", "Java", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "Redis", "Docker", "Linux", "系统设计"],
    "J-FS-001": ["JavaScript", "TypeScript", "React", "Node.js", "Python", "PostgreSQL", "Docker", "Git", "MongoDB", "REST API"],
    "J-QA-001": ["测试用例设计", "Selenium", "Postman", "SQL", "自动化测试", "缺陷管理", "性能测试", "Python"],
    "J-DA-001": ["Python", "SQL", "Pandas", "NumPy", "数据可视化", "Excel", "统计学", "机器学习基础", "Tableau"],
    "J-AI-001": ["Python", "PyTorch", "TensorFlow", "深度学习", "机器学习", "NLP", "计算机视觉", "数学建模", "CUDA"],
    "J-OPS-001": ["Linux", "Docker", "Kubernetes", "Shell", "CI/CD", "Nginx", "监控运维", "Ansible", "Python"],
    "J-PM-001": ["Axure", "需求分析", "用户研究", "数据分析", "项目管理", "SQL", "Figma", "原型设计"],
    "J-FIN-001": ["财务建模", "行业研究", "Excel", "Python", "估值分析", "Wind", "数据可视化"],
    "J-ACC-001": ["会计准则", "财务报表", "税务申报", "ERP系统", "成本核算", "Excel", "财务分析"],
    "J-LAW-001": ["合同审查", "法律法规", "合规管理", "法律文书", "风险评估", "劳动法", "知识产权"],
    "J-EDU-001": ["课程设计", "教学方法", "PPT制作", "学员评估", "互动教学", "教育心理学", "在线教学工具"],
    "J-MKT-001": ["市场调研", "营销策划", "品牌推广", "数据分析", "活动执行", "竞品分析", "社交媒体营销"],
    "J-SAL-001": ["客户开发", "销售谈判", "CRM系统", "客户关系管理", "市场分析", "方案撰写", "商务礼仪"],
    "J-HR-001": ["招聘管理", "绩效考核", "员工关系", "培训组织", "HR系统", "劳动法规", "薪酬福利"],
    "J-ADM-001": ["办公软件", "会议管理", "档案管理", "采购管理", "接待礼仪", "流程优化", "跨部门协调"],
    "J-MECH-001": ["AutoCAD", "SolidWorks", "机械设计", "材料力学", "工艺优化", "GD&T", "有限元分析"],
    "J-CIV-001": ["AutoCAD", "结构设计", "施工管理", "工程测量", "BIM", "质量验收", "工程概预算"],
    "J-ARC-001": ["AutoCAD", "SketchUp", "Revit", "建筑规范", "方案设计", "施工图", "效果图渲染"],
    "J-ELE-001": ["电气设计", "PLC编程", "电路分析", "AutoCAD Electrical", "控制系统", "电力电子", "设备调试"],
    "J-PHA-001": ["医学知识", "学术推广", "客户管理", "演讲能力", "CRM系统", "市场分析", "合规意识"],
    "J-SPL-001": ["采购管理", "库存管理", "物流协调", "供应商评估", "ERP系统", "成本分析", "数据统计"],
    "J-JOU-001": ["新闻采写", "内容编辑", "选题策划", "舆情分析", "摄影摄像", "排版设计", "新媒体发布"],
    "J-NMD-001": ["内容策划", "短视频制作", "数据分析", "用户增长", "平台运营", "文案写作", "热点追踪"],
    "J-TRL-001": ["笔译", "口译", "CAT工具", "术语管理", "跨文化沟通", "本地化工程", "质量审校"],
    "J-TRD-001": ["国际贸易", "外贸单证", "报关流程", "英语商务邮件", "跨境电商", "信用证", "市场开拓"],
    "J-PSY-001": ["心理咨询技术", "心理评估", "危机干预", "认知行为疗法", "倾听技巧", "案例分析", "伦理规范"],
    "J-FIT-001": ["运动解剖学", "训练计划设计", "营养指导", "体测评估", "私教课程", "团体课教学", "急救知识"],
    "J-AGR-001": ["作物栽培", "病虫害防治", "土壤分析", "农业机械", "数据记录", "农药使用", "田间试验"],
    "J-FDQ-001": ["食品安全法规", "HACCP", "质量检验", "ISO22000", "实验室管理", "供应商审核", "数据分析"],
    "J-CON-001": ["战略分析", "数据分析", "PPT制作", "访谈技巧", "行业研究", "项目管理", "商业模型"],
}

_CERTIFICATES_POOL = [
    "CET-4", "CET-6", "软件设计师", "计算机二级",
    "前端开发专项证书", "软件测试工程师", "AWS云从业者认证",
    "PMP项目管理", "数据库系统工程师", "网络工程师",
    "华为HCIA", "阿里云ACP", "微软Azure基础认证",
    "CPA注册会计师", "CFA特许金融分析师", "法律职业资格证", "教师资格证",
    "市场营销师", "人力资源管理师", "机械工程师", "二级建造师",
    "注册建筑师", "电气工程师", "执业药师", "CATTI翻译资格",
    "报关员", "导游证", "营养师", "心理咨询师",
    "社会工作者", "健身教练国家职业资格", "农艺师", "食品安全管理员",
    "PMP项目管理", "能源管理师",
]

_PROJECT_TEMPLATES = {
    "J-FE-001": [
        "基于React的企业级后台管理系统开发",
        "校园二手交易平台前端设计与实现",
        "在线教育平台小程序开发",
        "个人技术博客系统搭建",
        "电商首页性能优化实践",
    ],
    "J-BE-001": [
        "基于FastAPI的RESTful API服务设计与开发",
        "高并发秒杀系统设计与实现",
        "微服务架构下用户中心系统开发",
        "校园论坛后端系统重构",
        "分布式任务调度平台开发",
    ],
    "J-FS-001": [
        "全栈在线协作白板系统开发",
        "基于Next.js的全栈博客平台",
        "实时聊天应用前后端开发",
        "校园选课系统全栈开发",
    ],
    "J-QA-001": [
        "自动化测试框架搭建与实践",
        "电商系统接口测试与性能测试",
        "移动端App兼容性测试方案",
    ],
    "J-DA-001": [
        "用户行为数据分析平台搭建",
        "基于Pandas的销售数据清洗与分析",
        "A/B测试数据分析与可视化",
        "社交媒体舆情分析系统",
    ],
    "J-AI-001": [
        "基于BERT的中文情感分析模型",
        "目标检测模型训练与部署",
        "推荐系统算法设计与优化",
        "基于GPT的智能问答系统开发",
    ],
    "J-OPS-001": [
        "基于Docker的容器化部署方案",
        "CI/CD流水线搭建与优化",
        "基于Prometheus的监控告警系统",
    ],
    "J-PM-001": [
        "校园外卖平台产品需求文档编写",
        "在线教育产品竞品分析报告",
        "社交App用户调研与需求分析",
    ],
    "J-FIN-001": ["上市公司财务报表分析与估值建模", "行业研究报告撰写实践", "基于Python的量化投资策略回测", "企业并购案例分析"],
    "J-ACC-001": ["企业全套账务处理实践", "财务报表编制与分析", "税务申报全流程实操", "ERP系统财务模块实施"],
    "J-LAW-001": ["企业合同审查实务与风险点梳理", "劳动争议案例分析", "企业合规体系建设方案", "知识产权保护策略研究"],
    "J-EDU-001": ["在线课程体系设计与开发", "企业培训方案设计与实施", "教学效果评估体系搭建", "微课视频制作实践"],
    "J-MKT-001": ["品牌营销全案策划", "社交媒体运营方案设计", "市场调研报告撰写", "新品上市推广方案"],
    "J-SAL-001": ["B2B客户开发流程设计", "销售漏斗管理与优化", "客户关系维护方案", "销售数据分析与复盘"],
    "J-HR-001": ["校园招聘全流程策划", "员工培训体系搭建", "绩效考核方案设计", "企业文化建设方案"],
    "J-ADM-001": ["企业办公流程优化方案", "会议管理体系搭建", "行政成本分析与控制", "企业档案数字化管理"],
    "J-MECH-001": ["基于SolidWorks的减速器设计与仿真", "自动化产线机械结构设计", "有限元分析在零件优化中的应用"],
    "J-CIV-001": ["多层住宅结构设计实践", "施工组织设计方案编制", "BIM建模与工程量计算", "工程质量检测与评估"],
    "J-ARC-001": ["社区活动中心方案设计", "住宅楼施工图绘制", "城市更新概念方案", "建筑效果图制作"],
    "J-ELE-001": ["工厂配电系统设计", "PLC自动化控制程序编写", "电气设备选型与调试", "新能源微电网方案设计"],
    "J-PHA-001": ["药品学术推广方案设计", "竞品分析与市场策略", "客户拜访路线规划实践", "医药行业政策研究报告"],
    "J-SPL-001": ["供应商评估体系搭建", "采购成本分析与优化", "库存管理优化方案", "物流配送路径规划"],
    "J-JOU-001": ["深度新闻报道采写实践", "新媒体内容策划与发布", "舆情监测报告撰写", "短视频新闻制作"],
    "J-NMD-001": ["短视频账号运营实践", "社交媒体增长方案设计", "内容策划与数据分析", "品牌传播全案策划"],
    "J-TRL-001": ["技术文档翻译实践", "软件本地化项目实操", "商务口译模拟训练", "翻译质量控制流程设计"],
    "J-TRD-001": ["出口贸易全流程实操", "跨境电商店铺运营", "国际市场分析报告", "外贸单证制作实践"],
    "J-PSY-001": ["心理咨询案例分析", "心理健康讲座设计", "团体辅导方案策划", "心理测评工具应用"],
    "J-FIT-001": ["个性化训练方案设计", "体测评估报告撰写", "健身课程编排实践", "运动营养方案制定"],
    "J-AGR-001": ["作物种植方案设计", "病虫害防治方案制定", "土壤检测与分析", "智慧农业系统调研"],
    "J-FDQ-001": ["食品安全管理体系搭建", "食品检测实验方案", "HACCP计划制定", "食品质量追溯系统设计"],
    "J-CON-001": ["行业研究报告撰写", "企业战略分析方案", "管理咨询模拟项目", "数据驱动决策分析"],
}

_INTERNSHIP_COMPANIES = [
    "字节跳动", "腾讯", "阿里巴巴", "美团", "京东",
    "百度", "华为", "小米", "网易", "滴滴",
    "快手", "拼多多", "OPPO", "vivo", "中兴通讯",
    "科大讯飞", "商汤科技", "ThoughtWorks", "SAP", "IBM",
    "创业公司", "校内实验室", "导师课题组", None,
    "四大会计师事务所", "中国银行", "工商银行", "中信证券",
    "中建集团", "中车集团", "三一重工", "华为终端",
    "复星医药", "恒瑞医药", "新东方", "好未来",
    "蓝色光标", "奥美广告", "万豪酒店", "万科地产",
    "中国石油", "国家电网", "中国中化",
]


def _random_datetime(days_ago_min: int, days_ago_max: int) -> datetime:
    """Generate a random datetime within the given range of days ago."""
    now = datetime.now(timezone.utc)
    days_ago = random.randint(days_ago_min, days_ago_max)
    hours_offset = random.randint(0, 23)
    minutes_offset = random.randint(0, 59)
    return now - timedelta(days=days_ago, hours=hours_offset, minutes=minutes_offset)


def seed_demo_students(db: Session) -> int:
    """Create 35 simulated students with full data chain.

    Idempotent: skips if demo students already exist (checks for user
    'demo_student_001').
    Returns the number of students created.
    """
    if db.scalar(select(User).where(User.username == "demo_student_001")):
        return 0

    # Pre-load or create job profiles for FK references
    job_profiles: dict[str, JobProfile] = {}
    for jp in db.scalars(select(JobProfile)).all():
        job_profiles[jp.job_code] = jp

    # Ensure a JobProfile exists for every job_code used in templates
    used_job_codes = {t[4] for t in _STUDENT_TEMPLATES}  # job_code is index 4
    for jcode, jtitle in TARGET_JOBS:
        if jcode in used_job_codes and jcode not in job_profiles:
            jp = JobProfile(
                job_code=jcode,
                title=jtitle,
                summary=f"{jtitle}岗位要求与能力模型",
                skill_requirements=_SKILLS_POOL.get(jcode, [])[:5],
                certificate_requirements=[],
                dimension_weights={
                    "basic_requirements": 0.15,
                    "professional_skills": 0.45,
                    "professional_literacy": 0.2,
                    "development_potential": 0.2,
                },
            )
            db.add(jp)
            db.flush()
            job_profiles[jcode] = jp

    created_count = 0
    now = datetime.now(timezone.utc)

    for idx, (
        name, major, grade, school, job_code, job_title,
        score_bucket, has_resume, has_profile, report_status,
        growth_task_status, completeness,
    ) in enumerate(_STUDENT_TEMPLATES, start=1):
        # --- User ---
        seq = f"{idx:03d}"
        username = f"demo_student_{seq}"
        user = User(
            username=username,
            password_hash=hash_password("demo123"),
            role="student",
            full_name=name,
            email=f"{username}@careerpilot.local",
        )
        db.add(user)
        db.flush()

        # --- Student ---
        student = Student(
            user_id=user.id,
            major=major,
            grade=grade,
            career_goal=job_title,
            target_job_code=job_code,
            target_job_title=job_title,
            learning_preferences={"preferred_roles": [job_title]},
        )
        db.add(student)
        db.flush()

        # --- UploadedFile (resume) ---
        uploaded_file_id = None
        if has_resume:
            uploaded_at = _random_datetime(30, 90)
            uf = UploadedFile(
                owner_id=user.id,
                file_type="resume",
                file_name=f"resume_{name}.pdf",
                content_type="application/pdf",
                storage_key=f"demos/{username}/resume.pdf",
                url=f"/uploads/demos/{username}/resume.pdf",
                meta_json={"ocr": {"status": "completed"}},
            )
            # Override created_at to simulate realistic timeline
            uf.created_at = uploaded_at
            uf.updated_at = uploaded_at
            db.add(uf)
            db.flush()
            uploaded_file_id = uf.id

        # --- StudentProfile ---
        profile_id = None
        if has_profile:
            skills = _SKILLS_POOL.get(job_code, _SKILLS_POOL["J-FE-001"])
            num_skills = max(2, int(len(skills) * (completeness / 100)))
            selected_skills = random.sample(skills, num_skills)
            num_certs = random.randint(0, 3)
            selected_certs = random.sample(_CERTIFICATES_POOL, min(num_certs, len(_CERTIFICATES_POOL)))
            projects = _PROJECT_TEMPLATES.get(job_code, _PROJECT_TEMPLATES["J-FE-001"])
            num_projects = max(0, int(len(projects) * (completeness / 120)))
            selected_projects = random.sample(projects, min(num_projects, len(projects)))

            internship_company = random.choice(_INTERNSHIP_COMPANIES)
            internships = [f"{internship_company} - {job_title}实习生"] if internship_company else []

            profile = StudentProfile(
                student_id=student.id,
                source_summary=f"{name}，{major}专业{grade}学生，目标岗位：{job_title}",
                skills_json=selected_skills,
                certificates_json=selected_certs,
                projects_json=selected_projects,
                internships_json=internships,
                capability_scores={
                    "innovation": round(score_bucket * random.uniform(0.85, 1.05), 1),
                    "learning": round(score_bucket * random.uniform(0.88, 1.08), 1),
                    "resilience": round(score_bucket * random.uniform(0.82, 1.02), 1),
                    "communication": round(score_bucket * random.uniform(0.80, 1.0), 1),
                    "internship": round(score_bucket * random.uniform(0.78, 1.05), 1),
                },
                completeness_score=float(completeness),
                competitiveness_score=round(score_bucket * 0.95, 1),
                evidence_summary={},
            )
            profile.created_at = _random_datetime(20, 85)
            profile.updated_at = profile.created_at
            db.add(profile)
            db.flush()
            profile_id = profile.id

        # --- AnalysisRun ---
        analysis_run = None
        if has_profile:
            analysis_run = AnalysisRun(
                student_id=student.id,
                status="completed",
                current_step="reported" if report_status else "matched",
                uploaded_file_ids=[uploaded_file_id] if uploaded_file_id else [],
                resume_file_id=uploaded_file_id,
                target_job_code=job_code,
            )
            analysis_run.created_at = _random_datetime(15, 80)
            analysis_run.updated_at = analysis_run.created_at
            db.add(analysis_run)
            db.flush()

        # --- MatchResult + MatchDimensionScore ---
        match_result_id = None
        if has_profile and job_code in job_profiles:
            jp = job_profiles[job_code]
            total_score = float(score_bucket)

            # Generate realistic dimension scores
            dim_scores = {
                "基础要求": round(total_score * random.uniform(0.92, 1.08), 1),
                "职业技能": round(total_score * random.uniform(0.88, 1.06), 1),
                "职业素养": round(total_score * random.uniform(0.85, 1.05), 1),
                "发展潜力": round(total_score * random.uniform(0.82, 1.04), 1),
            }
            # Clamp to 0-100
            dim_scores = {k: max(0.0, min(100.0, v)) for k, v in dim_scores.items()}

            strengths = []
            if total_score >= 70:
                skills = _SKILLS_POOL.get(job_code, [])
                strengths = random.sample(skills[:5], min(3, len(skills[:5])))
                strengths = [f"具备{s}技能基础" for s in strengths]

            gaps = []
            if total_score < 85:
                gap_skills = _SKILLS_POOL.get(job_code, [])
                num_gaps = min(3, max(1, int((100 - total_score) / 15)))
                gaps = random.sample(gap_skills[-4:], min(num_gaps, len(gap_skills[-4:])))
                gaps = [{"item": g, "detail": f"建议系统学习{g}相关知识"} for g in gaps]

            suggestions = []
            if total_score >= 85:
                suggestions = ["关注面试技巧提升", "参与开源项目积累经验"]
            elif total_score >= 70:
                suggestions = ["补强核心技能短板", "争取相关实习机会"]
            elif total_score >= 60:
                suggestions = ["系统性学习目标岗位技能", "积累项目实践经验"]
            else:
                suggestions = ["重新评估职业目标", "制定长期学习计划"]

            match_result = MatchResult(
                student_profile_id=profile_id,
                job_profile_id=jp.id,
                total_score=total_score,
                summary=f"{name}与{job_title}岗位的综合匹配度为{total_score}分。",
                strengths_json=strengths,
                gaps_json=gaps,
                suggestions_json=suggestions,
                student_id=student.id,
                target_job_code=job_code,
            )
            match_result.created_at = _random_datetime(10, 75)
            match_result.updated_at = match_result.created_at
            db.add(match_result)
            db.flush()
            match_result_id = match_result.id

            # Create dimension scores
            weights = jp.dimension_weights or {
                "basic_requirements": 0.15,
                "professional_skills": 0.45,
                "professional_literacy": 0.2,
                "development_potential": 0.2,
            }
            dim_weight_map = {
                "基础要求": ("basic_requirements", weights.get("basic_requirements", 0.15)),
                "职业技能": ("professional_skills", weights.get("professional_skills", 0.45)),
                "职业素养": ("professional_literacy", weights.get("professional_literacy", 0.2)),
                "发展潜力": ("development_potential", weights.get("development_potential", 0.2)),
            }
            for dim_name, score in dim_scores.items():
                dim_key, weight = dim_weight_map[dim_name]
                dim_score = MatchDimensionScore(
                    match_result_id=match_result.id,
                    dimension=dim_key,
                    score=score,
                    weight=weight,
                    reasoning=f"{dim_name}维度得分{score}分。",
                    evidence_json={},
                )
                dim_score.created_at = match_result.created_at
                dim_score.updated_at = match_result.created_at
                db.add(dim_score)

            # Link analysis run
            if analysis_run:
                analysis_run.match_result_id = match_result_id

        # --- CareerReport ---
        report = None
        if has_profile and report_status:
            report = CareerReport(
                student_id=student.id,
                target_job_code=job_code,
                status=report_status,
                content_json={
                    "student_summary": f"{name}，{school}{major}专业{grade}在读，目标岗位为{job_title}。",
                    "capability_profile": {
                        "skills": _SKILLS_POOL.get(job_code, [])[:3],
                        "completeness": completeness,
                    },
                    "matching_analysis": {
                        "total_score": score_bucket,
                        "target_job": job_title,
                    },
                },
                markdown_content=f"# {name}的职业规划报告\n\n## 学生基本情况\n{name}，{school}{major}专业{grade}在读。\n\n## 目标岗位\n{job_title}\n\n## 匹配分析\n综合匹配度：{score_bucket}分。\n\n## 差距分析\n建议补强核心技能。\n\n## 行动计划\n1. 系统学习目标岗位所需技能\n2. 参与相关项目实践\n3. 积累实习经验\n\n## 教师建议\n（待教师填写）",
            )
            report.created_at = _random_datetime(5, 60)
            report.updated_at = report.created_at
            db.add(report)
            db.flush()

            # Link analysis run
            if analysis_run:
                analysis_run.report_id = report.id
                analysis_run.current_step = "reported"

        # --- GrowthTask ---
        if has_profile and growth_task_status:
            task_titles = {
                "J-FE-001": ["学习React高级模式", "完成3个前端项目", "参加前端技术分享会"],
                "J-BE-001": ["学习系统设计基础", "完成数据库优化实践", "参与后端项目开发"],
                "J-FS-001": ["学习全栈开发框架", "完成一个完整项目", "部署应用到云平台"],
                "J-QA-001": ["学习自动化测试工具", "编写100个测试用例", "完成性能测试报告"],
                "J-DA-001": ["学习数据分析工具", "完成一个数据分析项目", "参加数据竞赛"],
                "J-AI-001": ["完成深度学习课程", "训练一个AI模型", "参加AI竞赛"],
                "J-OPS-001": ["学习Docker和K8s", "搭建CI/CD流水线", "完成运维监控部署"],
                "J-PM-001": ["学习产品设计方法", "完成一份PRD文档", "参加用户调研实践"],
                "J-FIN-001": ["完成财务建模课程", "撰写一份行业研究报告", "考取CFA一级"],
                "J-ACC-001": ["完成会计实务课程", "编制一套完整财务报表", "备考CPA"],
                "J-LAW-001": ["学习合同法实务", "完成法律文书写作训练", "参加模拟法庭"],
                "J-EDU-001": ["设计一门完整课程", "完成教学实践录像", "学习教育心理学"],
                "J-MKT-001": ["完成营销策划全案", "学习数字营销工具", "参加营销竞赛"],
                "J-SAL-001": ["学习销售谈判技巧", "完成客户开发实践", "参加销售培训"],
                "J-HR-001": ["学习劳动法规", "完成招聘流程实操", "参加HR培训课程"],
                "J-ADM-001": ["学习办公管理流程", "完成活动策划实践", "提升办公软件技能"],
                "J-MECH-001": ["完成SolidWorks高级建模", "参与机械设计竞赛", "完成有限元分析实践"],
                "J-CIV-001": ["完成结构设计课程", "学习BIM建模工具", "参与工程测量实践"],
                "J-ARC-001": ["完成建筑方案设计", "学习Revit建模", "参加建筑设计竞赛"],
                "J-ELE-001": ["完成PLC编程实训", "学习电气设计规范", "参与自动化项目"],
                "J-PHA-001": ["学习医药行业知识", "完成学术推广演练", "考取相关资格证书"],
                "J-SPL-001": ["学习供应链管理方法", "完成采购流程实操", "学习ERP系统操作"],
                "J-JOU-001": ["完成新闻采写训练", "学习新媒体运营", "参加媒体实习"],
                "J-NMD-001": ["完成内容策划实践", "学习短视频制作", "学习数据分析工具"],
                "J-TRL-001": ["完成翻译实践项目", "学习CAT工具操作", "参加翻译竞赛"],
                "J-TRD-001": ["学习外贸流程操作", "完成跨境电商实操", "学习贸易法规"],
                "J-PSY-001": ["完成心理咨询培训", "参与心理援助实践", "学习心理评估工具"],
                "J-FIT-001": ["完成健身教练培训", "学习运动营养知识", "参加体能训练实践"],
                "J-AGR-001": ["完成作物栽培实践", "学习病虫害防治技术", "参与农业调研"],
                "J-FDQ-001": ["学习食品安全法规", "完成质量检测实训", "学习HACCP体系"],
                "J-CON-001": ["完成行业研究分析", "学习咨询方法论", "参加案例竞赛"],
            }
            titles = task_titles.get(job_code, ["完成技能提升计划", "参加实践活动"])
            phases = ["短期", "中期"]
            for i, title in enumerate(titles):
                deadline = now + timedelta(days=random.randint(7, 60))
                task = GrowthTask(
                    student_id=student.id,
                    report_id=report.id if report else None,
                    title=title,
                    phase=phases[i] if i < len(phases) else "中期",
                    deadline=deadline,
                    metric="完成度100%",
                    status=growth_task_status if i == 0 else random.choice(GROWTH_TASK_STATUSES),
                )
                task.created_at = _random_datetime(3, 50)
                task.updated_at = task.created_at
                db.add(task)

        created_count += 1

    # Ensure teacher_demo has a Teacher record and bindings to all demo students
    teacher_user = db.scalar(select(User).where(User.username == "teacher_demo"))
    if teacher_user:
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        if not teacher:
            teacher = Teacher(user_id=teacher_user.id)
            db.add(teacher)
            db.flush()

        # Bind all demo students to this teacher
        demo_student_ids = db.scalars(
            select(Student.id).where(
                Student.user_id.in_(
                    select(User.id).where(User.username.like("demo_student_%"))
                )
            )
        ).all()
        for sid in demo_student_ids:
            existing = db.scalar(
                select(TeacherStudentLink).where(
                    TeacherStudentLink.teacher_id == teacher.id,
                    TeacherStudentLink.student_id == sid,
                )
            )
            if not existing:
                db.add(TeacherStudentLink(
                    teacher_id=teacher.id,
                    student_id=sid,
                    is_primary=True,
                    source="manual",
                    status="active",
                ))

    db.commit()
    return created_count

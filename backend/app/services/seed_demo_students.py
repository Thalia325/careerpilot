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
]

SCHOOLS = [
    "计算机学院",
    "软件学院",
    "人工智能学院",
    "信息工程学院",
    "电子与通信工程学院",
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
}

_CERTIFICATES_POOL = [
    "CET-4", "CET-6", "软件设计师", "计算机二级",
    "前端开发专项证书", "软件测试工程师", "AWS云从业者认证",
    "PMP项目管理", "数据库系统工程师", "网络工程师",
    "华为HCIA", "阿里云ACP", "微软Azure基础认证",
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
}

_INTERNSHIP_COMPANIES = [
    "字节跳动", "腾讯", "阿里巴巴", "美团", "京东",
    "百度", "华为", "小米", "网易", "滴滴",
    "快手", "拼多多", "OPPO", "vivo", "中兴通讯",
    "科大讯飞", "商汤科技", "ThoughtWorks", "SAP", "IBM",
    "创业公司", "校内实验室", "导师课题组", None,
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

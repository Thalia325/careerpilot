from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobProfile, Student, StudentProfile
from app.services.matching.matching_service import MatchingService


@dataclass
class InterviewContext:
    student: Student
    student_profile: StudentProfile
    job_profile: JobProfile
    match_result: dict


class MockInterviewService:
    def __init__(self, matching_service: MatchingService) -> None:
        self.matching_service = matching_service

    def _resolve_context(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        profile_version_id: int | None = None,
        analysis_run_id: int | None = None,
    ) -> InterviewContext:
        student = db.get(Student, student_id)
        student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
        if not student or not student_profile:
            raise ValueError("学生画像不存在，请先完成画像生成。")

        job_profile = self.matching_service._ensure_job_profile(db, job_code)
        if not job_profile:
            raise ValueError("目标岗位画像不存在，请先导入岗位并生成岗位画像。")

        match_result = self.matching_service.analyze_match(
            db,
            student_id,
            job_code,
            profile_version_id=profile_version_id,
            analysis_run_id=analysis_run_id,
        )
        return InterviewContext(
            student=student,
            student_profile=student_profile,
            job_profile=job_profile,
            match_result=match_result,
        )

    @staticmethod
    def _readiness_level(score: float) -> str:
        if score >= 85:
            return "较强"
        if score >= 70:
            return "中等"
        return "待提升"

    @staticmethod
    def _build_focus_summary(context: InterviewContext) -> list[str]:
        gap_items = context.match_result.get("gap_items") or []
        strengths = (context.match_result.get("strengths") or [])[:2]
        missing = [item.get("name", "") for item in gap_items[:3] if item.get("name")]
        certificates = (context.job_profile.certificate_requirements or [])[:2]

        summary: list[str] = []
        if strengths:
            summary.append(f"优先突出已具备优势：{'、'.join(strengths)}")
        if missing:
            summary.append(f"重点准备能力短板：{'、'.join(missing)}")
        if certificates:
            summary.append(f"提前说明证书或补证计划：{'、'.join(certificates)}")
        if not summary:
            summary.append("围绕目标岗位核心技能、项目经历和成长计划进行准备。")
        return summary

    @staticmethod
    def _focus_check(label: str, aliases: list[str]) -> dict[str, list[str] | str]:
        return {"label": label, "aliases": aliases}

    def generate_questions(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        profile_version_id: int | None = None,
        analysis_run_id: int | None = None,
    ) -> dict:
        context = self._resolve_context(db, student_id, job_code, profile_version_id, analysis_run_id)
        student_skills = context.student_profile.skills_json or []
        strengths = (context.match_result.get("strengths") or [])[:3]
        gap_items = context.match_result.get("gap_items") or []
        missing = [item["name"] for item in gap_items[:3] if item.get("name")]

        first_skill = strengths[0] if strengths else (student_skills[0] if student_skills else "核心技能")
        first_gap = missing[0] if missing else "目标岗位高频技能"

        questions = [
            {
                "question_id": "q1",
                "category": "自我介绍",
                "question": f"请结合你的专业背景和项目经历，做一段面向“{context.job_profile.title}”岗位的 1 分钟自我介绍。",
                "focus_points": ["专业背景", "项目经历", context.job_profile.title],
                "focus_checks": [
                    self._focus_check("专业背景", ["专业", "方向", "本科", "硕士"]),
                    self._focus_check("项目经历", ["项目", "课题", "实习", "经历"]),
                    self._focus_check(context.job_profile.title, [context.job_profile.title]),
                ],
                "answer_tips": ["先说专业和方向", "再说最贴近岗位的项目", "最后点出为什么适合该岗位"],
            },
            {
                "question_id": "q2",
                "category": "技能深挖",
                "question": f"请举一个你实际使用“{first_skill}”解决问题的例子，说明场景、做法和结果。",
                "focus_points": [first_skill, "问题分析", "结果量化"],
                "focus_checks": [
                    self._focus_check(first_skill, [first_skill]),
                    self._focus_check("问题分析", ["问题", "难点", "挑战", "分析"]),
                    self._focus_check("结果量化", ["提升", "降低", "完成", "%", "倍", "天", "周", "月"]),
                ],
                "answer_tips": ["说明业务场景", "说清技术动作", "尽量量化结果"],
            },
            {
                "question_id": "q3",
                "category": "短板应对",
                "question": f"如果面试官追问你在“{first_gap}”上的经验不足，你会如何回应并展示补足计划？",
                "focus_points": [first_gap, "学习计划", "补足路径"],
                "focus_checks": [
                    self._focus_check(first_gap, [first_gap]),
                    self._focus_check("学习计划", ["学习", "计划", "课程", "训练", "准备"]),
                    self._focus_check("补足路径", ["补齐", "提升", "项目", "实习", "课程"]),
                ],
                "answer_tips": ["不要回避短板", "说明已做过的学习或实践", "给出短期补足计划"],
            },
            {
                "question_id": "q4",
                "category": "综合素养",
                "question": "请分享一次你在项目中与他人协作、沟通分工或处理压力的经历。",
                "focus_points": ["沟通协作", "抗压能力", "复盘改进"],
                "focus_checks": [
                    self._focus_check("沟通协作", ["沟通", "协作", "合作", "团队", "分工"]),
                    self._focus_check("抗压能力", ["压力", "紧急", "截止", "推进", "压缩"]),
                    self._focus_check("复盘改进", ["复盘", "改进", "总结", "优化"]),
                ],
                "answer_tips": ["讲清角色分工", "说明冲突或压力点", "给出结果和反思"],
            },
            {
                "question_id": "q5",
                "category": "职业规划",
                "question": f"如果你拿到“{context.job_profile.title}”岗位的 offer，未来 3 到 6 个月你准备如何提升自己？",
                "focus_points": ["成长目标", "学习路径", "岗位适应"],
                "focus_checks": [
                    self._focus_check("成长目标", ["目标", "成长", "阶段", "规划"]),
                    self._focus_check("学习路径", ["学习", "路径", "课程", "项目"]),
                    self._focus_check("岗位适应", ["适应", "上手", "岗位", "业务"]),
                ],
                "answer_tips": ["把计划拆成阶段", "尽量贴近岗位技能要求", "兼顾项目实践和课程/证书"],
            },
        ]

        score = float(context.match_result.get("total_score") or 0)
        return {
            "student_id": student_id,
            "job_code": context.job_profile.job_code,
            "job_title": context.job_profile.title,
            "readiness_score": score,
            "readiness_level": self._readiness_level(score),
            "focus_summary": self._build_focus_summary(context),
            "questions": questions,
        }

    @staticmethod
    def _matches_focus_point(answer: str, aliases: list[str]) -> bool:
        normalized = answer.lower()
        for alias in aliases:
            if alias.lower() in normalized:
                return True
        return False

    @classmethod
    def _score_answer(cls, answer: str, focus_checks: list[dict[str, list[str] | str]]) -> tuple[float, list[str], list[str]]:
        matched = [
            str(item["label"])
            for item in focus_checks
            if cls._matches_focus_point(answer, [str(alias) for alias in item.get("aliases", [])])
        ]
        labels = [str(item["label"]) for item in focus_checks]
        missing = [label for label in labels if label not in matched]
        length_bonus = min(len(answer.strip()) / 180, 1.0) * 20
        focus_score = (len(matched) / max(len(labels), 1)) * 80
        score = round(min(100.0, focus_score + length_bonus), 2)
        return score, matched, missing

    def evaluate_answers(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        answers: list[dict],
        profile_version_id: int | None = None,
        analysis_run_id: int | None = None,
    ) -> dict:
        generated = self.generate_questions(db, student_id, job_code, profile_version_id, analysis_run_id)
        question_map = {item["question_id"]: item for item in generated["questions"]}
        feedback = []

        for item in answers:
            question = question_map.get(item["question_id"])
            if not question:
                continue
            score, matched, missing = self._score_answer(item["answer"], question.get("focus_checks", []))
            if score >= 85:
                suggestion = "回答结构较完整，建议再补 1 个更具体的量化结果。"
            elif score >= 70:
                suggestion = "回答基本到位，但还可以把技术动作和最终结果说得更具体。"
            else:
                suggestion = f"建议围绕“{'、'.join(question['focus_points'])}”重新组织回答。"
            feedback.append(
                {
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "score": score,
                    "matched_points": matched,
                    "missing_points": missing,
                    "suggestion": suggestion,
                }
            )

        overall_score = round(sum(item["score"] for item in feedback) / max(len(feedback), 1), 2)
        if overall_score >= 85:
            recommendation = "模拟面试表现较好，可以直接作为答辩或岗位面试前的演练材料。"
        elif overall_score >= 70:
            recommendation = "具备基本表达能力，建议重点强化项目细节、量化结果和短板回应。"
        else:
            recommendation = "当前回答还偏泛，建议先按题目逐条准备结构化答案后再进行下一轮模拟。"

        next_actions = generated["focus_summary"][:]
        low_score_items = [item for item in feedback if item["score"] < 70]
        if low_score_items:
            next_actions.append(f"优先重答低分题：{'、'.join(item['question_id'] for item in low_score_items)}")

        return {
            "student_id": generated["student_id"],
            "job_code": generated["job_code"],
            "job_title": generated["job_title"],
            "overall_score": overall_score,
            "readiness_level": generated["readiness_level"],
            "recommendation": recommendation,
            "focus_summary": generated["focus_summary"],
            "feedback": feedback,
            "next_actions": next_actions[:5],
        }

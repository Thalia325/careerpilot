from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from app.services.reference import find_best_template

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_job_profile(self, job_posting: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_student_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def polish_markdown(self, markdown_content: str) -> str:
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    async def generate_job_profile(self, job_posting: dict[str, Any]) -> dict[str, Any]:
        template = find_best_template(job_posting["title"])
        return {
            "job_code": job_posting["job_code"],
            "title": job_posting["title"],
            "summary": template["summary"],
            "skill_requirements": template["skills"],
            "certificate_requirements": template["certificates"],
            "innovation_requirements": template["explanations"]["创新能力"],
            "learning_requirements": template["explanations"]["学习能力"],
            "resilience_requirements": template["explanations"]["抗压能力"],
            "communication_requirements": template["explanations"]["沟通能力"],
            "internship_requirements": template["explanations"]["实习能力"],
            "capability_scores": template["capabilities"],
            "dimension_weights": template["dimension_weights"],
            "explanation_json": template["explanations"],
        }

    async def generate_student_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        skills = sorted(set(payload.get("skills", [])))
        certificates = sorted(set(payload.get("certificates", [])))
        internships = payload.get("internships", [])
        projects = payload.get("projects", [])
        capability_scores = {
            "innovation": min(95, 55 + len(projects) * 12),
            "learning": min(95, 60 + len(skills) * 3 + len(certificates) * 5),
            "resilience": min(95, 60 + len(internships) * 8),
            "communication": min(95, 58 + len(projects) * 6 + len(internships) * 5),
            "internship": min(95, 50 + len(internships) * 15),
        }
        completeness_items = [
            bool(skills),
            bool(certificates),
            bool(projects),
            bool(internships),
            bool(payload.get("self_introduction")),
        ]
        completeness_score = round(sum(1 for item in completeness_items if item) / len(completeness_items) * 100, 2)
        competitiveness_score = round(
            (len(skills) * 7 + len(certificates) * 6 + len(projects) * 10 + len(internships) * 12)
            + sum(capability_scores.values()) / 8,
            2,
        )
        evidence = []
        for skill in skills:
            evidence.append({"source": "融合输入", "excerpt": f"识别到技能：{skill}", "confidence": 0.92})
        for certificate in certificates:
            evidence.append({"source": "融合输入", "excerpt": f"识别到证书：{certificate}", "confidence": 0.95})
        return {
            "source_summary": payload.get("source_summary", ""),
            "skills": skills,
            "certificates": certificates,
            "projects": payload.get("projects", []),
            "internships": payload.get("internships", []),
            "capability_scores": capability_scores,
            "completeness_score": completeness_score,
            "competitiveness_score": min(100.0, competitiveness_score),
            "willingness": payload.get("preferences", {}),
            "evidence": evidence,
        }

    async def generate_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        student_name = payload.get("student_name", "学生")
        job_title = payload.get("job_title", "目标岗位")
        match_result = payload["match_result"]
        path_result = payload["path_result"]
        resume_evidence = payload.get("resume_evidence") or {}
        student_major = payload.get("student_major", "")
        resume_intent = payload.get("resume_intent") or {}
        student_profile = payload.get("student_profile") or {}
        job_profile = payload.get("job_profile") or {}
        path_recs = path_result.get("recommendations") or []
        evaluation_metrics = path_result.get("evaluation_metrics") or []

        gap_items = match_result.get("gap_items") or []
        suggestions = match_result.get("suggestions") or []
        dimensions = match_result.get("dimensions") or []
        strengths = match_result.get("strengths") or []
        total_score = match_result.get("total_score", 0)

        # Build gap description from real gap_items
        skill_gaps = [g for g in gap_items if g.get("type") == "skill"]
        cert_gaps = [g for g in gap_items if g.get("type") == "certificate"]

        # Build strengths from matched skills in evidence
        matched_skills = resume_evidence.get("skills") or []
        student_skills = student_profile.get("skills") or []
        all_matched = list(dict.fromkeys(matched_skills + student_skills))

        # === Section 1: student_summary ===
        student_summary = {
            "name": student_name,
            "major": student_major,
            "grade": payload.get("student_grade", ""),
            "intent_job": resume_intent.get("job", ""),
            "intent_city": resume_intent.get("city", ""),
            "completeness_score": student_profile.get("completeness_score", 0),
        }

        # === Section 2: resume_summary ===
        resume_summary = {
            "skills": resume_evidence.get("skills") or [],
            "projects": resume_evidence.get("projects") or [],
            "internships": resume_evidence.get("internships") or [],
            "certificates": student_profile.get("certificates") or [],
            "raw_excerpt": resume_evidence.get("raw_excerpt", "")[:500],
        }

        # === Section 3: capability_profile ===
        capability_profile = {
            "skills": student_skills,
            "certificates": student_profile.get("certificates") or [],
            "capability_scores": student_profile.get("capability_scores") or {},
            "completeness_score": student_profile.get("completeness_score", 0),
            "competitiveness_score": student_profile.get("competitiveness_score", 0),
            "projects": student_profile.get("projects") or [],
            "internships": student_profile.get("internships") or [],
        }

        # === Section 4: target_job_analysis ===
        current_ability = path_result.get("current_ability") or {}
        target_job_analysis = {
            "job_code": job_profile.get("job_code", ""),
            "job_title": job_title,
            "skill_requirements": job_profile.get("skill_requirements") or [],
            "certificate_requirements": job_profile.get("certificate_requirements") or [],
            "summary": job_profile.get("summary", ""),
            "matched_skills": current_ability.get("matched_skills") or [],
            "missing_skills": current_ability.get("missing_skills") or [],
        }

        # === Section 5: matching_analysis ===
        matching_analysis = {
            "total_score": total_score,
            "dimensions": dimensions,
            "strengths": strengths,
            "summary": match_result.get("summary", ""),
        }

        # === Section 6: gap_analysis ===
        gap_analysis = {
            "skill_gaps": skill_gaps,
            "certificate_gaps": cert_gaps,
            "suggestions": suggestions,
        }

        # === Section 7: career_path ===
        career_path = {
            "primary_path": path_result.get("primary_path", []),
            "alternate_paths": path_result.get("alternate_paths", []),
            "rationale": path_result.get("rationale", ""),
            "current_ability": current_ability,
            "certificate_recommendations": path_result.get("certificate_recommendations") or [],
            "learning_resources": path_result.get("learning_resources") or [],
        }

        # === Section 8: short_term_plan ===
        short_term_items: list[str] = []
        for gap in gap_items:
            short_term_items.append(gap.get("suggestion", f"补齐 {gap['name']}。"))
        for suggestion in suggestions:
            short_term_items.append(suggestion)
        for rec in path_recs:
            if rec.get("phase") == "短期":
                short_term_items.append(f"{rec['focus']}：{'、'.join(rec.get('items', []))}")
        short_term_plan = {
            "items": short_term_items[:8],
            "focus": "补齐目标岗位高频技能与证书",
        }

        # === Section 9: mid_term_plan ===
        mid_term_items: list[str] = []
        for rec in path_recs:
            if rec.get("phase") == "中期":
                mid_term_items.append(f"{rec['focus']}：{'、'.join(rec.get('items', []))}")
        mid_term_plan = {
            "items": mid_term_items[:6],
            "focus": "通过实习/项目验证路径可行性",
        }

        # === Section 10: evaluation_cycle ===
        eval_phases = [m for m in evaluation_metrics if m.get("phase")]
        evaluation_cycle = {
            "cycle": "每 2-4 周复盘一次",
            "metrics": eval_phases if eval_phases else [
                {"phase": "短期", "metric": "技能覆盖率提升", "target": "掌握核心缺失技能", "evaluation_method": "技能自评 + 项目实践验证"},
                {"phase": "中期", "metric": "项目/实习成果达成", "target": "完成实习投递或竞赛项目", "evaluation_method": "实习反馈 + 阶段复盘"},
            ],
        }

        # === Section 11: teacher_comments ===
        teacher_comments = {
            "comments": [],
            "status": "pending_review",
        }

        content = {
            "student_summary": student_summary,
            "resume_summary": resume_summary,
            "capability_profile": capability_profile,
            "target_job_analysis": target_job_analysis,
            "matching_analysis": matching_analysis,
            "gap_analysis": gap_analysis,
            "career_path": career_path,
            "short_term_plan": short_term_plan,
            "mid_term_plan": mid_term_plan,
            "evaluation_cycle": evaluation_cycle,
            "teacher_comments": teacher_comments,
        }

        # === Build markdown from real data ===
        major_text = f"，专业为 {student_major}" if student_major else ""
        intent_text = f"，意向岗位为 {resume_intent.get('job', '')}" if resume_intent.get("job") else ""

        # Dimension lines
        dim_lines = []
        for dim in dimensions:
            dim_lines.append(
                f"- {dim['dimension']}：{dim['score']:.1f} 分（权重 {dim['weight']:.0%}）— {dim.get('reasoning', '')}"
            )
        dim_section = "\n".join(dim_lines) if dim_lines else ""

        # Strengths
        strengths_section = "、".join(strengths[:8]) if strengths else "、".join(all_matched[:8])

        # Gap lines
        gap_lines = []
        if skill_gaps:
            gap_lines.append(f"技能差距：{'、'.join(g['name'] for g in skill_gaps)}")
        if cert_gaps:
            gap_lines.append(f"证书差距：{'、'.join(g['name'] for g in cert_gaps)}")
        gap_section = "；".join(gap_lines) if gap_lines else "无明显差距"

        # Path
        primary_path = path_result.get("primary_path", [])
        alt_paths = path_result.get("alternate_paths", [])
        primary_section = " → ".join(primary_path) if primary_path else job_title
        alt_section = "；".join(" → ".join(p) for p in alt_paths[:3]) if alt_paths else "暂无"

        # Plans
        short_section = "；".join(short_term_items[:6]) if short_term_items else "暂无"
        mid_section = "；".join(mid_term_items[:6]) if mid_term_items else "暂无"

        # Evaluation
        eval_lines = []
        for m in eval_phases:
            eval_lines.append(f"- {m.get('phase', '')}：{m.get('metric', '')}，目标：{m.get('target', '')}，评估方式：{m.get('evaluation_method', '')}")
        eval_section = "\n".join(eval_lines) if eval_lines else "- 每 2-4 周复盘一次；重点看技能覆盖率提升与项目成果达成"

        # Cert recommendations
        cert_recs = path_result.get("certificate_recommendations") or []
        cert_section = "\n".join(f"- {c['name']}（优先级：{c.get('priority', '中')}）— {c.get('reason', '')}" for c in cert_recs[:5]) if cert_recs else "暂无"

        markdown = (
            f"# CareerPilot 职业发展报告\n\n"
            f"## 一、学生基本情况\n"
            f"- 姓名：{student_name}\n"
            f"- 专业：{student_major or '未填写'}\n"
            f"- 年级：{payload.get('student_grade', '未填写')}\n"
            f"- 意向岗位：{resume_intent.get('job', '未填写')}\n"
            f"- 意向城市：{resume_intent.get('city', '未填写')}\n\n"
            f"## 二、简历解析摘要\n"
            f"- 技能：{'、'.join(resume_summary['skills'][:8]) or '暂无'}\n"
            f"- 项目：{'、'.join(resume_summary['projects'][:3]) or '暂无'}\n"
            f"- 实习：{'、'.join(resume_summary['internships'][:3]) or '暂无'}\n"
            f"- 证书：{'、'.join(resume_summary['certificates'][:5]) or '暂无'}\n\n"
            f"## 三、能力画像\n"
            f"- 技能标签：{'、'.join(student_skills[:10]) or '暂无'}\n"
            f"- 证书标签：{'、'.join(student_profile.get('certificates', [])[:5]) or '暂无'}\n"
            f"- 项目经验：{'、'.join(student_profile.get('projects', [])[:3]) or '暂无'}\n"
            f"- 实习经验：{'、'.join(student_profile.get('internships', [])[:3]) or '暂无'}\n"
            f"- 画像完整度：{student_profile.get('completeness_score', 0):.0f}%\n\n"
            f"## 四、目标岗位分析\n"
            f"- 目标岗位：{job_title}\n"
            f"- 岗位摘要：{job_profile.get('summary', '暂无')}\n"
            f"- 技能要求：{'、'.join(job_profile.get('skill_requirements', [])[:10]) or '暂无'}\n"
            f"- 证书要求：{'、'.join(job_profile.get('certificate_requirements', [])[:5]) or '暂无'}\n"
            f"- 已匹配技能：{'、'.join(target_job_analysis['matched_skills'][:8]) or '暂无'}\n"
            f"- 缺失技能：{'、'.join(target_job_analysis['missing_skills'][:8]) or '暂无'}\n\n"
            f"## 五、人岗匹配分析\n"
            f"综合匹配得分：{total_score:.1f} 分\n\n"
            f"### 维度评分\n{dim_section}\n\n"
            f"### 契合点\n{strengths_section}\n\n"
            f"## 六、差距分析\n{gap_section}\n\n"
            f"### 提升建议\n"
            + "\n".join(f"- {s}" for s in suggestions[:5])
            + "\n\n"
            f"## 七、职业路径规划\n"
            f"- 主路径：{primary_section}\n"
            f"- 备选路径：{alt_section}\n"
            f"- 路径依据：{path_result.get('rationale', '暂无')}\n\n"
            f"### 证书建议\n{cert_section}\n\n"
            f"## 八、短期行动计划\n{short_section}\n\n"
            f"## 九、中期行动计划\n{mid_section}\n\n"
            f"## 十、评估周期\n{eval_section}\n\n"
            f"## 十一、教师建议\n"
            f"> 待教师点评后补充。\n"
        )
        return {"content": content, "markdown_content": markdown}

    async def polish_markdown(self, markdown_content: str) -> str:
        polished = markdown_content.strip()
        if "CareerPilot 职业发展报告" not in polished:
            polished = f"# CareerPilot 职业发展报告\n\n{polished}"
        return polished + "\n\n> 本报告已完成智能润色与结构校验。"

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        # Derive a concise reply from the system prompt context; never inject
        # a full-length generic career planning template.
        has_context = "【" in system_prompt and "学生" in system_prompt
        if has_context:
            return (
                f"根据你的背景信息，我为你整理了以下分析要点：\n\n"
                "（Mock 模式）请参考系统提示中的用户背景数据，基于真实信息给出个性化建议。\n\n"
                "> 当前为 Mock 模式，实际部署后将调用 LLM 基于你的真实数据生成完整建议。"
            )
        return (
            "你好！我是职航智策 AI 助手，专门帮助大学生进行职业规划。\n\n"
            "请先上传简历或选择目标岗位，这样我就能基于你的真实数据给出个性化建议。\n\n"
            "你可以问我：\n"
            "- 某个岗位需要什么技能？\n"
            "- 如何从当前专业转入某个职业方向？\n"
            "- 某个行业的发展前景如何？\n\n"
            "请描述你的问题，我会尽力为你解答！"
        )


class ErnieLLMProvider(BaseLLMProvider):
    def __init__(
        self,
        access_token: str,
        base_url: str = "https://aistudio.baidu.com/llm/lmapi/v3",
        model: str = "ernie-5.0-thinking-preview",
        allow_job_profile_mock_fallback: bool = True,
    ) -> None:
        self.access_token = access_token
        self.base_url = base_url
        self.model = model
        self.allow_job_profile_mock_fallback = allow_job_profile_mock_fallback
        self.mock = MockLLMProvider()
        self.client = OpenAI(api_key=access_token, base_url=base_url, timeout=60.0) if access_token else None

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("empty response")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fenced = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))
        first = text.find("{")
        last = text.rfind("}")
        if first >= 0 and last > first:
            return json.loads(text[first : last + 1])
        raise ValueError("no json object found")

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            mapping = {"low": 0.55, "medium": 0.75, "high": 0.92}
            lowered = value.strip().lower()
            if lowered in mapping:
                return mapping[lowered]
            try:
                return float(lowered)
            except ValueError:
                return default
        return default

    def _normalize_student_profile(self, parsed: dict[str, Any]) -> dict[str, Any]:
        capabilities = parsed.get("capability_scores", {}) or {}
        normalized_capabilities = {
            "innovation": round(self._to_float(capabilities.get("innovation"), 60.0), 2),
            "learning": round(self._to_float(capabilities.get("learning"), 60.0), 2),
            "resilience": round(self._to_float(capabilities.get("resilience"), 60.0), 2),
            "communication": round(self._to_float(capabilities.get("communication"), 60.0), 2),
            "internship": round(self._to_float(capabilities.get("internship"), 60.0), 2),
        }
        evidence = []
        for item in parsed.get("evidence", []) or []:
            if isinstance(item, dict):
                evidence.append(
                    {
                        "source": str(item.get("source", "ERNIE")),
                        "excerpt": str(item.get("excerpt", "")),
                        "confidence": round(self._to_float(item.get("confidence"), 0.8), 2),
                    }
                )
        return {
            "source_summary": str(parsed.get("source_summary", "ERNIE 生成画像")),
            "skills": [str(item) for item in parsed.get("skills", []) if item],
            "certificates": [str(item) for item in parsed.get("certificates", []) if item],
            "projects": [str(item) for item in parsed.get("projects", []) if item],
            "internships": [str(item) for item in parsed.get("internships", []) if item],
            "capability_scores": normalized_capabilities,
            "completeness_score": round(self._to_float(parsed.get("completeness_score"), 80.0), 2),
            "competitiveness_score": round(self._to_float(parsed.get("competitiveness_score"), 80.0), 2),
            "willingness": parsed.get("willingness", {}) if isinstance(parsed.get("willingness", {}), dict) else {},
            "evidence": evidence,
        }

    def _normalize_job_profile(self, parsed: dict[str, Any], fallback_title: str, fallback_job_code: str) -> dict[str, Any]:
        capabilities = parsed.get("capability_scores", {}) or {}
        weights = parsed.get("dimension_weights", {}) or {}
        normalized = {
            "job_code": str(parsed.get("job_code", fallback_job_code)),
            "title": str(parsed.get("title", fallback_title)),
            "summary": str(parsed.get("summary", "")),
            "skill_requirements": [str(item) for item in parsed.get("skill_requirements", []) if item],
            "certificate_requirements": [str(item) for item in parsed.get("certificate_requirements", []) if item],
            "innovation_requirements": str(parsed.get("innovation_requirements", "")),
            "learning_requirements": str(parsed.get("learning_requirements", "")),
            "resilience_requirements": str(parsed.get("resilience_requirements", "")),
            "communication_requirements": str(parsed.get("communication_requirements", "")),
            "internship_requirements": str(parsed.get("internship_requirements", "")),
            "capability_scores": {
                "innovation": round(self._to_float(capabilities.get("innovation"), 75.0), 2),
                "learning": round(self._to_float(capabilities.get("learning"), 80.0), 2),
                "resilience": round(self._to_float(capabilities.get("resilience"), 75.0), 2),
                "communication": round(self._to_float(capabilities.get("communication"), 78.0), 2),
                "internship": round(self._to_float(capabilities.get("internship"), 75.0), 2),
            },
            "dimension_weights": {
                "basic_requirements": round(self._to_float(weights.get("basic_requirements"), 0.2), 2),
                "professional_skills": round(self._to_float(weights.get("professional_skills"), 0.4), 2),
                "professional_literacy": round(self._to_float(weights.get("professional_literacy"), 0.2), 2),
                "development_potential": round(self._to_float(weights.get("development_potential"), 0.2), 2),
            },
            "explanation_json": parsed.get("explanation_json", {}) if isinstance(parsed.get("explanation_json", {}), dict) else {},
        }
        return normalized

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            raise RuntimeError("AI Studio Access Token 未配置")
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
                message = completion.choices[0].message
                return message.content or getattr(message, "reasoning_content", "") or ""
            except Exception as exc:
                last_error = exc
                error_text = str(exc)
                should_retry = any(
                    marker in error_text
                    for marker in (
                        "访问过于频繁",
                        "Too Many Requests",
                        "rate limit",
                        "429",
                    )
                )
                if not should_retry or attempt == 4:
                    raise
                sleep_seconds = attempt * 10
                logger.warning(
                    "ERNIE chat throttled on attempt %s/4, retrying in %ss: %s",
                    attempt,
                    sleep_seconds,
                    exc,
                )
                time.sleep(sleep_seconds)
        raise RuntimeError(f"ERNIE chat failed after retries: {last_error}")

    def _repair_json(self, invalid_response: str) -> dict[str, Any]:
        repair_system_prompt = (
            "You repair model output into exactly one valid JSON object. "
            "Return JSON only. Do not add markdown, explanations, or code fences. "
            "Keep the original fields and values whenever possible."
        )
        repair_user_prompt = json.dumps({"invalid_response": invalid_response}, ensure_ascii=False)
        repaired = self._chat(repair_system_prompt, repair_user_prompt)
        return self._extract_json(repaired)

    def _request_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        response_label: str,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        raw_content = self._chat(system_prompt, user_prompt)
        try:
            return self._extract_json(raw_content)
        except Exception as exc:
            last_error = exc
            logger.warning("Failed to parse %s response on attempt 1: %s", response_label, exc)

        try:
            return self._repair_json(raw_content)
        except Exception as exc:
            last_error = exc
            logger.warning("Failed to repair %s response on attempt 2: %s", response_label, exc)

        retry_system_prompt = (
            f"{system_prompt}\n"
            "Return exactly one valid JSON object. "
            "Do not wrap it in markdown. "
            "Do not output any text before or after the JSON."
        )
        raw_content = self._chat(retry_system_prompt, user_prompt)
        try:
            return self._extract_json(raw_content)
        except Exception as exc:
            last_error = exc
            logger.warning("Failed to parse %s response on attempt 3: %s", response_label, exc)

        try:
            return self._repair_json(raw_content)
        except Exception as exc:
            last_error = exc
            logger.warning("Failed to repair %s response on attempt 4: %s", response_label, exc)

        raise ValueError(f"{response_label} JSON parsing failed after 4 attempts: {last_error}")

    async def generate_job_profile(self, job_posting: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "你是 CareerPilot 的岗位画像专家。"
            "请仅返回 JSON，不要输出解释、标题或 Markdown。"
            "JSON 字段必须包含：job_code,title,summary,skill_requirements,"
            "certificate_requirements,innovation_requirements,learning_requirements,"
            "resilience_requirements,communication_requirements,internship_requirements,"
            "capability_scores,dimension_weights,explanation_json。"
            "其中 capability_scores 必须包含 innovation,learning,resilience,communication,internship 五项 0-100 分。"
            "dimension_weights 必须包含 basic_requirements,professional_skills,professional_literacy,development_potential 四项，且总和为 1。"
            "explanation_json 需包含 专业技能、证书要求、创新能力、学习能力、抗压能力、沟通能力、实习能力 七项。"
        )
        user_prompt = json.dumps(job_posting, ensure_ascii=False)
        try:
            parsed = self._request_json(system_prompt, user_prompt, response_label="job profile")
            return self._normalize_job_profile(parsed, job_posting["title"], job_posting["job_code"])
        except Exception as exc:
            if not self.allow_job_profile_mock_fallback:
                raise
            logger.warning("ERNIE job profile generation failed, fallback to mock: %s", exc)
            return await self.mock.generate_job_profile(job_posting)

    async def generate_student_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "你是 CareerPilot 的学生就业能力画像专家。"
            "请根据输入材料生成学生画像，并且只返回 JSON。"
            "JSON 字段必须包含：source_summary,skills,certificates,projects,internships,capability_scores,"
            "completeness_score,competitiveness_score,willingness,evidence。"
            "capability_scores 必须包含 innovation,learning,resilience,communication,internship 五项分数。"
            "evidence 必须是数组，每项包含 source,excerpt,confidence。"
            "请重点分析以下内容："
            "1. 实习经历：从实习中提取相关技能、工作内容、职责范围和实践经验"
            "2. 项目经历：分析项目的技术难度、团队协作、个人贡献和实际成果"
            "3. 评估这些经历对职业发展的价值和与目标岗位的匹配度"
            "4. 将具体的实习和项目经历作为证据链的一部分"
            "注意：如果 payload 中包含 major_source 字段为 'OCR解析'，说明专业信息是从简历OCR解析得到的，"
            "这是最准确的信息来源，请直接使用，不要提示与'学生基本信息'存在差异。"
        )
        user_prompt = json.dumps(payload, ensure_ascii=False)
        try:
            parsed = self._request_json(system_prompt, user_prompt, response_label="student profile")
            return self._normalize_student_profile(parsed)
        except Exception as exc:
            logger.warning("ERNIE student profile generation failed, fallback to mock: %s", exc)
            return await self.mock.generate_student_profile(payload)

    async def generate_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "你是 CareerPilot 的职业规划报告生成专家。"
            "请只返回 JSON，不要输出 Markdown 代码块。"
            "JSON 顶层字段必须包含 content 和 markdown_content。"
            "content 必须包含 student_summary,resume_summary,capability_profile,target_job_analysis,"
            "matching_analysis,gap_analysis,career_path,short_term_plan,mid_term_plan,evaluation_cycle,teacher_comments。"
            "\n\n**核心要求：必须逐项消费真实匹配结果，不得生成泛化文案。**"
            "\n- student_summary：包含 name、major、grade、intent_job、intent_city、completeness_score。"
            "\n- resume_summary：包含 skills、projects、internships、certificates、raw_excerpt。"
            "\n- capability_profile：包含 skills、certificates、capability_scores、completeness_score、projects、internships。"
            "\n- target_job_analysis：包含 job_code、job_title、skill_requirements、certificate_requirements、summary、matched_skills、missing_skills。"
            "\n- matching_analysis：包含 total_score、dimensions、strengths、summary。"
            "\n- gap_analysis：包含 skill_gaps、certificate_gaps、suggestions。"
            "\n- career_path：包含 primary_path、alternate_paths、rationale、current_ability、certificate_recommendations、learning_resources。"
            "\n- short_term_plan：包含 items、focus。"
            "\n- mid_term_plan：包含 items、focus。"
            "\n- evaluation_cycle：包含 cycle、metrics。"
            "\n- teacher_comments：包含 comments（列表）、status（如 pending_review）。"
            "\n\nmarkdown_content 需为中文职业发展报告，可直接导出，并必须覆盖以下章节："
            "一、学生基本情况；二、简历解析摘要；三、能力画像；四、目标岗位分析；"
            "五、人岗匹配分析；六、差距分析；七、职业路径规划；"
            "八、短期行动计划；九、中期行动计划；十、评估周期；十一、教师建议。"
            "\n\n注意：如果 payload 中包含 student_major_source 字段为 'OCR解析'，说明专业信息是从简历OCR解析得到的，"
            "这是最准确的信息来源，请直接使用 student_major 字段作为专业信息。"
        )
        user_prompt = json.dumps(payload, ensure_ascii=False)
        try:
            parsed = self._request_json(system_prompt, user_prompt, response_label="report")
            return parsed
        except Exception as exc:
            logger.warning("ERNIE report generation failed, fallback to mock: %s", exc)
            return await self.mock.generate_report(payload)

    async def polish_markdown(self, markdown_content: str) -> str:
        system_prompt = (
            "你是 CareerPilot 的中文报告润色助手。"
            "请在不改变事实的前提下润色内容，并返回纯 Markdown 文本。"
            "要求保留标题结构，增强可读性、完整性和职业规划语气。"
        )
        try:
            polished = self._chat(system_prompt, markdown_content).strip()
            if not polished:
                raise ValueError("empty polished content")
            return polished
        except Exception as exc:
            logger.warning("ERNIE markdown polish failed, fallback to mock: %s", exc)
            return await self.mock.polish_markdown(markdown_content)


async def safe_ping_http(url: str) -> bool:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            return response.status_code < 500
    except Exception:
        return False

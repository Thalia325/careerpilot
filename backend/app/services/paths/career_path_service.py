from __future__ import annotations

import logging
import re
from ast import literal_eval
from types import SimpleNamespace
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobProfile, PathRecommendation, ProfileVersion, StudentProfile
from app.services.paths.graph_query_service import GraphQueryService

logger = logging.getLogger(__name__)


TRANSITION_FALLBACKS: dict[str, list[list[str]]] = {
    "AI 算法工程师": [
        ["AI 算法工程师", "数据工程师"],
        ["AI 算法工程师", "后端开发工程师"],
        ["AI 算法工程师", "数据分析师"],
        ["AI 算法工程师", "AI 产品经理"],
    ],
    "数据工程师": [
        ["数据工程师", "AI 算法工程师"],
        ["数据工程师", "数据分析师"],
        ["数据工程师", "后端开发工程师"],
    ],
    "数据分析师": [
        ["数据分析师", "数据产品经理"],
        ["数据分析师", "AI 算法工程师"],
        ["数据分析师", "产品经理"],
    ],
    "后端开发工程师": [
        ["后端开发工程师", "AI 算法工程师"],
        ["后端开发工程师", "数据工程师"],
        ["后端开发工程师", "全栈工程师"],
    ],
    "前端开发工程师": [
        ["前端开发工程师", "全栈工程师"],
        ["前端开发工程师", "产品经理"],
        ["前端开发工程师", "UI/UX 设计师"],
    ],
    "全栈工程师": [
        ["全栈工程师", "后端开发工程师"],
        ["全栈工程师", "前端架构师"],
        ["全栈工程师", "产品经理"],
    ],
    "产品经理": [
        ["产品经理", "数据产品经理"],
        ["产品经理", "项目经理"],
        ["产品经理", "运营专家"],
    ],
    "UI/UX 设计师": [
        ["UI/UX 设计师", "产品经理"],
        ["UI/UX 设计师", "数据产品经理"],
        ["UI/UX 设计师", "前端开发工程师"],
    ],
    "测试工程师": [
        ["测试工程师", "测试开发工程师"],
        ["测试工程师", "产品经理"],
        ["测试工程师", "数据分析师"],
    ],
    "测试开发工程师": [
        ["测试开发工程师", "后端开发工程师"],
        ["测试开发工程师", "运维工程师"],
        ["测试开发工程师", "全栈工程师"],
    ],
    "金融分析师": [
        ["金融分析师", "投资顾问"],
        ["金融分析师", "风险控制专员"],
        ["金融分析师", "数据分析师"],
    ],
    "财务会计": [
        ["财务会计", "审计专员"],
        ["财务会计", "金融分析师"],
        ["财务会计", "税务专员"],
    ],
    "法务专员": [
        ["法务专员", "合规专员"],
        ["法务专员", "知识产权专员"],
    ],
    "培训讲师": [
        ["培训讲师", "人力资源专员"],
        ["培训讲师", "教学设计师"],
    ],
    "市场营销专员": [
        ["市场营销专员", "品牌策划"],
        ["市场营销专员", "广告策划"],
        ["市场营销专员", "电商运营"],
    ],
    "销售代表": [
        ["销售代表", "大客户经理"],
        ["销售代表", "医药代表"],
        ["销售代表", "市场营销专员"],
    ],
    "人力资源专员": [
        ["人力资源专员", "行政管理"],
        ["人力资源专员", "法务专员"],
    ],
    "行政专员": [
        ["行政专员", "人力资源专员"],
        ["行政专员", "项目管理"],
    ],
    "机械工程师": [
        ["机械工程师", "工业工程师"],
        ["机械工程师", "质量工程师"],
        ["机械工程师", "项目管理"],
    ],
    "土木工程师": [
        ["土木工程师", "建筑设计师"],
        ["土木工程师", "工程项目管理"],
    ],
    "建筑设计师": [
        ["建筑设计师", "UI/UX 设计师"],
        ["建筑设计师", "室内设计师"],
        ["建筑设计师", "项目管理"],
    ],
    "电气工程师": [
        ["电气工程师", "新能源工程师"],
        ["电气工程师", "运维工程师"],
        ["电气工程师", "项目管理"],
    ],
    "医药代表": [
        ["医药代表", "销售代表"],
        ["医药代表", "市场营销专员"],
    ],
    "供应链专员": [
        ["供应链专员", "采购专员"],
        ["供应链专员", "数据分析师"],
        ["供应链专员", "电商运营"],
    ],
    "记者/编辑": [
        ["记者/编辑", "新媒体运营"],
        ["记者/编辑", "公关专员"],
        ["记者/编辑", "广告策划"],
    ],
    "新媒体运营": [
        ["新媒体运营", "电商运营"],
        ["新媒体运营", "市场营销专员"],
        ["新媒体运营", "产品经理"],
    ],
    "管理咨询顾问": [
        ["管理咨询顾问", "产品经理"],
        ["管理咨询顾问", "项目管理"],
        ["管理咨询顾问", "金融分析师"],
    ],
}


def _unique_paths(paths: list[list[str]]) -> list[list[str]]:
    seen: set[str] = set()
    result: list[list[str]] = []
    for path in paths:
        normalized = [item for item in path if item]
        key = "->".join(normalized)
        if len(normalized) >= 2 and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _job_info(title: str, profiles_by_title: dict[str, JobProfile]) -> dict:
    profile = profiles_by_title.get(title)
    return {
        "title": title,
        "description": profile.summary if profile and profile.summary else f"{title} 相关岗位，需结合业务场景持续积累项目经验。",
        "skills": (profile.skill_requirements if profile else [])[:6],
    }


UNAVAILABLE_VALUES = {
    "",
    "无",
    "暂无",
    "未知",
    "未填写",
    "不详",
    "没有",
    "无证书",
    "暂无证书",
    "none",
    "null",
    "n/a",
    "na",
}

UNAVAILABLE_PHRASES = (
    "由于信息不足",
    "信息不足",
    "无法详细",
    "无法列举",
    "无法判断",
    "无法识别",
    "无法确定",
    "不能确定",
    "不可得",
    "不明确",
    "未提供",
    "未提及",
    "没有提及",
    "可推测",
    "推测",
)

GENERIC_STRUCTURED_VALUES = {"负责人", "实习生", "学生", "经历", "项目"}


def _parse_object_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{" or text[-1] not in "]}":
        return value
    try:
        return literal_eval(text)
    except (ValueError, SyntaxError):
        return value


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" \t\r\n,，;；、。")
    if not text:
        return ""
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        return ""
    if text in UNAVAILABLE_VALUES or text.lower() in UNAVAILABLE_VALUES:
        return ""
    if any(phrase in text for phrase in UNAVAILABLE_PHRASES):
        return ""
    return text


def _clean_value(value: Any, *, limit: int = 4) -> str:
    parsed = _parse_object_string(value)
    if isinstance(parsed, dict):
        parts = _clean_list(parsed.values(), limit=limit)
        return "；".join(parts)
    if isinstance(parsed, (list, tuple, set)):
        parts = _clean_list(parsed, limit=limit)
        return "、".join(parts)
    return _clean_text(parsed)


def _format_structured_item(item: dict[str, Any], keys: list[str]) -> str:
    values: dict[str, str] = {}
    for key in keys:
        cleaned = _clean_value(item.get(key))
        if cleaned:
            values[key] = cleaned

    title_keys = [key for key in ("name", "project_name", "company") if key in keys]
    title = next((values.pop(key) for key in title_keys if values.get(key)), "")
    if not title and "position" in values and values["position"] not in GENERIC_STRUCTURED_VALUES:
        title = values.pop("position")

    details = [value for value in values.values() if value not in GENERIC_STRUCTURED_VALUES]
    if not title and not details:
        return ""
    if not details and title in GENERIC_STRUCTURED_VALUES:
        return ""
    if title and details:
        return f"{title}：{'；'.join(details)}"
    return title or "；".join(details)


def _clean_list(values: Any, *, limit: int = 12, object_keys: list[str] | None = None) -> list[str]:
    parsed = _parse_object_string(values)
    if parsed is None:
        return []
    if isinstance(parsed, dict):
        iterable: list[Any] = [parsed]
    elif isinstance(parsed, (list, tuple, set)):
        iterable = list(parsed)
    else:
        iterable = [parsed]

    result: list[str] = []
    seen: set[str] = set()
    for item in iterable:
        parsed_item = _parse_object_string(item)
        if isinstance(parsed_item, (list, tuple, set)):
            candidates = _clean_list(parsed_item, limit=limit, object_keys=object_keys)
        elif isinstance(parsed_item, dict):
            if object_keys:
                candidates = [_format_structured_item(parsed_item, object_keys)]
            else:
                candidates = _clean_list(parsed_item.values(), limit=limit)
        else:
            candidates = [_clean_text(parsed_item)]

        for candidate in candidates:
            cleaned = _clean_text(candidate)
            if not cleaned or cleaned in GENERIC_STRUCTURED_VALUES:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(cleaned)
            if len(result) >= limit:
                return result
    return result


def clean_current_ability(current_ability: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize current ability content before storing or returning it."""
    ability = dict(current_ability or {})
    ability["skills"] = _clean_list(ability.get("skills"), limit=16)
    ability["certificates"] = _clean_list(ability.get("certificates"), limit=8)
    ability["projects"] = _clean_list(
        ability.get("projects"),
        limit=6,
        object_keys=[
            "name",
            "project_name",
            "description",
            "actual_achievements",
        ],
    )
    ability["internships"] = _clean_list(
        ability.get("internships"),
        limit=4,
        object_keys=["company", "position", "duration", "responsibilities", "gained_skills"],
    )
    ability["matched_skills"] = _clean_list(ability.get("matched_skills"), limit=12)
    ability["missing_skills"] = _clean_list(ability.get("missing_skills"), limit=12)
    return ability


class CareerPathService:
    def __init__(self, graph_query_service: GraphQueryService) -> None:
        self.graph_query_service = graph_query_service

    @staticmethod
    def _profile_from_version(version: ProfileVersion, fallback: StudentProfile) -> SimpleNamespace:
        snapshot = version.snapshot_json or {}
        return SimpleNamespace(
            skills_json=snapshot.get("skills") or fallback.skills_json or [],
            certificates_json=snapshot.get("certificates") or fallback.certificates_json or [],
            projects_json=snapshot.get("projects") or fallback.projects_json or [],
            internships_json=snapshot.get("internships") or fallback.internships_json or [],
            capability_scores=snapshot.get("capability_scores") or fallback.capability_scores or {},
        )

    async def plan_path(
        self,
        db: Session,
        student_id: int,
        job_code: str,
        profile_version_id: int | None = None,
        match_result_id: int | None = None,
        analysis_run_id: int | None = None,
    ) -> dict:
        try:
            student_profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id))
            job_profile = db.scalar(select(JobProfile).where(JobProfile.job_code == job_code))
            if not student_profile or not job_profile:
                raise ValueError("路径规划缺少学生画像或岗位画像")
            ability_profile = student_profile
            if profile_version_id:
                profile_version = db.get(ProfileVersion, profile_version_id)
                if not profile_version or profile_version.student_id != student_id:
                    raise ValueError("画像版本不存在或不属于当前学生")
                ability_profile = self._profile_from_version(profile_version, student_profile)
            graph = await self.graph_query_service.query_job(job_code)
            primary_path = graph["promotion_paths"][0] if graph["promotion_paths"] else [job_profile.title]
            all_profiles = list(db.scalars(select(JobProfile)).all())
            profiles_by_title: dict[str, JobProfile] = {}
            for profile in all_profiles:
                profiles_by_title.setdefault(profile.title, profile)

            alternate_paths = self._build_transition_paths(graph, job_profile.title)
            vertical_graph = self._build_vertical_graph(graph, primary_path, profiles_by_title)
            transition_graph = self._build_transition_graph(graph, job_profile.title, alternate_paths, profiles_by_title)
            gaps = [
                {"stage": "当前岗位", "missing_skills": graph["adjacent_skill_gaps"].get(path[-1], [])}
                for path in alternate_paths
            ]
            recommendations = [
                {
                    "phase": "短期",
                    "focus": "补齐目标岗位高频技能与证书",
                    "items": job_profile.skill_requirements[:3],
                },
                {
                    "phase": "中期",
                    "focus": "通过实习/项目验证路径可行性",
                    "items": ["实习投递", "竞赛项目", "阶段复盘"],
                },
            ]
            rationale = "基于岗位图谱的晋升链路和转岗链路，结合学生当前技能覆盖情况生成主路径与备选路径。"

            # Build enriched content
            current_ability = self._build_current_ability(ability_profile, job_profile)
            certificate_recommendations = self._build_certificate_recommendations(ability_profile, job_profile)
            learning_resources = self._build_learning_resources(ability_profile, job_profile, gaps)
            evaluation_metrics = self._build_evaluation_metrics(job_profile, recommendations)

            if analysis_run_id:
                existing = db.scalar(
                    select(PathRecommendation)
                    .where(PathRecommendation.student_id == student_id)
                    .where(PathRecommendation.target_job_code == job_code)
                    .where(PathRecommendation.analysis_run_id == analysis_run_id)
                )
            elif profile_version_id:
                existing = db.scalar(
                    select(PathRecommendation)
                    .where(PathRecommendation.student_id == student_id)
                    .where(PathRecommendation.target_job_code == job_code)
                    .where(PathRecommendation.profile_version_id == profile_version_id)
                )
            else:
                existing = db.scalar(
                    select(PathRecommendation)
                    .where(PathRecommendation.student_id == student_id)
                    .where(PathRecommendation.target_job_code == job_code)
                    .where(PathRecommendation.analysis_run_id == None)
                    .where(PathRecommendation.profile_version_id == None)
                )
            if not existing:
                existing = PathRecommendation(student_id=student_id, target_job_code=job_code)
                db.add(existing)
                db.flush()
            existing.primary_path_json = primary_path
            existing.alternate_paths_json = alternate_paths
            existing.vertical_graph_json = vertical_graph
            existing.transition_graph_json = transition_graph
            existing.gaps_json = gaps
            existing.recommendations_json = recommendations
            existing.current_ability_json = current_ability
            existing.certificate_recommendations_json = certificate_recommendations
            existing.learning_resources_json = learning_resources
            existing.evaluation_metrics_json = evaluation_metrics
            # Store binding IDs
            if profile_version_id is not None:
                existing.profile_version_id = profile_version_id
            if match_result_id is not None:
                existing.match_result_id = match_result_id
            if analysis_run_id is not None:
                existing.analysis_run_id = analysis_run_id
            db.commit()
            return {
                "path_recommendation_id": existing.id,
                "student_id": student_id,
                "target_job_code": job_code,
                "primary_path": primary_path,
                "alternate_paths": alternate_paths,
                "vertical_graph": vertical_graph,
                "transition_graph": transition_graph,
                "gaps": gaps,
                "recommendations": recommendations,
                "rationale": rationale,
                "current_ability": current_ability,
                "certificate_recommendations": certificate_recommendations,
                "learning_resources": learning_resources,
                "evaluation_metrics": evaluation_metrics,
                "profile_version_id": existing.profile_version_id,
                "match_result_id": existing.match_result_id,
                "analysis_run_id": existing.analysis_run_id,
            }
        except ValueError as e:
            logger.error(f"ValueError in plan_path for student {student_id}, job {job_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in plan_path for student {student_id}, job {job_code}: {str(e)}")
            raise ValueError(f"Failed to plan career path: {str(e)}") from e

    def _build_current_ability(self, student_profile: StudentProfile, job_profile: JobProfile) -> dict[str, Any]:
        """Build current ability starting point from student profile."""
        student_skill_list = _clean_list(student_profile.skills_json or [], limit=16)
        job_skill_list = _clean_list(job_profile.skill_requirements or [], limit=16)
        student_skills = set(student_skill_list)
        job_skills = set(job_skill_list)
        matched_skills = list(student_skills & job_skills)
        missing_skills = list(job_skills - student_skills)
        student_certs = set(_clean_list(student_profile.certificates_json or [], limit=8))
        return clean_current_ability({
            "skills": student_skill_list,
            "certificates": list(student_certs),
            "projects": student_profile.projects_json or [],
            "internships": student_profile.internships_json or [],
            "capability_scores": student_profile.capability_scores or {},
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        })

    def _build_certificate_recommendations(self, student_profile: StudentProfile, job_profile: JobProfile) -> list[dict[str, Any]]:
        """Build certificate recommendations based on gap analysis."""
        student_certs = set(student_profile.certificates_json or [])
        job_certs = set(job_profile.certificate_requirements or [])
        missing_certs = job_certs - student_certs
        recommendations = []
        for cert in missing_certs:
            recommendations.append({
                "name": cert,
                "priority": "高" if cert in list(job_certs)[:3] else "中",
                "reason": f"目标岗位 {job_profile.title} 要求持有 {cert} 证书",
            })
        return recommendations

    def _build_learning_resources(
        self, student_profile: StudentProfile, job_profile: JobProfile, gaps: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build learning resource recommendations."""
        resources = []
        # From missing skills
        missing_skills = set(job_profile.skill_requirements or []) - set(student_profile.skills_json or [])
        for skill in list(missing_skills)[:5]:
            resources.append({
                "type": "技能",
                "name": skill,
                "suggestion": f"通过在线课程或项目实践提升 {skill} 技能",
                "phase": "短期",
            })
        # From gaps
        for gap in gaps[:3]:
            for missing in gap.get("missing_skills", [])[:2]:
                resources.append({
                    "type": "技能",
                    "name": missing,
                    "suggestion": f"补齐 {missing} 以满足转岗路径要求",
                    "phase": "中期",
                })
        return resources

    def _build_evaluation_metrics(self, job_profile: JobProfile, recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build evaluation metrics for short/mid-term plans."""
        metrics = []
        for rec in recommendations:
            phase = rec.get("phase", "短期")
            items = rec.get("items", [])
            if phase == "短期":
                metrics.append({
                    "phase": phase,
                    "metric": "技能覆盖率提升",
                    "target": f"{phase}内掌握 {', '.join(items[:2])}",
                    "evaluation_method": "技能自评 + 项目实践验证",
                })
            else:
                metrics.append({
                    "phase": phase,
                    "metric": "项目/实习成果达成",
                    "target": f"{phase}内完成 {', '.join(items[:2])}",
                    "evaluation_method": "实习反馈 + 阶段复盘",
                })
        return metrics

    def _build_vertical_graph(self, graph: dict, primary_path: list[str], profiles_by_title: dict[str, JobProfile]) -> dict:
        promotion_paths = _unique_paths(graph.get("promotion_paths", []) or [primary_path])
        nodes = []
        for idx, title in enumerate(primary_path):
            info = _job_info(title, profiles_by_title)
            nodes.append({
                **info,
                "level": idx + 1,
                "stage": "当前目标" if idx == 0 else ("中期晋升" if idx == 1 else "长期发展"),
            })
        edges = [
            {
                "from": primary_path[idx],
                "to": primary_path[idx + 1],
                "relation": "晋升",
                "description": f"从 {primary_path[idx]} 晋升到 {primary_path[idx + 1]}，需要沉淀项目成果和团队协作能力。",
            }
            for idx in range(len(primary_path) - 1)
        ]
        return {
            "title": graph.get("title", primary_path[0] if primary_path else ""),
            "description": graph.get("description") or _job_info(primary_path[0], profiles_by_title)["description"],
            "nodes": nodes,
            "edges": edges,
            "promotion_paths": promotion_paths,
            "vertical_paths": graph.get("vertical_paths", []),
        }

    def _build_transition_paths(self, graph: dict, target_title: str) -> list[list[str]]:
        paths = _unique_paths(graph.get("transition_paths", []) + TRANSITION_FALLBACKS.get(target_title, []))
        for cluster in graph.get("transition_clusters", []):
            paths.extend(_unique_paths(cluster.get("related_paths", [])))
        related_titles = [target_title] + list(TRANSITION_FALLBACKS.keys())[:10]
        for related_title in related_titles:
            paths.extend(TRANSITION_FALLBACKS.get(related_title, []))
        return _unique_paths(paths)

    def _build_transition_graph(
        self,
        graph: dict,
        target_title: str,
        paths: list[list[str]],
        profiles_by_title: dict[str, JobProfile],
    ) -> dict:
        role_order: list[str] = [target_title]
        for path in paths:
            for title in path:
                if title not in role_order:
                    role_order.append(title)

        role_order = role_order[:8]
        role_paths = []
        for title in role_order:
            title_paths = [path for path in paths if path[0] == title or title in path]
            title_paths.extend(TRANSITION_FALLBACKS.get(title, []))
            unique = _unique_paths(title_paths)
            if len(unique) < 2:
                unique.extend(_unique_paths([[title, target_title], [title, "数据产品经理"]]))
            unique = [path for path in _unique_paths(unique) if path[0] == title or title in path][:3]
            if len(unique) < 2:
                continue
            role_paths.append({
                **_job_info(title, profiles_by_title),
                "paths": [
                    {
                        "steps": path,
                        "relation": "换岗",
                        "description": f"{path[0]} 可通过补齐 {path[-1]} 的核心技能完成转换。",
                        "skill_bridge": _job_info(path[-1], profiles_by_title)["skills"][:4],
                    }
                    for path in unique[:3]
                ],
            })

        if len(role_paths) < 5:
            for title in TRANSITION_FALLBACKS:
                if any(item["title"] == title for item in role_paths):
                    continue
                unique = _unique_paths(TRANSITION_FALLBACKS[title])
                role_paths.append({
                    **_job_info(title, profiles_by_title),
                    "paths": [
                        {
                            "steps": path,
                            "relation": "换岗",
                            "description": f"{path[0]} 可向 {path[-1]} 转换，重点补齐目标岗位技能。",
                            "skill_bridge": _job_info(path[-1], profiles_by_title)["skills"][:4],
                        }
                        for path in unique[:3]
                    ],
                })
                if len(role_paths) >= 5:
                    break

        nodes = [_job_info(title, profiles_by_title) for title in role_order]
        edges = [
            {"from": path[0], "to": path[-1], "relation": "换岗", "steps": path}
            for path in paths[:20]
        ]
        return {
            "target": target_title,
            "nodes": nodes,
            "edges": edges,
            "role_paths": role_paths[:8],
            "clusters": graph.get("transition_clusters", []),
        }

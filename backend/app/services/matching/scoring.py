from __future__ import annotations

import re


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


SKILL_GROUPS: dict[str, set[str]] = {
    "ai_ml": {
        "ai", "人工智能", "算法", "算法工程", "机器学习", "深度学习", "模型", "建模",
        "pytorch", "tensorflow", "sklearn", "scikit-learn",
    },
    "data": {
        "数据", "数据分析", "数据处理", "统计", "统计建模", "sql", "mysql", "pandas",
        "numpy", "数据可视化", "可视化", "excel",
    },
    "backend": {
        "后端", "后端开发", "api", "接口", "java", "python", "fastapi", "springboot",
        "spring boot", "mysql", "sql",
    },
    "frontend": {
        "前端", "前端开发", "javascript", "typescript", "react", "vue", "vuejs",
        "vue.js", "html", "css", "nextjs", "next.js",
    },
    "testing": {
        "测试", "自动化测试", "测试用例", "postman", "selenium", "smoketest", "质量保障",
    },
    "devops": {
        "运维", "linux", "docker", "kubernetes", "k8s", "ci/cd", "cicd", "shell",
    },
    "product": {
        "产品", "需求", "需求分析", "原型", "用户研究", "项目管理", "商业分析",
    },
}


ALIASES: dict[str, str] = {
    "vuejs": "vue",
    "vue.js": "vue",
    "nextjs": "next.js",
    "springboot": "spring boot",
    "k8s": "kubernetes",
    "cicd": "ci/cd",
    "smoke test": "smoketest",
}


def _normalize_skill(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    compact = text.replace(" ", "")
    return ALIASES.get(text) or ALIASES.get(compact) or compact


def _skill_groups(value: object) -> set[str]:
    normalized = _normalize_skill(value)
    groups: set[str] = set()
    for group, tokens in SKILL_GROUPS.items():
        normalized_tokens = {_normalize_skill(token) for token in tokens}
        if normalized in normalized_tokens:
            groups.add(group)
            continue
        if any(
            token
            and not token.isascii()
            and not normalized.isascii()
            and (token in normalized or normalized in token)
            for token in normalized_tokens
        ):
            groups.add(group)
    return groups


def _has_directional_relationship(student_norm: str, required_norm: str) -> bool:
    ai_terms = {"ai", "人工智能", "算法", "机器学习", "深度学习", "模型", "建模", "pytorch", "tensorflow"}
    if student_norm in ai_terms and required_norm in ai_terms:
        return True

    if student_norm == "python" and required_norm in {"pandas", "numpy"}:
        return True
    if student_norm in {"python", "sql", "mysql"} and required_norm in {"数据分析", "数据处理", "统计", "统计建模", "数据可视化"}:
        return True
    if student_norm in {"javascript", "typescript"} and required_norm in {"react", "vue", "html", "css"}:
        return True
    if student_norm == "python" and required_norm == "fastapi":
        return True
    if student_norm == "java" and required_norm == "spring boot":
        return True
    if student_norm == "linux" and required_norm in {"shell", "ci/cd"}:
        return True
    return False


def _skill_similarity(student_skill: str, required_skill: str) -> float:
    student_norm = _normalize_skill(student_skill)
    required_norm = _normalize_skill(required_skill)
    if not student_norm or not required_norm:
        return 0.0
    if student_norm == required_norm:
        return 1.0
    if (
        not (student_norm.isascii() and required_norm.isascii())
        and len(student_norm) >= 3
        and len(required_norm) >= 3
        and (student_norm in required_norm or required_norm in student_norm)
    ):
        return 0.85
    if _has_directional_relationship(student_norm, required_norm):
        return 0.6
    return 0.0


def score_basic_requirements(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_certificates = set(student_profile["certificates"])
    job_certificates = set(job_profile["certificate_requirements"])
    cert_ratio = len(student_certificates.intersection(job_certificates)) / max(1, len(job_certificates))
    internship_score = student_profile["capability_scores"].get("internship", 0)
    completeness = student_profile["completeness_score"]
    score = cert_ratio * 55 + internship_score * 0.25 + completeness * 0.2
    evidence = {
        "matched_certificates": sorted(student_certificates.intersection(job_certificates)),
        "missing_certificates": sorted(job_certificates.difference(student_certificates)),
    }
    return clamp_score(score), evidence


def score_professional_skills(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_skills = [str(item).strip() for item in student_profile["skills"] if str(item).strip()]
    required = [str(item).strip() for item in job_profile["skill_requirements"] if str(item).strip()]
    if not required:
        return 50.0, {"matched_skills": [], "related_skills": [], "missing_skills": []}

    matched: set[str] = set()
    related: set[str] = set()
    missing: set[str] = set()
    weighted_coverage = 0.0

    for required_skill in required:
        best_score = 0.0
        best_student_skill = ""
        for student_skill in student_skills:
            similarity = _skill_similarity(student_skill, required_skill)
            if similarity > best_score:
                best_score = similarity
                best_student_skill = student_skill

        weighted_coverage += best_score
        if best_score >= 0.95:
            matched.add(best_student_skill or required_skill)
        elif best_score >= 0.55:
            related.add(f"{best_student_skill}→{required_skill}")
            missing.add(required_skill)
        else:
            missing.add(required_skill)

    coverage_score = weighted_coverage / max(1, len(required)) * 100
    breadth_groups: set[str] = set()
    for skill in student_skills:
        breadth_groups.update(_skill_groups(skill))
    breadth_bonus = min(8.0, len(breadth_groups) * 2.0)
    score = coverage_score + breadth_bonus
    evidence = {
        "matched_skills": sorted(matched),
        "related_skills": sorted(related),
        "missing_skills": sorted(missing),
    }
    return clamp_score(score), evidence


def score_professional_literacy(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_caps = student_profile["capability_scores"]
    job_caps = job_profile["capability_scores"]
    communication_gap = 100 - abs(student_caps.get("communication", 0) - job_caps.get("communication", 0))
    resilience_gap = 100 - abs(student_caps.get("resilience", 0) - job_caps.get("resilience", 0))
    internship_gap = 100 - abs(student_caps.get("internship", 0) - job_caps.get("internship", 0))
    score = (communication_gap + resilience_gap + internship_gap) / 3
    evidence = {
        "communication": student_caps.get("communication", 0),
        "resilience": student_caps.get("resilience", 0),
        "internship": student_caps.get("internship", 0),
    }
    return clamp_score(score), evidence


def score_development_potential(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_caps = student_profile["capability_scores"]
    job_caps = job_profile["capability_scores"]
    learning_gap = 100 - abs(student_caps.get("learning", 0) - job_caps.get("learning", 0))
    innovation_gap = 100 - abs(student_caps.get("innovation", 0) - job_caps.get("innovation", 0))
    completeness = student_profile["completeness_score"]
    score = learning_gap * 0.4 + innovation_gap * 0.4 + completeness * 0.2
    evidence = {
        "learning": student_caps.get("learning", 0),
        "innovation": student_caps.get("innovation", 0),
        "completeness": completeness,
    }
    return clamp_score(score), evidence

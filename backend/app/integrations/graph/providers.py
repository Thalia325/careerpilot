from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from neo4j import GraphDatabase


FAMILY_LABELS = {
    "engineering": "研发开发序列",
    "qa": "测试质量序列",
    "delivery": "交付实施序列",
    "product": "产品序列",
    "operations": "运营增长序列",
    "sales": "销售商务序列",
    "support": "客服支持序列",
    "project": "项目管理序列",
    "management": "管理储备序列",
    "talent": "招聘培训序列",
    "consulting": "咨询顾问序列",
    "legal": "法务知识产权序列",
    "analysis": "研究分析序列",
    "admin": "资料行政序列",
    "language": "语言服务序列",
    "industry_engineering": "行业工程序列",
    "general": "综合岗位序列",
}

FAMILY_DESCRIPTIONS = {
    "engineering": "以开发能力、系统实现和项目交付结果为核心的技术成长路径。",
    "qa": "围绕测试验证、质量保障和交付质量推进的成长路径。",
    "delivery": "围绕客户交付、实施落地和技术支持的成长路径。",
    "product": "围绕需求理解、产品设计和方案统筹的成长路径。",
    "operations": "围绕内容、社区、增长和用户运营的成长路径。",
    "sales": "围绕客户拓展、商务转化和大客户经营的成长路径。",
    "support": "围绕客户服务、问题响应和服务协同的成长路径。",
    "project": "围绕项目推进、招投标协同和项目统筹的成长路径。",
    "management": "围绕储备培养、综合协同和管理助理的成长路径。",
    "talent": "围绕招聘、培训和人才经营的成长路径。",
    "consulting": "围绕咨询分析、方案建议和客户沟通的成长路径。",
    "legal": "围绕法务、合规和知识产权处理的成长路径。",
    "analysis": "围绕研究、统计和分析支持的成长路径。",
    "admin": "围绕资料、档案和流程支持的成长路径。",
    "language": "围绕翻译、语言支持和跨语言沟通的成长路径。",
    "industry_engineering": "围绕垂直行业工程应用和项目落地的成长路径。",
    "general": "围绕通用岗位能力和项目经验积累的成长路径。",
}

FAMILY_TRANSITIONS = {
    "engineering": ["qa", "delivery", "project", "product"],
    "qa": ["engineering", "delivery", "project"],
    "delivery": ["project", "sales", "qa", "operations"],
    "product": ["operations", "project", "sales"],
    "operations": ["product", "sales", "project", "support"],
    "sales": ["operations", "project", "delivery", "product"],
    "support": ["operations", "sales", "project"],
    "project": ["product", "delivery", "sales"],
    "management": ["project", "sales", "operations"],
    "talent": ["consulting", "management", "project"],
    "consulting": ["project", "sales", "management"],
    "legal": ["consulting", "project", "management"],
    "analysis": ["product", "project", "engineering"],
    "admin": ["project", "support", "operations"],
    "language": ["operations", "consulting", "project"],
    "industry_engineering": ["project", "delivery", "qa"],
    "general": ["project", "operations", "sales"],
}

TITLE_METADATA = {
    "Java": {"family": "engineering", "level": 1},
    "C/C++": {"family": "engineering", "level": 1},
    "前端开发": {"family": "engineering", "level": 1},
    "测试工程师": {"family": "qa", "level": 1},
    "软件测试": {"family": "qa", "level": 1},
    "硬件测试": {"family": "qa", "level": 1},
    "质检员": {"family": "qa", "level": 1},
    "质量管理/测试": {"family": "qa", "level": 2},
    "技术支持工程师": {"family": "delivery", "level": 1},
    "实施工程师": {"family": "delivery", "level": 2},
    "产品专员/助理": {"family": "product", "level": 1},
    "APP推广": {"family": "operations", "level": 1},
    "内容审核": {"family": "operations", "level": 1},
    "运营助理/专员": {"family": "operations", "level": 1},
    "社区运营": {"family": "operations", "level": 2},
    "游戏运营": {"family": "operations", "level": 2},
    "游戏推广": {"family": "operations", "level": 1},
    "商务专员": {"family": "sales", "level": 1},
    "销售助理": {"family": "sales", "level": 1},
    "电话销售": {"family": "sales", "level": 1},
    "网络销售": {"family": "sales", "level": 1},
    "广告销售": {"family": "sales", "level": 1},
    "大客户代表": {"family": "sales", "level": 2},
    "销售工程师": {"family": "sales", "level": 2},
    "销售运营": {"family": "sales", "level": 2},
    "BD经理": {"family": "sales", "level": 3},
    "售后客服": {"family": "support", "level": 1},
    "电话客服": {"family": "support", "level": 1},
    "网络客服": {"family": "support", "level": 1},
    "项目专员/助理": {"family": "project", "level": 1},
    "项目招投标": {"family": "project", "level": 2},
    "项目经理/主管": {"family": "project", "level": 3},
    "储备干部": {"family": "management", "level": 1},
    "管培生/储备干部": {"family": "management", "level": 1},
    "储备经理人": {"family": "management", "level": 2},
    "总助/CEO助理/董事长助理": {"family": "management", "level": 3},
    "招聘专员/助理": {"family": "talent", "level": 1},
    "培训师": {"family": "talent", "level": 2},
    "猎头顾问": {"family": "talent", "level": 2},
    "咨询顾问": {"family": "consulting", "level": 2},
    "法务专员/助理": {"family": "legal", "level": 1},
    "律师助理": {"family": "legal", "level": 1},
    "知识产权/专利代理": {"family": "legal", "level": 2},
    "律师": {"family": "legal", "level": 3},
    "统计员": {"family": "analysis", "level": 1},
    "科研人员": {"family": "analysis", "level": 2},
    "档案管理": {"family": "admin", "level": 1},
    "资料管理": {"family": "admin", "level": 1},
    "英语翻译": {"family": "language", "level": 1},
    "日语翻译": {"family": "language", "level": 1},
    "风电工程师": {"family": "industry_engineering", "level": 2},
}


class BaseGraphProvider(ABC):
    @abstractmethod
    async def load_seed(self, seed_data: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_job_profile(self, job_profile: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def query_job(self, job_code: str) -> dict[str, Any]:
        raise NotImplementedError


def _dedupe_paths(paths: list[list[str]]) -> list[list[str]]:
    result: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for path in paths:
        normalized = tuple(item.strip() for item in path if str(item).strip())
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(list(normalized))
    return result


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


class MockGraphProvider(BaseGraphProvider):
    def __init__(self) -> None:
        self.seed_jobs: dict[str, dict[str, Any]] = {}
        self.seed_data: dict[str, Any] = {}
        self.generated_profiles: dict[str, dict[str, Any]] = {}
        self.generated_jobs: dict[str, dict[str, Any]] = {}

    async def load_seed(self, seed_data: dict[str, Any]) -> None:
        self.seed_data = seed_data.copy()
        self.seed_jobs = {
            code: {
                "title": str(item.get("title", "")).strip(),
                "description": str(item.get("description", "")).strip(),
                "skills": _unique_strings(list(item.get("skills", []) or [])),
                "promotions": _dedupe_paths(list(item.get("promotions", []) or [])),
                "transitions": _dedupe_paths(list(item.get("transitions", []) or [])),
            }
            for code, item in seed_data.get("jobs", {}).items()
        }

    async def upsert_job_profile(self, job_profile: dict[str, Any]) -> None:
        job_code = str(job_profile.get("job_code", "")).strip()
        title = str(job_profile.get("title", "")).strip()
        if not job_code or not title:
            return

        self.generated_profiles[job_code] = {
            "job_code": job_code,
            "title": title,
            "description": str(job_profile.get("summary") or job_profile.get("description") or "").strip(),
            "skills": _unique_strings(list(job_profile.get("skill_requirements", []) or [])),
        }
        self._rebuild_generated_jobs()

    async def query_job(self, job_code: str) -> dict[str, Any]:
        if job_code in self.generated_jobs:
            return self._build_response(job_code, self.generated_jobs[job_code])
        if job_code in self.seed_jobs:
            return self._build_seed_response(job_code, self.seed_jobs[job_code])
        return self._build_response(
            job_code,
            {
                "title": "",
                "description": "",
                "skills": [],
                "promotions": [],
                "transitions": [],
                "vertical_paths": [],
                "transition_clusters": [],
            },
        )

    def _rebuild_generated_jobs(self) -> None:
        titles_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        enriched_items: list[tuple[str, dict[str, Any]]] = []
        for job_code, item in self.generated_profiles.items():
            meta = self._resolve_title_meta(item["title"])
            enriched = {**item, **meta}
            titles_by_family[meta["family"]].append(enriched)
            enriched_items.append((job_code, enriched))

        for family_items in titles_by_family.values():
            family_items.sort(key=lambda candidate: (candidate["level"], candidate["title"]))

        rebuilt: dict[str, dict[str, Any]] = {}
        for job_code, item in enriched_items:
            promotions = self._build_promotion_paths(item, titles_by_family)
            transitions = self._build_transition_paths(item, titles_by_family)
            rebuilt[job_code] = {
                "title": item["title"],
                "description": item["description"] or self._default_description(item),
                "skills": item["skills"],
                "promotions": promotions,
                "transitions": transitions,
                "vertical_paths": self._build_vertical_paths(item, titles_by_family),
                "transition_clusters": self._build_transition_clusters(item, transitions),
            }

        self.generated_jobs = rebuilt

    def _resolve_title_meta(self, title: str) -> dict[str, Any]:
        if title in TITLE_METADATA:
            return TITLE_METADATA[title].copy()

        lowered = title.lower()
        if "java" in lowered or "c/c++" in lowered or "开发" in title:
            return {"family": "engineering", "level": 1}
        if "测试" in title or "质检" in title or "质量" in title:
            return {"family": "qa", "level": 1}
        if "实施" in title or "技术支持" in title:
            return {"family": "delivery", "level": 1}
        if "产品" in title:
            return {"family": "product", "level": 1}
        if "运营" in title or "推广" in title or "审核" in title:
            return {"family": "operations", "level": 1}
        if "销售" in title or "商务" in title or "客户代表" in title or "bd" in lowered:
            return {"family": "sales", "level": 1}
        if "客服" in title:
            return {"family": "support", "level": 1}
        if "项目" in title:
            return {"family": "project", "level": 1}
        if "储备" in title or "总助" in title or "助理" in title:
            return {"family": "management", "level": 1}
        if "招聘" in title or "猎头" in title or "培训" in title:
            return {"family": "talent", "level": 1}
        if "咨询" in title:
            return {"family": "consulting", "level": 1}
        if "法务" in title or "律师" in title or "专利" in title:
            return {"family": "legal", "level": 1}
        if "统计" in title or "科研" in title:
            return {"family": "analysis", "level": 1}
        if "档案" in title or "资料" in title:
            return {"family": "admin", "level": 1}
        if "翻译" in title:
            return {"family": "language", "level": 1}
        if "工程师" in title:
            return {"family": "industry_engineering", "level": 1}
        return {"family": "general", "level": 1}

    def _default_description(self, item: dict[str, Any]) -> str:
        family_label = FAMILY_LABELS.get(item["family"], "岗位发展")
        return f"{item['title']} 属于{family_label}，建议结合项目经历和岗位核心技能持续积累。"

    def _build_promotion_paths(
        self,
        item: dict[str, Any],
        titles_by_family: dict[str, list[dict[str, Any]]],
    ) -> list[list[str]]:
        family_items = titles_by_family.get(item["family"], [])
        higher = [candidate for candidate in family_items if candidate["level"] > item["level"]]
        if not higher:
            return []

        next_level = min(candidate["level"] for candidate in higher)
        next_candidates = [candidate for candidate in higher if candidate["level"] == next_level][:2]
        paths: list[list[str]] = []
        for candidate in next_candidates:
            path = [item["title"], candidate["title"]]
            follow_ups = [entry for entry in higher if entry["level"] > candidate["level"]]
            if follow_ups:
                follow_up = sorted(follow_ups, key=lambda entry: (entry["level"], entry["title"]))[0]
                if follow_up["title"] not in path:
                    path.append(follow_up["title"])
            paths.append(path)
        return _dedupe_paths(paths)

    def _build_transition_paths(
        self,
        item: dict[str, Any],
        titles_by_family: dict[str, list[dict[str, Any]]],
    ) -> list[list[str]]:
        targets: list[list[str]] = []
        for family in FAMILY_TRANSITIONS.get(item["family"], []):
            target = self._pick_transition_target(item, titles_by_family.get(family, []))
            if target:
                targets.append([item["title"], target["title"]])
            if len(targets) >= 4:
                break

        if not targets:
            same_level = [
                candidate
                for candidate in titles_by_family.get(item["family"], [])
                if candidate["title"] != item["title"] and candidate["level"] == item["level"]
            ]
            targets.extend([[item["title"], candidate["title"]] for candidate in same_level[:2]])
        return _dedupe_paths(targets)

    def _pick_transition_target(
        self,
        item: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not candidates:
            return None

        desired_levels = [
            item["level"],
            item["level"] + 1,
            max(1, item["level"] - 1),
            2,
            1,
            3,
        ]
        for level in desired_levels:
            for candidate in candidates:
                if candidate["title"] == item["title"]:
                    continue
                if candidate["level"] == level:
                    return candidate
        return next((candidate for candidate in candidates if candidate["title"] != item["title"]), None)

    def _build_vertical_paths(
        self,
        item: dict[str, Any],
        titles_by_family: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        family_items = titles_by_family.get(item["family"], [])
        if len(family_items) < 2:
            return []
        return [
            {
                "name": FAMILY_LABELS.get(item["family"], "岗位成长路径"),
                "description": FAMILY_DESCRIPTIONS.get(item["family"], ""),
                "levels": [candidate["title"] for candidate in family_items],
            }
        ]

    def _build_transition_clusters(
        self,
        item: dict[str, Any],
        transition_paths: list[list[str]],
    ) -> list[dict[str, Any]]:
        if not transition_paths:
            return []

        family_label = FAMILY_LABELS.get(item["family"], "岗位")
        clusters = [
            {
                "name": f"{family_label}关联转岗",
                "description": f"围绕 {item['title']} 所在序列可延展的相近岗位方向。",
                "related_paths": transition_paths[:3],
            }
        ]

        first_target_title = transition_paths[0][-1]
        target_meta = self._resolve_title_meta(first_target_title)
        target_label = FAMILY_LABELS.get(target_meta["family"], "关联序列")
        clusters.append(
            {
                "name": f"{family_label} -> {target_label}",
                "description": f"从 {item['title']} 切换到 {target_label} 时，重点关注通用能力和岗位技能迁移。",
                "related_paths": transition_paths[:2],
            }
        )
        return clusters

    def _build_response(self, job_code: str, item: dict[str, Any]) -> dict[str, Any]:
        title = item.get("title", "")
        skills = list(item.get("skills", []) or [])
        promotions = _dedupe_paths(list(item.get("promotions", []) or []))
        transitions = _dedupe_paths(list(item.get("transitions", []) or []))
        upstream = [path[0] for path in promotions if path] + [path[0] for path in transitions if path]
        downstream = [path[-1] for path in promotions if path] + [path[-1] for path in transitions if path]
        adjacent_skill_gaps: dict[str, list[str]] = {}
        for path in transitions:
            target_title = path[-1]
            target_job = next(
                (job for job in self.generated_jobs.values() if job.get("title") == target_title),
                None,
            )
            target_skills = set(target_job.get("skills", [])) if target_job else set()
            adjacent_skill_gaps[target_title] = sorted(target_skills.difference(skills))

        return {
            "job_code": job_code,
            "title": title,
            "description": item.get("description", ""),
            "promotion_paths": promotions,
            "transition_paths": transitions,
            "upstream_jobs": sorted(set(upstream)),
            "downstream_jobs": sorted(set(downstream)),
            "required_skills": skills,
            "adjacent_skill_gaps": adjacent_skill_gaps,
            "vertical_paths": list(item.get("vertical_paths", []) or []),
            "transition_clusters": list(item.get("transition_clusters", []) or []),
        }

    def _build_seed_response(self, job_code: str, item: dict[str, Any]) -> dict[str, Any]:
        title = item.get("title", "")
        response = self._build_response(
            job_code,
            {
                **item,
                "vertical_paths": [
                    {
                        "name": name,
                        "description": info.get("description", ""),
                        "levels": info.get("levels", []),
                    }
                    for name, info in self.seed_data.get("vertical_paths", {}).items()
                    if title in info.get("jobs", [])
                ],
                "transition_clusters": [
                    {
                        "name": name,
                        "description": info.get("description", ""),
                        "related_paths": info.get("paths", []),
                    }
                    for name, info in self.seed_data.get("transition_clusters", {}).items()
                    if any(title in path for path in info.get("paths", []))
                ],
            },
        )
        return response


class Neo4jGraphProvider(BaseGraphProvider):
    def __init__(self, uri: str, username: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.mock = MockGraphProvider()

    async def load_seed(self, seed_data: dict[str, Any]) -> None:
        await self.mock.load_seed(seed_data)

    async def upsert_job_profile(self, job_profile: dict[str, Any]) -> None:
        await self.mock.upsert_job_profile(job_profile)

    async def query_job(self, job_code: str) -> dict[str, Any]:
        return await self.mock.query_job(job_code)

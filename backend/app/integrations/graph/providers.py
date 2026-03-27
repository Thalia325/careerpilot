from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from neo4j import GraphDatabase


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


class MockGraphProvider(BaseGraphProvider):
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}

    async def load_seed(self, seed_data: dict[str, Any]) -> None:
        self.jobs = seed_data.get("jobs", {}).copy()

    async def upsert_job_profile(self, job_profile: dict[str, Any]) -> None:
        existing = self.jobs.get(job_profile["job_code"], {})
        self.jobs[job_profile["job_code"]] = {
            "title": job_profile["title"],
            "skills": job_profile.get("skill_requirements", existing.get("skills", [])),
            "promotions": existing.get("promotions", []),
            "transitions": existing.get("transitions", []),
        }

    async def query_job(self, job_code: str) -> dict[str, Any]:
        item = self.jobs.get(job_code, {})
        title = item.get("title", "")
        skills = item.get("skills", [])
        promotions = item.get("promotions", [])
        transitions = item.get("transitions", [])
        upstream = [path[0] for path in promotions if path] + [path[0] for path in transitions if path]
        downstream = [path[-1] for path in promotions if path] + [path[-1] for path in transitions if path]
        adjacent_skill_gaps: dict[str, list[str]] = {}
        for path in transitions:
            if len(path) >= 2:
                target_title = path[-1]
                target_job = next((job for job in self.jobs.values() if job.get("title") == target_title), None)
                target_skills = set(target_job.get("skills", [])) if target_job else set()
                adjacent_skill_gaps[target_title] = sorted(target_skills.difference(skills))
        return {
            "job_code": job_code,
            "title": title,
            "promotion_paths": promotions,
            "transition_paths": transitions,
            "upstream_jobs": sorted(set(upstream)),
            "downstream_jobs": sorted(set(downstream)),
            "required_skills": skills,
            "adjacent_skill_gaps": adjacent_skill_gaps,
        }


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


from __future__ import annotations

from app.integrations.graph.providers import BaseGraphProvider


class GraphQueryService:
    def __init__(self, graph_provider: BaseGraphProvider) -> None:
        self.graph_provider = graph_provider

    async def query_job(self, job_code: str) -> dict:
        return await self.graph_provider.query_job(job_code)


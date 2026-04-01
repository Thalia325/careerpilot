from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx


class BaseRAGProvider(ABC):
    @abstractmethod
    async def index_document(self, title: str, content: str, metadata: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockRAGProvider(BaseRAGProvider):
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def index_document(self, title: str, content: str, metadata: dict[str, Any]) -> None:
        self.documents.append({"title": title, "content": content, "metadata": metadata})

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()
        ranked = sorted(
            self.documents,
            key=lambda item: item["content"].lower().count(query_lower) + item["title"].lower().count(query_lower),
            reverse=True,
        )
        return ranked[:top_k]


class RAGFlowProvider(BaseRAGProvider):
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.mock = MockRAGProvider()

    async def index_document(self, title: str, content: str, metadata: dict[str, Any]) -> None:
        if not self.base_url or not self.api_key:
            await self.mock.index_document(title, content, metadata)
            return
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{self.base_url}/documents",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"title": title, "content": content, "metadata": metadata},
            )

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.base_url or not self.api_key:
            return await self.mock.search(query, top_k)
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"query": query, "top_k": top_k},
            )
            response.raise_for_status()
            return response.json().get("items", [])


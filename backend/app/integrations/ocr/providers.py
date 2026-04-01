from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx


class BaseOCRProvider(ABC):
    @abstractmethod
    async def parse_document(
        self,
        file_name: str,
        content_bytes: bytes,
        document_type: str = "resume",
        raw_text: Optional[str] = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


def _extract_keywords(text: str, candidates: list[str]) -> list[str]:
    return [item for item in candidates if item.lower() in text.lower()]


def _extract_gpa(text: str) -> Optional[float]:
    match = re.search(r"(GPA|绩点)[:： ]*([0-9]\.?[0-9]*)", text, flags=re.IGNORECASE)
    return float(match.group(2)) if match else None


class MockOCRProvider(BaseOCRProvider):
    SKILL_CANDIDATES = [
        "Python",
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "FastAPI",
        "PostgreSQL",
        "Redis",
        "SQL",
        "Docker",
        "Linux",
        "Figma",
        "机器学习",
        "深度学习",
        "PyTorch",
        "Excel",
        "数据可视化",
    ]
    CERTIFICATE_CANDIDATES = [
        "英语四级",
        "英语六级",
        "软件设计师",
        "计算机二级",
        "数据分析师证书",
        "产品经理证书",
        "人工智能工程师",
    ]

    async def parse_document(
        self,
        file_name: str,
        content_bytes: bytes,
        document_type: str = "resume",
        raw_text: Optional[str] = None,
    ) -> dict[str, Any]:
        text = raw_text or content_bytes.decode("utf-8", errors="ignore")
        if not text.strip():
            text = (
                "姓名 张三\n"
                "专业 软件工程\n"
                "技能 Python FastAPI SQL React TypeScript\n"
                "项目 校园就业平台、职业规划系统\n"
                "实习 Web 开发实习生\n"
                "证书 英语四级 计算机二级\n"
                "GPA 3.7\n"
            )
        skills = _extract_keywords(text, self.SKILL_CANDIDATES)
        certificates = _extract_keywords(text, self.CERTIFICATE_CANDIDATES)
        projects = re.findall(r"(项目|Project)[:： ]*(.+)", text)
        internships = re.findall(r"(实习|Internship)[:： ]*(.+)", text)
        structured = {
            "document_type": document_type,
            "name": re.search(r"姓名[:： ]*([^\n]+)", text).group(1).strip()
            if re.search(r"姓名[:： ]*([^\n]+)", text)
            else "未知学生",
            "major": re.search(r"(专业|Major)[:： ]*([^\n]+)", text).group(2).strip()
            if re.search(r"(专业|Major)[:： ]*([^\n]+)", text)
            else "",
            "skills": skills,
            "certificates": certificates,
            "projects": [item[1].strip() for item in projects],
            "internships": [item[1].strip() for item in internships],
            "gpa": _extract_gpa(text),
        }
        layout_blocks = [
            {"section": "header", "text": structured["name"]},
            {"section": "skills", "text": ", ".join(skills)},
            {"section": "certificates", "text": ", ".join(certificates)},
            {"section": "experience", "text": "; ".join(structured["internships"] + structured["projects"])},
        ]
        return {
            "raw_text": text,
            "layout_blocks": layout_blocks,
            "structured_json": structured,
        }


class PaddleOCRProvider(BaseOCRProvider):
    def __init__(self, service_url: str) -> None:
        self.service_url = service_url

    async def parse_document(
        self,
        file_name: str,
        content_bytes: bytes,
        document_type: str = "resume",
        raw_text: Optional[str] = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.service_url,
                files={"file": (file_name, content_bytes)},
                data={"document_type": document_type, "raw_text": raw_text or ""},
            )
            response.raise_for_status()
            return response.json()

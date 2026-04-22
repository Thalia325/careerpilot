from pydantic import BaseModel, Field


class KnowledgeHit(BaseModel):
    title: str
    snippet: str
    doc_type: str = ""
    source_ref: str = ""
    score: float | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    knowledge_hits: list[KnowledgeHit] = Field(default_factory=list)


class KnowledgeSearchResponse(BaseModel):
    query: str
    items: list[KnowledgeHit] = Field(default_factory=list)


class GreetingResponse(BaseModel):
    greeting: str
    subline: str

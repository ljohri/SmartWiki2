from __future__ import annotations

from pydantic import BaseModel, Field


class QueryAnswer(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    uncertainty: str | None = None


class ClassificationResult(BaseModel):
    page_type: str
    confidence: float
    rationale: str

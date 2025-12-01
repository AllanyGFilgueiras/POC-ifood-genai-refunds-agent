from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel, Field


@dataclass
class KnowledgeDocument:
    id: str
    content: str
    categoria: str
    fonte: str
    pergunta: str
    resposta: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)


class RetrievedSource(BaseModel):
    id: str
    fonte: str
    categoria: str
    pergunta: str
    resposta: str
    score: Optional[float] = None


class SimilarityScore(BaseModel):
    source_id: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    is_fallback: bool
    sources: List[RetrievedSource]
    similarity_scores: List[SimilarityScore] = Field(default_factory=list)

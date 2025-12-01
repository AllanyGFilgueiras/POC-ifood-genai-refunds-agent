from __future__ import annotations

from typing import List, Tuple

from langchain_core.documents import Document

from backend.app.core.config import get_settings
from backend.app.models.schemas import ChatResponse, RetrievedSource, SimilarityScore
from backend.app.rag.llm_client import FALLBACK_MESSAGE, LLMClient
from backend.app.rag.retriever import VectorStoreRetriever, RetrievalError


OUT_OF_SCOPE_KEYWORDS = ["previsão do tempo", "clima", "tempo amanhã", "meteorologia"]


def classify_scope(question: str) -> str:
    normalized = question.lower()
    for keyword in OUT_OF_SCOPE_KEYWORDS:
        if keyword in normalized:
            return "FORA_DO_ESCOPO"
    return "OPERACIONAL"


class AgentService:
    def __init__(
        self,
        retriever: VectorStoreRetriever | None = None,
        llm_client: LLMClient | None = None,
        use_fake_override: bool | None = None,
    ):
        self.settings = get_settings()
        self.retriever = retriever or VectorStoreRetriever()
        try:
            from langchain_community.embeddings import FakeEmbeddings
        except Exception:  # pragma: no cover - fallback sem dependência
            FakeEmbeddings = None  # type: ignore
        has_fake_embeddings = (
            FakeEmbeddings is not None and hasattr(self.retriever, "embeddings") and isinstance(self.retriever.embeddings, FakeEmbeddings)
        )
        self.use_fake = use_fake_override if use_fake_override is not None else (
            self.settings.use_fake_embeddings or has_fake_embeddings
        )
        self.llm_client = llm_client or LLMClient()

    def _to_sources(self, docs_with_scores: List[Tuple[Document, float]]) -> List[RetrievedSource]:
        sources: List[RetrievedSource] = []
        for doc, score in docs_with_scores:
            metadata = doc.metadata
            sources.append(
                RetrievedSource(
                    id=str(metadata.get("id")),
                    fonte=str(metadata.get("fonte")),
                    categoria=str(metadata.get("categoria")),
                    pergunta=str(metadata.get("pergunta")),
                    resposta=str(metadata.get("resposta")),
                    score=float(score),
                )
            )
        return sources

    def answer(self, question: str) -> ChatResponse:
        intent = classify_scope(question)
        if intent == "FORA_DO_ESCOPO":
            return ChatResponse(answer=FALLBACK_MESSAGE, is_fallback=True, sources=[], similarity_scores=[])

        try:
            docs_with_scores = self.retriever.search(question, k=self.settings.retrieval_k)
        except RetrievalError:
            return ChatResponse(answer=FALLBACK_MESSAGE, is_fallback=True, sources=[], similarity_scores=[])
        sources = self._to_sources(docs_with_scores)
        if not sources:
            return ChatResponse(answer=FALLBACK_MESSAGE, is_fallback=True, sources=[], similarity_scores=[])

        top_score = sources[0].score or 0.0
        similarity_scores = [
            SimilarityScore(source_id=src.id, score=src.score or 0.0) for src in sources if src.score is not None
        ]

        overlaps = [_has_question_overlap(question, src) for src in sources]
        overlap_ok = any(overlaps)

        # Heurística para modo fake: se threshold for baixo (modo demo), prioriza responder com as fontes;
        # se threshold alto, mantém fallback salvo quando não há sobreposição.
        if self.use_fake and self.settings.similarity_threshold <= 0.1:
            answer = self.llm_client.generate(question=question, sources=sources)
            return ChatResponse(
                answer=answer, is_fallback=False, sources=sources, similarity_scores=similarity_scores
            )

        if self.use_fake:
            if not overlap_ok:
                return ChatResponse(
                    answer=FALLBACK_MESSAGE, is_fallback=True, sources=sources, similarity_scores=similarity_scores
                )
            top_score = max(top_score, 1.0)

        if top_score < self.settings.similarity_threshold:
            return ChatResponse(
                answer=FALLBACK_MESSAGE, is_fallback=True, sources=sources, similarity_scores=similarity_scores
            )

        answer = self.llm_client.generate(question=question, sources=sources)
        return ChatResponse(answer=answer, is_fallback=False, sources=sources, similarity_scores=similarity_scores)


def _has_question_overlap(question: str, source: RetrievedSource) -> bool:
    """Heurística simples de sobreposição para evitar respostas irrelevantes no modo fake."""
    import re

    def _tokens(text: str) -> set[str]:
        return {
            re.sub(r"[^a-z0-9áàâãçéêíóôõúü]", "", raw)
            for raw in text.lower().split()
            if len(raw) > 2
        }

    q_tokens = _tokens(question)
    doc_blob = " ".join([source.pergunta, source.resposta, source.categoria, source.fonte]).lower()
    d_tokens = _tokens(doc_blob)
    return len(q_tokens.intersection(d_tokens)) > 0

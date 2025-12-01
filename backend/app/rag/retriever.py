from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from backend.app.core.config import get_settings
from backend.app.rag.ingestion import build_embeddings


class RetrievalError(RuntimeError):
    pass


class VectorStoreRetriever:
    def __init__(self, vector_store: FAISS | None = None, embeddings: Embeddings | None = None):
        self.settings = get_settings()
        self.embeddings = embeddings or build_embeddings(self.settings)
        self.vector_store = vector_store or self._load_vector_store(self.settings.vector_store_path)

    def _load_vector_store(self, path: Path) -> FAISS:
        if not path.exists():
            raise RetrievalError(
                f"Vector store não encontrado em {path}. Rode a ingestão antes de fazer queries."
            )
        return FAISS.load_local(str(path), self.embeddings, allow_dangerous_deserialization=True)

    def search(self, query: str, k: int | None = None) -> List[Tuple[Document, float]]:
        top_k = k or self.settings.retrieval_k
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
        # Quando em modo fake ou embeddings de teste, os scores não representam similaridade real; normaliza para 0.0
        from langchain_community.embeddings import (
            FakeEmbeddings,
        )  # local import para evitar dependência dura

        if self.settings.use_fake_embeddings or isinstance(self.embeddings, FakeEmbeddings):
            docs_and_scores = [(doc, 0.0) for doc, _ in docs_and_scores]
        return docs_and_scores

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import FakeEmbeddings
from langchain_openai import OpenAIEmbeddings

from backend.app.core.config import get_settings
from backend.app.models.schemas import KnowledgeDocument


def build_embeddings(settings) -> Embeddings:
    # Usa embeddings fake quando solicitado ou quando não há chave OpenAI definida
    if settings.use_fake_embeddings or not settings.openai_api_key:
        return FakeEmbeddings(size=1536)
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)


def csv_to_documents(csv_path: Path) -> List[KnowledgeDocument]:
    documents: List[KnowledgeDocument] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            categoria = row.get("categoria", "").strip()
            pergunta = row.get("pergunta", "").strip()
            resposta = row.get("resposta", "").strip()
            fonte = row.get("fonte", "").strip()
            content = (
                f"[FONTE: {fonte}]\n"
                f"[CATEGORIA: {categoria}]\n"
                f"CENÁRIO: {pergunta}\n"
                f"AÇÃO RECOMENDADA: {resposta}"
            )
            doc_id = f"doc-{idx+1}"
            documents.append(
                KnowledgeDocument(
                    id=doc_id,
                    content=content,
                    categoria=categoria,
                    fonte=fonte,
                    pergunta=pergunta,
                    resposta=resposta,
                )
            )
    return documents


def knowledge_documents_to_langchain_docs(docs: Iterable[KnowledgeDocument]) -> List[Document]:
    langchain_docs: List[Document] = []
    for doc in docs:
        metadata = {
            "id": doc.id,
            "categoria": doc.categoria,
            "fonte": doc.fonte,
            "pergunta": doc.pergunta,
            "resposta": doc.resposta,
        }
        langchain_docs.append(Document(page_content=doc.content, metadata=metadata))
    return langchain_docs


def ingest_csv_to_vector_store(csv_path: Path | None = None, persist_dir: Path | None = None) -> FAISS:
    settings = get_settings()
    csv_file = csv_path or settings.csv_path
    vector_dir = persist_dir or settings.vector_store_path
    docs = csv_to_documents(csv_file)
    langchain_docs = knowledge_documents_to_langchain_docs(docs)
    embeddings = build_embeddings(settings)
    vector_store = FAISS.from_documents(langchain_docs, embeddings)
    vector_dir.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(vector_dir))
    return vector_store


if __name__ == "__main__":
    ingest_csv_to_vector_store()
    print("Ingestão concluída com sucesso.")

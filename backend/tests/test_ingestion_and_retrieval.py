from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import FAISS

from backend.app import main
from backend.app.api.routes import get_agent
from backend.app.core import config
from backend.app.rag.agent import AgentService
from backend.app.rag.ingestion import ingest_csv_to_vector_store
from backend.app.rag.llm_client import FALLBACK_MESSAGE
from backend.app.rag.retriever import VectorStoreRetriever


BUSINESS_CSV = """categoria,pergunta,resposta,fonte
reembolso,Pedido saiu para entrega. Cliente pede reembolso.,Reembolsar apenas se falha do restaurante/entregador. Caso desistência, avaliar exceções.,Política Reembolso Saída
cancelamento,Falta de ingrediente. Cliente quer saber se reembolso é automático.,Reembolso automático por falha do restaurante.,Política Cancelamento Ingrediente
financeiro,Cliente foi cobrado após cancelamento.,Validar estorno e abrir ticket financeiro se não constar devolução.,Fluxo Financeiro Cancelamento
fraude,Tentativa de múltiplos reembolsos seguidos.,Sinalizar antifraude e bloquear até validação.,Fluxo Segurança
"""


class EchoLLM:
    def generate(self, question: str, sources):
        return f"Resposta baseada em {len(list(sources))} fontes para: {question}"


def prepare_vector_store(tmp_path: Path, csv_content: str = BUSINESS_CSV) -> Path:
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    config.get_settings.cache_clear()
    env = {
        "AGENT_USE_FAKE_EMBEDDINGS": "true",
        "AGENT_CSV_PATH": str(csv_path),
        "AGENT_VECTOR_STORE_PATH": str(tmp_path / "vector_store"),
        "AGENT_SIMILARITY_THRESHOLD": "0.0",
    }
    for key, value in env.items():
        os.environ[key] = value
    ingest_csv_to_vector_store(csv_path=csv_path, persist_dir=tmp_path / "vector_store")
    return tmp_path / "vector_store"


def make_retriever(vector_dir: Path) -> VectorStoreRetriever:
    return VectorStoreRetriever(
        vector_store=FAISS.load_local(
            str(vector_dir), FakeEmbeddings(size=1536), allow_dangerous_deserialization=True
        ),
        embeddings=FakeEmbeddings(size=1536),
    )


def test_ingestion_builds_documents(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    assert (vector_dir / "index.faiss").exists()


def test_retrieval_returns_best_match(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    retriever = make_retriever(vector_dir)
    docs = retriever.search("reembolso", k=1)
    assert docs
    doc, score = docs[0]
    assert doc.page_content
    assert score >= 0


def test_api_fallback_out_of_scope(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    retriever = make_retriever(vector_dir)
    agent = AgentService(retriever=retriever, llm_client=EchoLLM())
    app = main.app
    app.dependency_overrides[get_agent] = lambda: agent
    client = TestClient(app)
    response = client.post("/api/chat", json={"question": "Como está a previsão do tempo amanhã?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_fallback"] is True
    assert FALLBACK_MESSAGE in data["answer"]


def test_agent_returns_fallback_when_no_documents():
    class EmptyRetriever:
        def search(self, query: str, k: int | None = None):
            return []

    agent = AgentService(retriever=EmptyRetriever(), llm_client=EchoLLM(), use_fake_override=True)
    response = agent.answer("Pergunta não coberta")
    assert response.is_fallback is True
    assert FALLBACK_MESSAGE in response.answer


def test_business_scenarios_reembolso_saida(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    os.environ["AGENT_USE_FAKE_EMBEDDINGS"] = "1"
    os.environ["AGENT_SIMILARITY_THRESHOLD"] = "0.0"
    config.get_settings.cache_clear()
    retriever = make_retriever(vector_dir)
    agent = AgentService(retriever=retriever, llm_client=EchoLLM(), use_fake_override=True)
    response = agent.answer("Pedido saiu para entrega, cliente quer reembolso")
    assert response.is_fallback is False
    assert any("reembolso" in s.categoria for s in response.sources)


def test_business_scenarios_cancelamento_falta_ingrediente(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    os.environ["AGENT_USE_FAKE_EMBEDDINGS"] = "1"
    os.environ["AGENT_SIMILARITY_THRESHOLD"] = "0.0"
    config.get_settings.cache_clear()
    retriever = make_retriever(vector_dir)
    agent = AgentService(retriever=retriever, llm_client=EchoLLM(), use_fake_override=True)
    response = agent.answer("Restaurante cancelou por falta de ingrediente. Reembolso é automático?")
    assert response.is_fallback is False
    assert any("cancelamento" in s.categoria for s in response.sources)


def test_business_scenarios_cobranca_apos_cancelamento(tmp_path: Path):
    vector_dir = prepare_vector_store(tmp_path)
    os.environ["AGENT_USE_FAKE_EMBEDDINGS"] = "1"
    os.environ["AGENT_SIMILARITY_THRESHOLD"] = "0.0"
    config.get_settings.cache_clear()
    retriever = make_retriever(vector_dir)
    agent = AgentService(retriever=retriever, llm_client=EchoLLM(), use_fake_override=True)
    response = agent.answer("Cliente foi cobrado depois do cancelamento, o que fazer?")
    assert response.is_fallback is False
    assert any("financeiro" in s.categoria for s in response.sources)


def test_threshold_triggers_fallback(tmp_path: Path):
    # Força threshold alto; como scores fake são zerados na retriever, cairá em fallback
    vector_dir = prepare_vector_store(tmp_path)
    os.environ["AGENT_USE_FAKE_EMBEDDINGS"] = "true"
    os.environ["AGENT_SIMILARITY_THRESHOLD"] = "0.9"
    config.get_settings.cache_clear()
    retriever = make_retriever(vector_dir)
    agent = AgentService(retriever=retriever, llm_client=EchoLLM())
    response = agent.answer("Pergunta genérica sem match")
    assert response.is_fallback is True
    assert FALLBACK_MESSAGE in response.answer

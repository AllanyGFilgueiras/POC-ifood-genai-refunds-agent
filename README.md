# 🍔 iFood GenAI Refunds Agent

POC educativa de agente interno (reembolso/cancelamento/cobrança) usando RAG em CSV. Foco: anti-alucinação, transparência de fontes e fallback seguro.

> ⚠️ **Aviso**: base simulada, não representa políticas oficiais do iFood. Uso educacional/portfólio.

## ✨ Visão Rápida
- 🔍 Sempre consulta a base antes de responder; cita fontes.
- 🛡️ Anti-alucinação + fallback seguro quando sem confiança.
- 🖥️ Stack: FastAPI + LangChain/FAISS + React/Vite/TS.
- ✅ Qualidade: lint/test em CI (backend e frontend).

## 🧭 Arquitetura
```
CSV -> Ingestão (CLI) -> Embeddings -> FAISS
                                 |
User -> Frontend (React) -> FastAPI (/api/chat)
                           |-> Retriever (FAISS)
                           |-> Prompt anti-alucinação
                           |-> Fallback seguro
                     <- Resposta + fontes + scores
```
- Ingestão: `python -m backend.app.rag.ingestion` lê `data/base_conhecimento_ifood_genai-exemplo.csv` e grava FAISS.
- RAG: busca top-k com `similarity_threshold`; offline usa heurística para evitar respostas irrelevantes.
- API: `/api/chat` retorna `answer`, `is_fallback`, `sources`, `similarity_scores`.
- Frontend: SPA com chat, badge de fallback e painel de fontes.

## 🛠️ Decisões Técnicas
- LangChain + FAISS local (sem dependência paga).
- FastAPI com Pydantic/Mypy; testes com pytest.
- React + Vite + Vitest/RTL; ESLint/Prettier.
- Anti-alucinação: prompt rígido, fallback em score baixo ou fora de escopo.

## 🧪 Como Rodar
Pré-requisitos: Python 3.11+, Node 18+. Chave OpenAI opcional (fake embeddings disponíveis).
```bash
# Backend
pip install -e .[dev]
export AGENT_USE_FAKE_EMBEDDINGS=true   # ou AGENT_OPENAI_API_KEY=...
python -m backend.app.rag.ingestion
uvicorn backend.app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
VITE_API_URL=http://localhost:8000/api npm run dev
```

## ✅ Testes
- Backend: `pytest` (usa FakeEmbeddings; offline seguro).
- Frontend: `cd frontend && npm test`.
- Cenários manuais: reembolso após saída, falta de ingrediente, cobrança pós-cancelamento, fora de escopo, caso ambíguo (fallback).

## 🛡️ Fallback & Anti-Alucinação
- `AGENT_SIMILARITY_THRESHOLD` (default 0.6). Offline: use `0.0` para demo ou >0.5 para rigor.
- Sem docs, fora de escopo ou baixa confiança → fallback:  
  “Não encontrei informação suficiente na base para responder com segurança. Sugiro abrir um ticket interno ou consultar a política oficial.”
- Prompt exige citar fonte e proíbe criar regra não existente.

## 🌐 API (POST /api/chat)
Payload:
```json
{ "question": "string" }
```
Resposta:
```json
{
  "answer": "string",
  "is_fallback": true,
  "sources": [{ "id": "...", "fonte": "...", "categoria": "...", "pergunta": "...", "resposta": "...", "score": 0.0 }],
  "similarity_scores": [{ "source_id": "...", "score": 0.0 }]
}
```

## 🔧 Variáveis de Ambiente
- `AGENT_OPENAI_API_KEY` (ou `OPENAI_API_KEY`), `AGENT_USE_FAKE_EMBEDDINGS`.
- `AGENT_CSV_PATH`, `AGENT_VECTOR_STORE_PATH`.
- `AGENT_SIMILARITY_THRESHOLD`, `AGENT_RETRIEVAL_K`, `AGENT_LLM_MODEL`, `AGENT_EMBEDDING_MODEL`.

## 📚 Base de Conhecimento
`data/base_conhecimento_ifood_genai-exemplo.csv` — cada linha vira um documento vetorial único; material meramente ilustrativo.

## 🧭 Estrutura
```
backend/
  app/api/routes.py
  app/core/config.py
  app/rag/{ingestion,retriever,llm_client,agent}.py
  app/main.py
  tests/
frontend/
  src/{components,services,types}.ts(x)
  vite/tsconfig/vitest configs
.github/workflows/ci.yml
Makefile
README.md
```

## 🚀 Evoluções
- Observabilidade (LangSmith/Otel), logs de confiança.
- Integração com orquestradores no-code (n8n/Dify).
- Classificador de intenção mais robusto; APIs fictícias de pedidos/estornos.

## 📜 Disclaimer
POC educativa; não substitui políticas oficiais do iFood. Use apenas para demonstração/portfólio.

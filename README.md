# iFood GenAI Refunds Agent

POC educativa de um agente interno para decisões de reembolso, cancelamento e cobrança usando RAG em cima de um CSV de políticas simuladas. Foco em consistência, anti-alucinação e transparência das fontes.

> Aviso: esta POC usa uma base simulada e **não representa políticas oficiais do iFood**. Serve apenas para estudo/portfólio.

## Visão Geral
- Problema: colaboradores precisam decidir sobre reembolsos/cancelamentos de forma consistente e auditável.
- Objetivos: respostas baseadas em política, citar fontes, aplicar fallback seguro quando não há confiança, evitar alucinação.
- Entregáveis: backend FastAPI + RAG (LangChain + FAISS), frontend React/Vite exibindo resposta e fontes, CI com lint/test.

## Arquitetura
```
           +-------------------+
CSV -----> | Ingestão (CLI)    | -- embeddings --> Vector Store (FAISS)
           +-------------------+
                     |
                     v
User ---> Frontend (React) ----> Backend FastAPI (/api/chat)
                                   |--> Retriever (FAISS)
                                   |--> Prompt + LLM (OpenAI ou fake)
                                   |--> Fallback anti-alucinação
                     v
              Resposta + fontes
```
- Camada de ingestão: `python -m backend.app.rag.ingestion` lê `data/base_conhecimento_ifood_genai-exemplo.csv`, cria documentos semânticos e salva FAISS local.
- Camada RAG: `VectorStoreRetriever` busca top-k, aplica `similarity_threshold` para confiança.
- API: `/api/chat` recebe pergunta, classifica fora-do-escopo simples, consulta RAG, monta prompt anti-alucinação e retorna resposta + fontes + flag `is_fallback` + `similarity_scores`.
- Frontend: SPA mostra chat, badge de fallback e painel de fontes.

## Decisões Técnicas
- **LangChain + FAISS**: local, fácil de trocar embeddings/LLM, sem dependência paga para vetor.
- **FastAPI**: tipagem, validação Pydantic e TestClient para TDD.
- **React + Vite**: build rápido, DX simples, teste com Vitest/RTL.
- **Anti-alucinação**: system prompt rígido (ver `backend/app/rag/llm_client.py`), fallback quando `score < 0.6` ou sem docs, fora de escopo (ex. clima) explicitado.

## Stack
| Área | Escolha |
| --- | --- |
| Backend | Python 3.11, FastAPI, LangChain, FAISS, ChatOpenAI |
| Frontend | React + Vite + TypeScript |
| Qualidade backend | pytest, ruff, black, isort, mypy |
| Qualidade frontend | ESLint, Prettier, Vitest + RTL |
| CI | GitHub Actions (lint + testes) |

## Como rodar localmente
Pré-requisitos: Python 3.11+, Node 18+, chave OpenAI (opcional se usar embeddings fake para testes).

1. Clone o repo e entre na pasta.
2. Backend
   ```bash
   pip install -e .[dev]
   export AGENT_OPENAI_API_KEY=...  # opcional, use AGENT_USE_FAKE_EMBEDDINGS=true para ambiente offline
   python -m backend.app.rag.ingestion
   uvicorn backend.app.main:app --reload --port 8000
   ```
3. Frontend
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Ajuste o frontend para apontar para o backend com `VITE_API_URL` (por padrão http://localhost:8000/api).

## Como testar
- Backend: `pytest` (usa FakeEmbeddings, não chama OpenAI; modo offline seguro com heurística/fallback).
- Frontend: `cd frontend && npm test`.
- Cenários manuais sugeridos:
  - Pedido já saiu para entrega, cliente quer reembolso (usa política 3.2 / 4.1).
  - Restaurante cancelou por falta de ingrediente (política 2.3).
  - Cliente cobrado após cancelamento (Fluxo Financeiro, validação de estorno).
  - Pergunta fora de escopo (“previsão do tempo”) → fallback imediato.
  - Pergunta ambígua não coberta → fallback seguro.

## Fallback e Anti-alucinação
- Threshold de similaridade (`AGENT_SIMILARITY_THRESHOLD`, default 0.6). Abaixo disso, devolve fallback padronizado. Em modo fake/offline, o threshold pode ser ajustado (ex.: 0.0 para demos, >0.5 para forçar fallback).
- Sem documentos, fora do escopo ou baixa confiança → fallback.
- Prompt proíbe criar regras não presentes e exige citar fontes.
- Mensagem de fallback: "Não encontrei informação suficiente na base para responder com segurança. Sugiro abrir um ticket interno ou consultar a política oficial."

## Variáveis de ambiente principais
- `AGENT_OPENAI_API_KEY`: chave para LLM/embeddings (opcional em teste).
- `AGENT_USE_FAKE_EMBEDDINGS`: `true` para ambiente offline/teste.
- `AGENT_CSV_PATH`: caminho do CSV (default `data/base_conhecimento_ifood_genai-exemplo.csv`).
- `AGENT_VECTOR_STORE_PATH`: onde persistir o FAISS (default `data/vector_store`).
- `AGENT_SIMILARITY_THRESHOLD`, `AGENT_RETRIEVAL_K`, `AGENT_LLM_MODEL`, `AGENT_EMBEDDING_MODEL` para ajustes finos.

## Campos retornados pela API
`POST /api/chat` retorna:
```json
{
  "answer": "string",
  "is_fallback": true,
  "sources": [{ "id": "...", "fonte": "...", "categoria": "...", "pergunta": "...", "resposta": "...", "score": 0.0 }],
  "similarity_scores": [{ "source_id": "...", "score": 0.0 }]
}
```
`similarity_scores` é opcional e traz o score associado a cada fonte retornada.

## Limitações e modo offline
- Em modo offline (`AGENT_USE_FAKE_EMBEDDINGS=true`), não há chamada a LLM externa; a resposta é construída de forma determinística a partir das fontes recuperadas e heurísticas de sobreposição de termos.
- Para demos, use `AGENT_SIMILARITY_THRESHOLD=0.0` para não cair em fallback; para mais rigor, aumente o threshold (ex. `0.8`) ou deixe default (0.6) para forçar fallback em dúvidas ambíguas.
- Em produção real, prefira embeddings/LLM de verdade para melhor relevância e confiança.

## Prompt do LLM (trecho)
Definido em `backend/app/rag/llm_client.py`:
> Você é um agente interno do iFood que auxilia colaboradores (Foodlovers) em dúvidas sobre reembolsos, cancelamentos e cobrança...\n
> - Sempre responda **apenas** com base nos trechos de contexto fornecidos.\n
> - Quando o contexto não for suficiente, siga o fallback: "Não encontrei informação suficiente..."\n
> - Cite a fonte no formato: "De acordo com [FONTE: {fonte}] – ..."\n
> - Fora de escopo (ex.: clima) deve ser indicado como tal.

## Estrutura de pastas
```
backend/
  app/
    api/routes.py        # rotas FastAPI (/api/chat, /health)
    core/config.py       # settings (env)
    rag/ingestion.py     # CLI de ingestão CSV -> FAISS
    rag/retriever.py     # busca semântica
    rag/llm_client.py    # prompt anti-alucinação + client LLM
    rag/agent.py         # orquestração retrieval + fallback
    main.py              # inicialização FastAPI
  tests/                 # pytest com FakeEmbeddings e TestClient
frontend/
  src/
    components/          # Chat, MessageBubble, SourcesPanel
    services/api.ts      # chamada HTTP
    types.ts             # modelos TS
    App.tsx, main.tsx
  vite.config.ts, vitest.config.ts, tsconfig*.json
.github/workflows/ci.yml
ENGINEERING_GUIDELINES.md
Makefile
README.md
```

## Evoluções possíveis
- Logs de confiança e observabilidade (ex.: LangSmith, OpenTelemetry).
- Integração com orquestradores no-code (n8n/Dify) consumindo a API.
- Classificador de intenção mais robusto para categorias internas.
- Integração com APIs fictícias de pedido/estorno para enriquecer contexto.

## Base de conhecimento
Arquivo `data/base_conhecimento_ifood_genai-exemplo.csv` com categorias/perguntas/respostas/fonte simuladas. Cada linha vira um documento vetorial único (sem chunking múltiplo). Não é material oficial.

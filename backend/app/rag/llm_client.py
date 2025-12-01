from __future__ import annotations

from typing import Iterable, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.app.core.config import get_settings
from backend.app.models.schemas import RetrievedSource

SYSTEM_PROMPT = (
    "Você é um agente interno do iFood que auxilia colaboradores (Foodlovers) em dúvidas "
    "sobre reembolsos, cancelamentos e cobrança, com base em uma base de conhecimento oficial.\n"
    "INSTRUÇÕES IMPORTANTES:\n"
    "- Sempre responda apenas com base nos trechos de contexto fornecidos.\n"
    "- NÃO crie nem infira políticas que não estejam presentes nos documentos.\n"
    "- Quando o contexto não for suficiente para responder com segurança, você DEVE dizer que não sabe "
    "e seguir o protocolo de fallback: 'Não encontrei informação suficiente na base para responder com segurança. "
    "Sugiro abrir um ticket interno ou consultar a política oficial.'\n"
    "- Sempre que citar uma regra, mencione a fonte no formato: 'De acordo com [FONTE: {fonte}] – ...'\n"
    "- Use linguagem clara, objetiva e respeitosa, adequada a ambiente interno de empresa.\n"
    "- Se a pergunta não estiver relacionada a reembolso, cancelamento ou cobrança, informe que está fora do escopo do agente."
)

FALLBACK_MESSAGE = (
    "Não encontrei informação suficiente na base para responder com segurança. Sugiro abrir um ticket interno "
    "ou consultar a política oficial."
)


class OfflineLLM:
    """LLM simplificado para uso offline.

    Não chama provedores externos; a formatação/anti-alucinação é aplicada no LLMClient.generate,
    construindo a resposta apenas a partir das fontes recuperadas ou caindo em fallback.
    """

    def invoke(self, messages):
        # Em modo offline a formatação é tratada diretamente no LLMClient.generate
        return AIMessage(content="offline-response")


class LLMClient:
    def __init__(self, llm: ChatOpenAI | None = None):
        settings = get_settings()
        if settings.openai_api_key:
            self.llm = llm or ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)
            self.offline_mode = False
        else:
            # Modo offline: não chama provedor externo
            self.llm = OfflineLLM()
            self.offline_mode = True

    def render_context(self, sources: Iterable[RetrievedSource]) -> str:
        blocks: List[str] = []
        for src in sources:
            blocks.append(
                f"[FONTE: {src.fonte}] [CATEGORIA: {src.categoria}]\nCENÁRIO: {src.pergunta}\nAÇÃO RECOMENDADA: {src.resposta}"
            )
        return "\n\n".join(blocks)

    def generate(self, question: str, sources: Iterable[RetrievedSource]) -> str:
        if self.offline_mode:
            return self._generate_offline_response(question, list(sources))

        context_block = self.render_context(sources)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Contexto recuperado:\n"
                    f"{context_block if context_block else 'N/A'}\n\n"
                    f"Pergunta do colaborador: {question}\n"
                    "Responda citando as fontes e aplique o protocolo anti-alucinação."
                )
            ),
        ]
        response = self.llm.invoke(messages)
        if isinstance(response, AIMessage):
            return response.content
        return str(response)

    def _generate_offline_response(
        self, question: str, sources: List[RetrievedSource], max_sources: int = 3
    ) -> str:
        if not sources:
            return FALLBACK_MESSAGE
        top_sources = sources[:max_sources]
        bullets: List[str] = []
        for src in top_sources:
            bullets.append(
                f"- {src.fonte} [{src.categoria}]: {src.resposta} (cenário: {src.pergunta})"
            )
        return (
            "Resposta baseada na base simulada (modo offline, sem LLM externo):\n"
            "Fontes utilizadas:\n"
            + "\n".join(bullets)
            + "\n\nSe o contexto não cobrir totalmente, acione o fallback seguro."
        )

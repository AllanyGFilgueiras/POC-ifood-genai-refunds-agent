from fastapi import APIRouter, Depends

from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.rag.agent import AgentService

router = APIRouter()


def get_agent() -> AgentService:
    return AgentService()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, agent: AgentService = Depends(get_agent)) -> ChatResponse:
    return agent.answer(payload.question)

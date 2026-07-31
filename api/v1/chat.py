from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from services.agentservices.run import handle_turn

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    message: str
    current_agent: str = "orchestrator"
    history: list[Any] = []


class ChatResponse(BaseModel):
    response: str
    current_agent: str
    history: list[Any]


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):

    response, current_agent, history = await handle_turn(
        req.current_agent,
        req.history,
        req.message
    )

    return ChatResponse(
        response=response,
        current_agent=current_agent,
        history=history
    )
import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.orchestrator import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, Any]] = []


class ToolCall(BaseModel):
    tool: str
    input: dict[str, Any]
    result_preview: str


class ChatResponse(BaseModel):
    response: str
    history: list[dict[str, Any]]
    tool_calls: list[ToolCall]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response_text, updated_history, tool_calls_log = await run_agent(
            request.message, request.history
        )
    except Exception as e:
        logger.exception("Agent error")
        response_text = f"Agent error: {e}"
        updated_history = request.history
        tool_calls_log = []
    return ChatResponse(
        response=response_text,
        history=updated_history,
        tool_calls=[ToolCall(**tc) for tc in tool_calls_log],
    )

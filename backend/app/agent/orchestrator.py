import json
import logging
from typing import Any

import anthropic

from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, dispatch_tool
from app.config import settings

logger = logging.getLogger(__name__)


async def run_agent(
    user_message: str,
    conversation_history: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (response_text, updated_history, tool_calls_log)."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = conversation_history + [{"role": "user", "content": user_message}]
    tool_calls_log: list[dict[str, Any]] = []

    logger.info("--- New query: %s", user_message)

    max_iterations = 10
    for iteration in range(max_iterations):
        try:
            response = await client.messages.create(
                model=settings.model_name,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIError as e:
            error_msg = f"API error: {e.message}"
            logger.error("Claude API error: %s", error_msg)
            return error_msg, messages, tool_calls_log

        messages.append({"role": "assistant", "content": [b.model_dump() for b in response.content]})

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            text = "".join(
                b.text for b in response.content if hasattr(b, "text")
            )
            logger.info("--- Done after %d tool call round(s)", iteration)
            return text, messages, tool_calls_log

        tool_results = []
        for tool_block in tool_use_blocks:
            logger.info(
                "  [tool] %s(%s)",
                tool_block.name,
                json.dumps(tool_block.input, default=str),
            )
            result = await dispatch_tool(tool_block.name, tool_block.input)
            result_preview = result[:200] + "..." if len(result) > 200 else result
            logger.info("  [result] %s", result_preview)

            tool_calls_log.append({
                "tool": tool_block.name,
                "input": tool_block.input,
                "result_preview": result_preview,
            })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    return "Reached maximum tool iterations. Please try a simpler question.", messages, tool_calls_log

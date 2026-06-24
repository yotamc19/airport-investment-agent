from typing import Any

import anthropic

from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, dispatch_tool
from app.config import settings


async def run_agent(
    user_message: str,
    conversation_history: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    messages = conversation_history + [{"role": "user", "content": user_message}]

    max_iterations = 10
    for _ in range(max_iterations):
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
            return error_msg, messages

        messages.append({"role": "assistant", "content": response.content})

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            text = "".join(
                b.text for b in response.content if hasattr(b, "text")
            )
            return text, messages

        tool_results = []
        for tool_block in tool_use_blocks:
            result = await dispatch_tool(tool_block.name, tool_block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    return "Reached maximum tool iterations. Please try a simpler question.", messages


import json
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage


class TraceLogger:
    def __init__(self) -> None:
        self.current_section: str | None = None
        self.reasoning_buffer: list[str] = []
        self.answer_buffer: list[str] = []

    def section(self, name: str) -> None:
        if self.current_section == name:
            return

        self.current_section = name
        print(f"\n\n========== {name} ==========")

    def reasoning(self, text: str) -> None:
        if not text:
            return

        self.section("LLM REASONING")
        self.reasoning_buffer.append(text)
        print(text, end="", flush=True)

    def answer(self, text: str) -> None:
        if not text:
            return

        self.section("LLM ANSWER")
        self.answer_buffer.append(text)
        print(text, end="", flush=True)

    def tool_call(self, name: str, args: Any) -> None:
        self.section("TOOL CALL")
        print(f"Tool: {name}")
        print("Args:")
        print(json.dumps(args, ensure_ascii=False, indent=2))

    def tool_result(self, content: Any) -> None:
        self.section("TOOL RESULT")
        print(str(content).strip())

    def agent_step(self, node_name: str) -> None:
        self.section("AGENT STEP")
        print(f"Node completed: {node_name}")

    def final(self, data: Any) -> None:
        if not isinstance(data, dict):
            return

        messages = data.get("messages", [])
        if not messages:
            return

        last = messages[-1]
        if not isinstance(last, AIMessage):
            return

        if getattr(last, "tool_calls", None):
            return

        if not str(last.content).strip():
            return

        self.section("FINAL")
        print(str(last.content).strip())


def render_event(event_name: str, data: Any, logger: TraceLogger) -> None:
    if event_name == "messages":
        message, metadata = data

        if not isinstance(message, AIMessageChunk):
            return

        meta = message.response_metadata or {}
        channel = meta.get("_custom_channel")

        if channel == "reasoning":
            text = message.additional_kwargs.get("reasoning_delta", "")
            logger.reasoning(text)
            return

        if channel == "tool_call":
            for tool_call in message.tool_calls or []:
                logger.tool_call(
                    name=tool_call.get("name", "(unknown)"),
                    args=tool_call.get("args", {}),
                )
            return

        if channel == "answer":
            logger.answer(str(message.content))
            return
    if event_name == "updates":
        if not isinstance(data, dict):
            return

        for node_name, node_data in data.items():
            logger.agent_step(node_name)

            if not isinstance(node_data, dict):
                continue

            for msg in node_data.get("messages", []):
                if isinstance(msg, ToolMessage):
                    logger.tool_result(msg.content)

        return

    if event_name == "values":
        logger.final(data)
        return
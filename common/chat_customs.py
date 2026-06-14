
import json
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from typing import Any
import httpx
import requests

from langchain.agents import create_agent
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool

class ChatCustoms(BaseChatModel):
    model: str
    base_url: str = "http://localhost:8000"
    temperature: float = 0.7
    timeout: int = 120
    enable_thinking: bool = True
    headers: dict[str, str] | None = None
    debug_print_reasoning: bool = False
    debug_print_raw_answer: bool = False
    debug_print_raw_sse: bool = False

    bound_tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | bool | None = None

    @property
    def _llm_type(self) -> str:
        return "chat-customs"

    @property
    def chat_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/chat"

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: str | dict[str, Any] | bool | None = None,
        **kwargs: Any,
    ) -> "ChatCustoms":
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]

        return self.model_copy(
            update={
                "bound_tools": formatted_tools,
                "tool_choice": tool_choice,
            }
        )

    def _convert_messages(self, messages: list[BaseMessage]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []

        for message in messages:
            if isinstance(message, HumanMessage):
                converted.append({"role": "user", "content": self._serialize_message_content(message.content)})
            elif isinstance(message, SystemMessage):
                converted.append({"role": "system", "content": self._serialize_message_content(message.content)})
            elif isinstance(message, AIMessage):
                item: dict[str, Any] = {
                    "role": "assistant",
                    "content": self._serialize_message_content(message.content),
                }

                if message.tool_calls:
                    item["tool_calls"] = []

                    for index, tool_call in enumerate(message.tool_calls):
                        tool_call_id = tool_call.get("id") or f"call_{index}"
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args", {})

                        if not tool_name:
                            continue

                        item["tool_calls"].append(
                            {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_args,
                                },
                            }
                        )

                converted.append(item)
            elif isinstance(message, ToolMessage):
                tool_content = self._format_tool_message_content(message.content)

                item: dict[str, Any] = {
                    "role": "tool",
                    "content": tool_content,
                }
                if message.tool_call_id:
                    item["tool_call_id"] = message.tool_call_id
                if message.name:
                    item["tool_name"] = message.name

                converted.append(item)
            else:
                converted.append({"role": "user", "content": self._serialize_message_content(message.content)})

        return converted

    def _serialize_message_content(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                        continue
                    if item.get("type") == "tool_result":
                        result_text = item.get("content")
                        if isinstance(result_text, str):
                            parts.append(result_text)
            return "\n".join(part for part in parts if part)
        if isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, str):
                return text
        return str(content)

    def _format_tool_message_content(self, content: Any) -> str:
        serialized = self._serialize_message_content(content)

        try:
            parsed = json.loads(serialized)
        except (TypeError, json.JSONDecodeError):
            return serialized

        if isinstance(parsed, list):
            lines = ["Tool execution result:"]
            for index, item in enumerate(parsed, start=1):
                if isinstance(item, dict):
                    title = item.get("title") or item.get("name") or "Untitled"
                    url = item.get("url") or item.get("link") or ""
                    snippet = item.get("snippet") or item.get("content") or item.get("text") or ""
                    lines.append(f"{index}. {title}")
                    if url:
                        lines.append(f"   URL: {url}")
                    if snippet:
                        lines.append(f"   Summary: {snippet}")
                else:
                    lines.append(f"{index}. {item}")
            return "\n".join(lines)

        if isinstance(parsed, dict):
            lines = ["Tool execution result:"]
            for key, value in parsed.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)

        return serialized

    def _build_payload(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": stream,
            "think": self.enable_thinking,
            "options": {
                "temperature": self.temperature,
            },
        }

        if stop:
            payload["stop"] = stop

        if self.bound_tools:
            payload["tools"] = self.bound_tools

        if self.tool_choice:
            payload["tool_choice"] = self.tool_choice

        payload.update(kwargs)
        return payload

    def _raise_for_status(self, response: requests.Response | httpx.Response, payload: dict[str, Any]) -> None:
        try:
            response.raise_for_status()
        except (requests.HTTPError, httpx.HTTPStatusError) as exc:
            try:
                body = response.text[:2000]
            except httpx.ResponseNotRead:
                body = "<streaming response body was not read>"
            request_preview = {
                "model": payload.get("model"),
                "stream": payload.get("stream"),
                "think": payload.get("think"),
                "message_roles": [message.get("role") for message in payload.get("messages", [])],
                "last_message": (payload.get("messages") or [None])[-1],
                "tools_count": len(payload.get("tools") or []),
            }
            raise RuntimeError(
                "Chat API request failed "
                f"({response.status_code} {response.reason_phrase if isinstance(response, httpx.Response) else response.reason}).\n"
                f"Response body: {body}\n"
                f"Request preview: {json.dumps(request_preview, ensure_ascii=False, indent=2)}"
            ) from exc

    def _extract_message_fields(self, data: dict[str, Any]) -> tuple[str, str | None]:
        message = data.get("message") or {}

        content = message.get("content") or data.get("content") or data.get("response") or ""
        reasoning = (
            message.get("thinking")
            or message.get("reasoning")
            or message.get("reasoning_content")
            or data.get("thinking")
            or data.get("reasoning")
            or data.get("reasoning_content")
        )

        return str(content), str(reasoning) if reasoning else None

    def _extract_tool_calls(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        message = data.get("message") or {}
        raw_tool_calls = message.get("tool_calls") or data.get("tool_calls") or []

        tool_calls: list[dict[str, Any]] = []

        for index, raw_call in enumerate(raw_tool_calls):
            function = raw_call.get("function") or {}
            name = raw_call.get("name") or function.get("name")
            args = raw_call.get("args") or function.get("arguments") or {}

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"__raw_args": args}

            if name:
                tool_calls.append(
                    {
                        "id": raw_call.get("id") or f"call_{index}",
                        "name": name,
                        "args": args,
                    }
                )

        return tool_calls

    def _build_ai_message(self, data: dict[str, Any]) -> AIMessage:
        content, reasoning = self._extract_message_fields(data)
        tool_calls = self._extract_tool_calls(data)

        return AIMessage(
            content=content,
            tool_calls=tool_calls,
            additional_kwargs={
                "reasoning_content": reasoning,
            },
            response_metadata=data,
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload = self._build_payload(messages, stop=stop, stream=False, **kwargs)
        response = requests.post(
            self.chat_url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        self._raise_for_status(response, payload)

        message = self._build_ai_message(response.json())
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        final_content: list[str] = []
        final_reasoning: list[str] = []
        final_tool_calls: list[dict[str, Any]] = []

        async for chunk in self._astream(
            messages=messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        ):
            message = chunk.message
            metadata = message.response_metadata or {}

            channel = metadata.get("_custom_channel")

            if channel == "reasoning":
                reasoning_delta = message.additional_kwargs.get("reasoning_delta")
                if reasoning_delta:
                    final_reasoning.append(str(reasoning_delta))
                continue

            if message.content:
                final_content.append(str(message.content))

            for tool_call in message.tool_calls or []:
                final_tool_calls.append(tool_call)

        message = AIMessage(
            content="".join(final_content),
            tool_calls=final_tool_calls,
            additional_kwargs={
                "reasoning_content": "".join(final_reasoning) or None,
            },
        )

        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        payload = self._build_payload(messages, stop=stop, stream=True, **kwargs)
        with requests.post(
            self.chat_url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
            stream=True,
        ) as response:
            self._raise_for_status(response, payload)

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    line = line.removeprefix("data: ").strip()
                if line == "[DONE]":
                    break

                data = json.loads(line)
                content, reasoning = self._extract_message_fields(data)
                tool_calls = self._extract_tool_calls(data)
                if tool_calls:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(
                            content="",
                            tool_calls=tool_calls,
                            response_metadata={
                                "_custom_channel": "tool_call",
                            },
                        )
                    )
                if reasoning:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(
                            content="",
                            additional_kwargs={
                                "reasoning_delta": reasoning,
                            },
                            response_metadata={
                                **data,
                                "_custom_channel": "reasoning",
                            },
                        )
                    )

                if content:
                    if run_manager:
                        run_manager.on_llm_new_token(content)

                    yield ChatGenerationChunk(
                        message=AIMessageChunk(
                            content=content,
                            additional_kwargs={},
                            response_metadata={
                                **data,
                                "_custom_channel": "answer",
                            },
                        )
                    )

                if data.get("done"):
                    break

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = self._build_payload(messages, stop=stop, stream=True, **kwargs)
            async with client.stream(
                "POST",
                self.chat_url,
                json=payload,
                headers=self.headers,
            ) as response:
                if response.is_error:
                    await response.aread()
                self._raise_for_status(response, payload)

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line.removeprefix("data: ").strip()
                    if line == "[DONE]":
                        break

                    data = json.loads(line)
                   
                    content, reasoning = self._extract_message_fields(data)
                    tool_calls = self._extract_tool_calls(data)

                    if tool_calls:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(
                                content="",
                                tool_calls=tool_calls,
                                response_metadata={
                                    "_custom_channel": "tool_call",
                                },
                            )
                        )

                    if reasoning:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(
                                content="",
                                additional_kwargs={
                                    "reasoning_delta": reasoning,
                                },
                                response_metadata={
                                    **data,
                                    "_custom_channel": "reasoning",
                                },
                            )
                        )

                    if content:
                        if run_manager:
                            await run_manager.on_llm_new_token(content)

                        yield ChatGenerationChunk(
                            message=AIMessageChunk(
                                content=content,
                                additional_kwargs={},
                                response_metadata={
                                    **data,
                                    "_custom_channel": "answer",
                                },
                            )
                        )

                    if data.get("done"):
                        break
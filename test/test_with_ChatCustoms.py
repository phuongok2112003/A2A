from __future__ import annotations

import asyncio
import os
import json
import sys
import time
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
from langgraph.config import get_stream_writer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")





class ChatCustoms(BaseChatModel):
    model: str
    base_url: str = "https://agent.pgcluster.asia"
    temperature: float = 0.7
    timeout: int = 120
    enable_thinking: bool = True
    headers: dict[str, str] | None = None
    debug_print_reasoning: bool = False
    debug_print_raw_answer: bool = False
    debug_print_raw_sse: bool = False
    max_retries: int = 2
    retry_backoff: float = 3.0

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
                content = self._serialize_message_content(message.content)
                if message.tool_calls and not content:
                    continue

                item: dict[str, Any] = {
                    "role": "assistant",
                    "content": content,
                }

                converted.append(item)
            elif isinstance(message, ToolMessage):
                tool_content = self._format_tool_message_content(message.content)
                converted.append({"role": "user", "content": tool_content})
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

    def _retry_delay(self, response: requests.Response | httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                pass
        return self.retry_backoff * (attempt + 1)

    def _extract_message_fields(self, data: dict[str, Any]) -> tuple[str, str | None]:
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            delta = choices[0].get("delta") or choices[0].get("message") or {}
            content = delta.get("content") or ""
            reasoning = (
                delta.get("reasoning")
                or delta.get("reasoning_content")
                or delta.get("thinking")
            )
            return str(content), str(reasoning) if reasoning else None

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
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            delta = choices[0].get("delta") or choices[0].get("message") or {}
            raw_tool_calls = delta.get("tool_calls") or []
        else:
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

    def _choice_finish_reason(self, data: dict[str, Any]) -> str | None:
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            finish_reason = choices[0].get("finish_reason")
            return str(finish_reason) if finish_reason else None
        return None

    def _accumulate_tool_call_chunks(
        self,
        pending_tool_calls: dict[int, dict[str, Any]],
        data: dict[str, Any],
    ) -> None:
        choices = data.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return

        delta = choices[0].get("delta") or {}
        raw_tool_calls = delta.get("tool_calls") or []
        for fallback_index, raw_call in enumerate(raw_tool_calls):
            index = raw_call.get("index", fallback_index)
            pending = pending_tool_calls.setdefault(
                index,
                {
                    "id": raw_call.get("id") or f"call_{index}",
                    "name": None,
                    "args_text": "",
                },
            )
            if raw_call.get("id"):
                pending["id"] = raw_call["id"]

            function = raw_call.get("function") or {}
            if function.get("name"):
                pending["name"] = function["name"]
            if function.get("arguments"):
                pending["args_text"] += function["arguments"]

    def _finalize_pending_tool_calls(
        self,
        pending_tool_calls: dict[int, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tool_calls: list[dict[str, Any]] = []
        for index, pending in sorted(pending_tool_calls.items()):
            name = pending.get("name")
            if not name:
                continue

            args_text = pending.get("args_text") or "{}"
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError:
                args = {"__raw_args": args_text}

            tool_calls.append(
                {
                    "id": pending.get("id") or f"call_{index}",
                    "name": name,
                    "args": args,
                }
            )
        return tool_calls

    def _parse_stream_line(self, line: str) -> dict[str, Any] | None:
        line = line.strip()
        if not line or line == "[DONE]":
            return None
        if line.startswith(":") or line.startswith("event:"):
            return None
        if line.startswith("data:"):
            line = line.removeprefix("data:").strip()
        if not line or line == "[DONE]":
            return None

        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid chat stream line: {line[:500]!r}") from exc

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
        for attempt in range(self.max_retries + 1):
            response = requests.post(
                self.chat_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code == 429 and attempt < self.max_retries:
                time.sleep(self._retry_delay(response, attempt))
                continue
            self._raise_for_status(response, payload)
            break

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
        pending_tool_calls: dict[int, dict[str, Any]] = {}
        for attempt in range(self.max_retries + 1):
            with requests.post(
                self.chat_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                stream=True,
            ) as response:
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(self._retry_delay(response, attempt))
                    continue
                self._raise_for_status(response, payload)

                for line in response.iter_lines(decode_unicode=True):
                    data = self._parse_stream_line(line)
                    if data is None:
                        if line.strip() in {"[DONE]", "data: [DONE]"}:
                            break
                        continue
                    self._accumulate_tool_call_chunks(pending_tool_calls, data)
                    content, reasoning = self._extract_message_fields(data)
                    finish_reason = self._choice_finish_reason(data)
                    if finish_reason in {"tool_calls", "function_call"}:
                        tool_calls = self._finalize_pending_tool_calls(pending_tool_calls)
                        pending_tool_calls.clear()
                    elif data.get("choices"):
                        tool_calls = []
                    else:
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
            pending_tool_calls: dict[int, dict[str, Any]] = {}
            for attempt in range(self.max_retries + 1):
                async with client.stream(
                    "POST",
                    self.chat_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status_code == 429 and attempt < self.max_retries:
                        await response.aread()
                        await asyncio.sleep(self._retry_delay(response, attempt))
                        continue
                    if response.is_error:
                        await response.aread()
                    self._raise_for_status(response, payload)

                    async for line in response.aiter_lines():
                        data = self._parse_stream_line(line)
                        if data is None:
                            if line.strip() in {"[DONE]", "data: [DONE]"}:
                                break
                            continue
                        self._accumulate_tool_call_chunks(pending_tool_calls, data)
                       
                        content, reasoning = self._extract_message_fields(data)
                        finish_reason = self._choice_finish_reason(data)
                        if finish_reason in {"tool_calls", "function_call"}:
                            tool_calls = self._finalize_pending_tool_calls(pending_tool_calls)
                            pending_tool_calls.clear()
                        elif data.get("choices"):
                            tool_calls = []
                        else:
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
                    break

def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)

        return "".join(parts)

    return ""

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


from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup


try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - optional dependency
    sync_playwright = None




DEFAULT_SEARXNG_BASE_URL = "http://localhost:8888"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_FETCH_TEXT_LIMIT = 12000
LOCAL_TIMEZONE = ZoneInfo("Asia/Bangkok")

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass
class PageContent:
    url: str
    title: str
    content: str


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    clean_query = {
        key: value
        for key, value in query.items()
        if key not in TRACKING_PARAMS
    }
    query_string = "&".join(
        f"{key}={value[0]}"
        for key, value in clean_query.items()
        if value
    )
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            "",
        )
    )


def truncate_text(value: str, limit: int = DEFAULT_FETCH_TEXT_LIMIT) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def extract_content_from_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    main = soup.find("article") or soup.find("main") or soup.find("body")
    if not main:
        return title, ""

    text = main.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return title, "\n".join(lines)


def normalize_search_results(payload: Any, max_results: int = 5) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        raw_results = payload.get("results", [])
    elif isinstance(payload, list):
        raw_results = payload
    else:
        raw_results = []

    items: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        url = item.get("url") or item.get("link") or item.get("href")
        title = item.get("title") or item.get("name") or item.get("headline")
        snippet = item.get("content") or item.get("snippet") or item.get("description") or ""

        if not url or not title:
            continue

        cleaned_url = clean_url(str(url))
        if cleaned_url in seen:
            continue
        seen.add(cleaned_url)

        items.append(
            asdict(
                SearchResult(
                    title=str(title).strip(),
                    url=cleaned_url,
                    snippet=str(snippet).strip(),
                )
            )
        )
        if len(items) >= max_results:
            break

    return items


def normalize_fetch_result(payload: Any, url: str) -> dict[str, str]:
    if isinstance(payload, dict):
        title = payload.get("title") or payload.get("name") or ""
        content = (
            payload.get("content")
            or payload.get("text")
            or payload.get("body")
            or payload.get("markdown")
            or ""
        )
        resolved_url = payload.get("url") or payload.get("link") or url
    else:
        title = ""
        content = str(payload or "")
        resolved_url = url

    return asdict(
        PageContent(
            url=clean_url(str(resolved_url)),
            title=str(title).strip(),
            content=truncate_text(str(content)),
        )
    )


def searxng_search(
    keyword: str,
    limit: int = 15,
    base_url: str = DEFAULT_SEARXNG_BASE_URL,
) -> list[dict[str, str]]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = client.get(
            f"{base_url}/search",
            params={"q": keyword, "format": "json"},
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        response.raise_for_status()
        return normalize_search_results(response.json(), max_results=limit)


def current_local_datetime() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def normalize_freshness_search_query(query: str) -> str:
    current_year = str(current_local_datetime().year)
    freshness_terms = (
        "hôm nay",
        "hom nay",
        "mới nhất",
        "moi nhat",
        "latest",
        "today",
        "recent",
        "breaking",
    )
    old_years = ("2023", "2024", "2025")
    lowered = query.lower()

    if not any(term in lowered for term in freshness_terms):
        return query

    normalized = query
    for year in old_years:
        normalized = normalized.replace(year, current_year)

    if current_year not in normalized:
        normalized = f"{normalized} {current_year}"

    return normalized


def fetch_page_via_http(url: str) -> dict[str, str]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = client.get(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        response.raise_for_status()
        title, content = extract_content_from_html(response.text)
        if not content:
            content = response.text
        return asdict(
            PageContent(
                url=clean_url(str(response.url)),
                title=title,
                content=truncate_text(content),
            )
        )


def fetch_page_via_playwright(url: str) -> dict[str, str]:
    if sync_playwright is None:
        raise RuntimeError("playwright is not installed")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        try:
            page = browser.new_page(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1366, "height": 768},
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1500)
            html = page.content()
            title, content = extract_content_from_html(html)
            if len(content) < 200:
                try:
                    content = page.locator("body").inner_text(timeout=10_000)
                except Exception:
                    pass
            return asdict(
                PageContent(
                    url=clean_url(page.url),
                    title=title,
                    content=truncate_text(content),
                )
            )
        finally:
            browser.close()


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Search the web through the local SearXNG instance and return normalized results.
    For requests about today's/latest/recent news, use the current date/year from
    get_current_datetime; do not search old years such as 2024 or 2025 unless the
    user explicitly asks for historical information.

    Args:
        query: Search keyword or natural-language query.
        max_results: Maximum number of unique results to return.
    """
    normalized_query = normalize_freshness_search_query(query)
    return searxng_search(keyword=normalized_query, limit=max_results)


def fetch_webpage_text(url: str) -> dict[str, str]:
    """
    Fetch and extract readable text from a web page.

    The tool tries lightweight HTTP extraction first and falls back to Playwright
    for JavaScript-heavy pages when Playwright is available.
    """
    try:
        return fetch_page_via_http(url)
    except Exception as http_error:
        if sync_playwright is None:
            raise RuntimeError(
                f"HTTP fetch failed for {url} and Playwright is unavailable: {http_error}"
            ) from http_error

    try:
        return fetch_page_via_playwright(url)
    except Exception as playwright_error:
        raise RuntimeError(
            f"Unable to fetch webpage content for {url}: {playwright_error}"
        ) from playwright_error


def get_current_datetime() -> dict[str, str]:
    """
    Return the current local and UTC time so the agent can compare event dates
    against "today" before deciding whether an event is upcoming, ongoing, or past.
    """
    local_now = current_local_datetime()
    utc_now = local_now.astimezone(timezone.utc)
    return {
        "current_local_iso": local_now.isoformat(),
        "current_local_date": local_now.strftime("%Y-%m-%d"),
        "current_local_datetime": local_now.strftime("%Y-%m-%d %H:%M:%S Asia/Bangkok"),
        "current_year": str(local_now.year),
        "current_utc_iso": utc_now.isoformat(),
        "current_utc_date": utc_now.strftime("%Y-%m-%d"),
        "current_utc_datetime": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


async def main() -> None:
    ollama_key = os.environ.get("OLLAMA_KEY")
    if not ollama_key:
        raise RuntimeError("Set OLLAMA_KEY before running this script.")

    prompt = "Tổng hợp thông tin mới nhất về AI ngày hôm nay."
    current_time = get_current_datetime()
    system_prompt = (
        "Bạn là agent tìm kiếm tin tức có dùng tool. "
        f"Ngày hiện tại của người dùng là {current_time['current_local_date']} "
        f"({current_time['current_local_datetime']}). "
        "Khi người dùng hỏi 'hôm nay', 'mới nhất', hoặc 'latest', phải hiểu là ngày/năm hiện tại này. "
        "Trước khi trả lời tin tức mới nhất, hãy gọi get_current_datetime nếu cần xác nhận thời gian, "
        f"sau đó gọi search_web với truy vấn có năm hiện tại {current_time['current_year']} hoặc ngày hiện tại. "
        "Không tự dùng năm 2024 hoặc 2025 cho truy vấn tin mới nhất, trừ khi người dùng hỏi so sánh lịch sử. "
        "Nếu search_web trả về rỗng, hãy thử lại bằng truy vấn tiếng Anh và tiếng Việt khác nhưng vẫn giữ năm hiện tại. "
        "Trả lời bằng tiếng Việt và nêu rõ ngày bạn đang dùng."
    )
    prompt = "Tổng hợp thông tin mới nhất về AI ngày hôm nay."
    llm = ChatCustoms(
        model="nemotron-3-super:cloud",
        base_url="https://ollama.com",
        temperature=0.7,
        enable_thinking=True,
        headers={
            "Authorization": f"Bearer {ollama_key}"
        },)
    
    # llm = ChatCustoms(
    #     model="google/gemma-4-31b-it:free",
    #     base_url="https://openrouter.ai/api/v1",
    #     temperature=0.7,
    #     enable_thinking=True,
    #     headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    # )



    agent = create_agent(
        model=llm,
        tools=[fetch_webpage_text, search_web, get_current_datetime],
        system_prompt=system_prompt,
    )
   
    logger = TraceLogger()
    async for event_name, data in agent.astream(
    {
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    },
    stream_mode=["messages", "updates", "custom", "values"],
):
       render_event(event_name, data, logger)

if __name__ == "__main__":
    asyncio.run(main())

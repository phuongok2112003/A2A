from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os
import sys
import io
from pprint import pprint
from pathlib import Path

# Thêm project root vào sys.path để import absolute hoạt động
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from common.export_models_llm import ModelsLLM
from common.tool_common import run_shell

# Fix encoding trên Windows để hỗ trợ Unicode (tiếng Việt, v.v.)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


async def main():
    """
    Phiên bản sửa lỗi của test_mcp.py
    """

    # ---------- MCP Client (nguyên bản từ file gốc) ----------
    client = MultiServerMCPClient(
        {
            "gradio": {
                "url": "https://victor-websearch.hf.space/gradio_api/mcp/sse",
                "transport": "sse",
            },
        }
    )

    # ---------- Lấy tools từ MCP server ----------
    tools = await client.get_tools()

    system_prompt = """
You are a deterministic MCP Web Research Agent.

Primary objective:
- Use available MCP tools to retrieve up-to-date web information when a request needs browsing.
- Prefer tool-based evidence over model memory.

Core behavior:
- If the user asks about a URL, topic, or recent information, call tools first.
- Do not claim you visited or read a page unless a tool result confirms it.
- If a direct URL fetch fails, try an alternative tool strategy (search by title/topic, then open best match).

Tool usage rules:
- Use only parameters that are actually supported by the current MCP tool schema.
- Never invent Playwright-specific arguments (for example: waitUntil, headless, timeout) unless the tool explicitly defines them.
- If required params are missing, infer safe defaults from user intent.
- If a tool call fails due to bad args, fix args and retry once.

Extraction and summarization:
- Extract high-value content: title, main claims, technical details, definitions, and key numbers.
- Ignore noisy sections if possible (navigation text, ads, repetitive footer blocks).
- Summaries must include:
    1) Overview
    2) Key concepts
    3) Important details
    4) Source note (where the information came from)

Error handling:
- If tool access is blocked or unavailable, state exactly what failed.
- Provide a best-effort fallback: suggest next query or ask for another URL.
- Never fabricate page content.

Answer style:
- Clear, concise, and structured.
- Vietnamese when user writes Vietnamese.
"""
    # ---------- Tạo Agent với checkpointer đầy đủ ----------
    agent = create_deep_agent(
        ModelsLLM.llm_ollama_nemotron,
        tools,
        checkpointer=MemorySaver(),
        system_prompt=system_prompt,
    )

        # ---------- System prompt (điều chỉnh để phù hợp với MCP websearch hiện tại) ----------

    # ---------- Cập nhật system prompt cho agent ----------
    # Note: create_react_agent doesn't take system_prompt directly in this version
    # We'll need to handle this differently or use a different agent creation method
    # For now, let's test if the basic MCP connection works

    # ---------- Thông báo trạng thái ----------
    print("✅ Agent MCP đã được tạo thành công.")
    print(f"🔧 Số lượng tools từ MCP server: {len(tools)}")
    print(f"🤖 Model LLM: {ModelsLLM.llm_ollama_nemotron}")
    print(f"💾 Kết quả sẽ được xử lý bởi agent\n")

    # ---------- Tin nhắn từ người dùng (đã sửa để tránh lỗi encoding) ----------
    user_message = "Giá dầu thế giới hôm nay như thế nào? Hãy tra cứu thông tin trên internet và tóm tắt lại cho tôi."

    # ---------- Stream và in kết quả ----------
    print("=" * 70)
    print("🚀 Bắt đầu chạy agent MCP để truy cập IBM latent-space...")
    print("=" * 70 + "\n")

    try:
        async for event, data in agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=["values", "updates", "messages"],
            config={"configurable": {"thread_id": "browser-research-001"}}
        ):
            # In ra messages mới nhất
            if isinstance(data, dict) and "messages" in data:
                data["messages"][-1].pretty_print()
            elif hasattr(data, 'content'):
                # BaseMessage trực tiếp
                data.pretty_print()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())

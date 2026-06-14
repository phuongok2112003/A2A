from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os

from langchain_openai import ChatOpenAI

from deepagents import create_deep_agent

from langgraph.checkpoint.memory import MemorySaver





async def main():
    """
    Phiên bản sửa lỗi của test_mcp.py
    """

    # ---------- MCP Client (nguyên bản từ file gốc) ----------
    client = MultiServerMCPClient(
        {
            "web_search_and_fetch": {
                "transport": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "C:\\Users\\nguyenxuanphuong\\mcp_server\\web-search-mcp.py",
                ],
                "env": {
                    "OLLAMA_API_KEY": os.environ["OLLAMA_KEY"]
                },
            }
        }
    )

    # ---------- Lấy tools từ MCP server ----------
    tools = await client.get_tools()

    system_prompt = """
You are an autonomous AI research agent.

You have access to MCP tools:
- web_search
- web_fetch

CRITICAL RULES:
- You MUST use web_search before answering any factual, recent, real-world, event, organization, competition, schedule, or internet-related question.
- NEVER answer from memory for time-sensitive information.
- ALWAYS verify information by fetching the source page with web_fetch.
- If web_search returns no useful results, refine the query and search again.
- You may perform multiple searches.

RESEARCH WORKFLOW:
1. Understand the user's constraints precisely.
2. Use web_search to discover candidate sources.
3. Use web_fetch to open and validate the source content.
4. Extract structured information.
5. Remove duplicates.
6. Filter invalid/outdated entries.
7. Return only verified results.

DATE AWARENESS:
- Today's date is 2026-05-20.
- Exclude:
  - expired events
  - ongoing events
  - cancelled events
- Only include future upcoming events.

FILTERING RULES:
- Only include AI-related hackathons.
- Only include hackathons located in Northern Vietnam.
- Ignore nationwide online-only events unless they explicitly mention Northern Vietnam participation or venue.
- Ignore unrelated tech competitions.

OUTPUT FORMAT:
Return markdown table with columns:
| Name | Location | Start Date | Registration Deadline | Organizer | URL |

For every item:
- include exact source URL
- include only verified information
- if information is missing, write "Not publicly available"

TOOL USAGE POLICY:
- web_search is the primary discovery tool.
- web_fetch is mandatory before trusting a source.
- Never fabricate URLs or event details.

REASONING POLICY:
- Think step-by-step internally.
- Do not expose hidden chain-of-thought.
- Only provide concise reasoning summaries if needed.

If no valid events are found, clearly state that.
"""
    # ---------- Tạo Agent với checkpointer đầy đủ ----------
    model = ChatOpenAI(
    model="nemotron-3-super:cloud",
    temperature=0.2,
    api_key=os.environ["OLLAMA_KEY"],
    base_url="https://ollama.com/v1"
)
    agent = create_deep_agent(
        model,
        tools,
        checkpointer=MemorySaver(),
        system_prompt=system_prompt,
    )

  
    user_message = "Tôi muốn bạn tìm cho tôi những cuộc thi hackathon về AI sắp diễn ra trong năm 2026, hôm nay là ngày 20/5/2026, loại bỏ những cuộc thi đã diễn ra và đang diễn ra. Thống kê cho tôi những cuộc thi ở miền Bắc Việt Nam thôi"

    # ---------- Stream và in kết quả ----------
    print("=" * 70)
    print("🚀 Bắt đầu chạy agent MCP để truy cập IBM latent-space...")
    print("=" * 70 + "\n")

    try:
        async for event, data in agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=["values", "updates", "messages"],
            config={"configurable": {"thread_id": "browser-research-001"}},
        ):
            # In ra messages mới nhất
            if isinstance(data, dict) and "messages" in data:
                data["messages"][-1].pretty_print()
            elif hasattr(data, "content"):
                # BaseMessage trực tiếp
                data.pretty_print()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())

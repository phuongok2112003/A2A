import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from common.export_models_llm import ModelsLLM
from pprint import pprint
import sys
import io

# Fix encoding trên Windows để hỗ trợ Unicode (tiếng Việt, v.v.)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def main():
    """
    Phiên bản sửa lỗi của test_mcp.py
    """

    # ---------- MCP Client (nguyên bản từ file gốc) ----------
    client = MultiServerMCPClient(
        {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@executeautomation/playwright-mcp-server"],
                "transport":"stdio"
            }
        }
    )

    # ---------- Lấy tools từ MCP server ----------
    tools = await client.get_tools()

    # ---------- Tạo Agent với checkpointer đầy đủ ----------
    agent = create_react_agent(
        ModelsLLM.llm_ollama_nemotron,
        tools,
        checkpointer=MemorySaver(),
    )

    # ---------- System prompt (nguyên bản từ file gốc, đã sửa lỗi formatting) ----------
    system_prompt = """
You are a Browser Automation Agent powered by Playwright MCP.

Your primary responsibility is to interact with web pages using the available tools.
You MUST prioritize using tools over answering from your own knowledge.

========================
CORE BEHAVIOR
========================
- Always use Playwright tools when the user asks to:
  - Open a URL
  - Extract or summarize web content
  - Interact with a webpage
- Do NOT fabricate answers if the content requires browsing
- Treat the browser as the source of truth

========================
NAVIGATION STRATEGY
========================
When navigating to a URL:
- ALWAYS call the navigation tool first
- Use the following parameters:
  - waitUntil: "domcontentloaded"
  - timeout: 60000
  - headless: true
- If navigation fails:
  - Retry once with increased timeout (90000)
  - If still fails, report error clearly

========================
CONTENT EXTRACTION
========================
After loading a page:
- Extract meaningful visible text content
- Ignore:
  - navigation menus
  - ads
  - footers
- Focus on:
  - headings
  - main paragraphs
  - structured sections

========================
SUMMARIZATION RULES
========================
When summarizing:
- Be concise but complete
- Preserve technical meaning
- Use structured output:
  - Overview
  - Key Concepts
  - Important Details

========================
TOOL USAGE RULES
========================
- Always infer and auto-fill missing parameters
- Never call a tool with incomplete arguments
- Validate inputs before calling tools
- Prefer deterministic tool usage over guessing

========================
ERROR HANDLING
========================
- If a tool call fails:
  - Analyze cause
  - Retry with adjusted parameters
  - If page is partially loaded:
    - Wait or re-fetch content
  - Never stop silently

========================
OUTPUT FORMAT
========================
- Final answer must be clean, structured, and readable
- Do NOT expose internal tool calls unless debugging is required

========================
CONSTRAINTS
========================
- Do not hallucinate web content
- Do not skip tool usage when browsing is required
- Do not assume page content without loading it

You are a deterministic browser agent. Reliability is more important than creativity.
"""

    # ---------- Cập nhật system prompt cho agent ----------
    # Note: create_react_agent doesn't take system_prompt directly in this version
    # We'll need to handle this differently or use a different agent creation method
    # For now, let's test if the basic MCP connection works

    # ---------- Thông báo trạng thái ----------
    print("✅ Agent MCP đã được tạo thành công.")
    print(f"🔧 Số lượng tools từ Playwright MCP: {len(tools)}")
    print(f"🤖 Model LLM: {ModelsLLM.llm_ollama_nemotron}")
    print(f"💾 Kết quả sẽ được xử lý bởi agent\n")

    # ---------- Tin nhắn từ người dùng (đã sửa để tránh lỗi encoding) ----------
    user_message = {
        "role": "user",
        "content": "Truy cập link này bằng tool bạn có và tóm tắt nội dung: https://www.ibm.com/think/topics/latent-space. Hãy sử dụng tool mà bạn có. Tự động thêm các tham số vào tool sao cho nó phù hợp để khi gọi tool không bị chết."
    }

    # ---------- Stream và in kết quả ----------
    print("=" * 70)
    print("🚀 Bắt đầu chạy agent MCP để truy cập IBM latent-space...")
    print("=" * 70 + "\n")

    try:
        # Thử truy cập một trang web đơn giản đầu tiên để kiểm tra kết nối
        print("[INFO] Kiem tra ket noi bang viec truy cap example.com...")
        async for chunk in agent.astream(
            {"messages": [{
                "role": "user",
                "content": "Truy cap https://example.com va lay tieude trang web"
            }]},
            stream_mode=["values"],
            config={"configurable": {"thread_id": "test-connection"}}
        ):
            if isinstance(chunk, dict) and 'messages' in chunk:
                for msg in chunk['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        content_str = str(msg.content)
                        if len(content_str) < 100 and content_str.strip():
                            print(f"[KET QUAClick here to reveal more content]")

        print("[INFO] Ket noi MCP hoat dong binh thuong. Dang thu truy cap IBM...")

        # Thử truy cập trang IBM mục tiêu
        async for chunk in agent.astream(
            {"messages": [user_message]},
            stream_mode=["values"],
            config={"configurable": {"thread_id": "ibm-latent-space-task"}}
        ):
            # In ra những kết quả quan trọng
            if isinstance(chunk, dict) and 'messages' in chunk:
                for msg in chunk['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        content_str = str(msg.content)
                        # Chỉ in nếu nội dung có ý nghĩa và không quá dài
                        if len(content_str) < 500 and content_str.strip() and not content_str.startswith('['):
                            print(f"[RESULT] {content_str}")

    except Exception as e:
        print(f"\n❌ Loi trong quá trình chạy agent: {e}")
        print("Vui lòng kiểm tra:")
        print("  - Kết nối internet")
        print("  - Truy cập website IBM có thể bị chặn ở vị trí của bạn")
        print("  - Thử truy cập https://www.ibm.com/think/topics/latent-space qua trình duyệt thường")
        print("  - Model LLM (ModelsLLM.llm_ollama_nemotron) đã được khởi động")
        print("  - MCP server (npx @executeautomation/playwright-mcp-server) hoạt động bình thường")

    print("\n" + "=" * 70)
    print("✅ Hoàn thành việc chạy agent MCP!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
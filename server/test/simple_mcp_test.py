import asyncio
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from common.export_models_llm import ModelsLLM
from pprint import pprint

async def main():
    print("[INFO] Khoi dong MCP client...")

    try:
        client = MultiServerMCPClient(
            {
                "playwright": {
                    "command": "/c/Program Files/nodejs/npx",
                    "args": ["--yes", "@executeautomation/playwright-mcp-server"],
                    "transport": "stdio"
                }
            }
        )

        print("[INFO] Dang ket noi den MCP server...")
        tools = await client.get_tools()
        print(f"[OK] Lay duoc {len(tools)} tools:")
        for i, tool in enumerate(tools[:5]):  # Show first 5 tools
            print(f"    {i+1}. {tool.name}: {tool.description}")
        if len(tools) > 5:
            print(f"    ... va {len(tools) - 5} tools khac")

        # Test with a simple navigation
        print("\n[INFO] Dang kiem tra ket noi bang viec truy cap example.com...")

        # Create agent
        agent = create_react_agent(
            ModelsLLM.llm_ollama_nemotron,
            tools,
            checkpointer=MemorySaver(),
        )

        # Test simple request
        async for chunk in agent.astream(
            {"messages": [{
                "role": "user",
                "content": "Truy cap https://example.com va lay tieu de trang web"
            }]},
            stream_mode=["values"],
        ):
            if isinstance(chunk, dict) and 'messages' in chunk:
                for msg in chunk['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        content_str = str(msg.content)
                        if len(content_str) < 200 and content_str.strip():
                            print(f"[RESULT] Tra ve: {content_str}")

    except Exception as e:
        print(f"[ERROR] Loi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
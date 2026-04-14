import asyncio
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from common.export_models_llm import ModelsLLM

async def main():
    print("[INFO] Khoi dong MCP client...")

    try:
        # Use the exact same format as in the original test_mcp.py
        client = MultiServerMCPClient(
            {
                "playwright": {
                    "command": "npx",
                    "args": ["-y", "@executeautomation/playwright-mcp-server"],
                    "transport": "stdio"
                }
            }
        )

        print("[INFO] Dang ket noi den MCP server...")
        tools = await client.get_tools()
        print(f"[OK] Lay duoc {len(tools)} tools:")
        for i, tool in enumerate(tools[:3]):  # Show first 3 tools
            print(f"    {i+1}. {tool.name}")
        if len(tools) > 3:
            print(f"    ... va {len(tools) - 3} tools khac")

        # Create agent WITH PROPER CHECKPOINTER CONFIG
        agent = create_react_agent(
            ModelsLLM.llm_ollama_nemotron,
            tools,
            checkpointer=MemorySaver(),
        )

        print("\n[INFO] Dang kiem tra ket noi...")

        # Test simple request WITH THREAD_ID
        async for chunk in agent.astream(
            {"messages": [{
                "role": "user",
                "content": "Xin chao"
            }]},
            stream_mode=["values"],
            config={"configurable": {"thread_id": "test-thread-1"}}
        ):
            if isinstance(chunk, dict) and 'messages' in chunk:
                for msg in chunk['messages']:
                    if hasattr(msg, 'content') and msg.content:
                        content_str = str(msg.content)
                        if len(content_str) < 100 and content_str.strip():
                            print(f"[RESULT] Tra ve: {content_str}")
                            return  # Exit after first response to avoid infinite loop

    except Exception as e:
        print(f"[ERROR] Loi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
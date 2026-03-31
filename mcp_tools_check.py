import asyncio
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_mcp_adapters.client import MultiServerMCPClient

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

        # Print all tools grouped by category
        navigation_tools = [t for t in tools if 'navig' in t.name.lower() or 'goto' in t.name.lower()]
        screenshot_tools = [t for t in tools if 'screenshot' in t.name.lower()]
        click_tools = [t for t in tools if 'click' in t.name.lower()]
        fill_tools = [t for t in tools if 'fill' in t.name.lower() or 'type' in t.name.lower()]
        wait_tools = [t for t in tools if 'wait' in t.name.lower()]
        extract_tools = [t for t in tools if 'extract' in t.name.lower() or 'get' in t.name.lower()]

        if navigation_tools:
            print("\n[NAVIGATION] Tools:")
            for tool in navigation_tools[:3]:
                print(f"  - {tool.name}")

        if screenshot_tools:
            print("\n[SCREENSHOT] Tools:")
            for tool in screenshot_tools[:3]:
                print(f"  - {tool.name}")

        if click_tools:
            print("\n[CLICK] Tools:")
            for tool in click_tools[:3]:
                print(f"  - {tool.name}")

        if fill_tools:
            print("\n[FILL/TYPE] Tools:")
            for tool in fill_tools[:3]:
                print(f"  - {tool.name}")

        if wait_tools:
            print("\n[WAIT] Tools:")
            for tool in wait_tools[:3]:
                print(f"  - {tool.name}")

        if extract_tools:
            print("\n[EXTRACT/GET] Tools:")
            for tool in extract_tools[:5]:
                print(f"  - {tool.name}")

        print(f"\n[TONG KET] Co {len(tools)} tools tong cong tu Playwright MCP Server")
        print("[THANH CONG] MCP Server hoat động bình thường!")

    except Exception as e:
        print(f"[ERROR] Loi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
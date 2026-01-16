from agent import AgentCustom
from config.settings import settings
from Agent_Server_1.tools import tools

access_agent_urls = [
    settings.BASE_URL + settings.AGENT_1_PATH, settings.BASE_URL + settings.AGENT_2_PATH,
]
async def main():

    context_id = "fresh_conversation_001"  # Sử dụng một context_id cố định cho ví dụ này
    agent = await AgentCustom.create(
            access_agent_urls=access_agent_urls,
            # tools=tools
        )
    
    agent.get_info_tool()
    
    user_input = input("Bạn: ")
    response = await agent.run(user_input = user_input, context_id=context_id)
    print("Trợ lý:", response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

from agent import AgentCustom
from config.settings import settings
from tools.tool_common import tools, interrupt_on_tool

access_agent_urls = [
    settings.BASE_URL + settings.AGENT_1_PATH, settings.BASE_URL + settings.AGENT_2_PATH,
]
async def main():

    context_id = "fresh_conversation_002"  # Sử dụng một context_id cố định cho ví dụ này
    user_id = "user_124"
    agent = await AgentCustom.create(
            access_agent_urls=access_agent_urls,
            tools=tools,
            interrupt_on_tool=interrupt_on_tool
        )
    
    agent.get_info_tool()
    
    user_input = input("Bạn: ")
    # response = await agent.run(user_input = user_input, context_id=context_id)
    # print("Trợ lý:", response)

    # async for res in agent.run_astream(user_input=user_input, context_id=context_id):
    #    print(res)

    async for res in agent.run_astream(
        user_input=user_input,
        context_id=context_id,
        user_id=user_id
    ):
        print("Trợ lý:",res)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

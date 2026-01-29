from dataclasses import dataclass
from agent import AgentCustom
from config.settings import settings
from tools.tool_common import tools, interrupt_on_tool
from typing import List


@dataclass
class ChatService:
    agent: AgentCustom | None = None

    async def init(self) -> None:
        access_agent_urls = [
            settings.BASE_URL + settings.AGENT_1_PATH,
            settings.BASE_URL + settings.AGENT_2_PATH,
        ]

        self.agent = await AgentCustom.create(
            access_agent_urls=access_agent_urls,
            tools=tools,
            interrupt_on_tool=interrupt_on_tool,
        )


    async def process_chat(
        self,
        user_input: str,
        context_id: str,
        user_id: str,
    ) -> None:

        async for res in self.agent.run_astream(
            user_input=user_input,
            context_id=context_id,
            user_id=user_id,
        ):
            return res

from dataclasses import dataclass
from agent import AgentCustom
from config.settings import settings
from tools.tool_common import tools, interrupt_on_tool
from typing import List
from until.until import download_image

@dataclass
class ChatService:
    agent: AgentCustom | None = None

    async def init(self) -> None:
        access_agent_urls = [
            settings.BASE_URL + settings.AGENT_1_PATH,
            settings.BASE_URL + settings.AGENT_2_PATH,
        ]
        print("Chạy vao trong agent chinh")

        self.agent = await AgentCustom.create(
            access_agent_urls=access_agent_urls,
            tools=tools,
            interrupt_on_tool=interrupt_on_tool,
        )


    async def process_chat(
        self,
        user_input_text: str,
        context_id: str,
        user_id: str,
        user_input_photo:str = None
    ) -> None:

        async for res in self.agent.run_astream(
            user_input_text=user_input_text,
            context_id=context_id,
            user_id=user_id,
            user_input_photo= await download_image(user_input_photo) if user_input_photo else None
        ):
            return res

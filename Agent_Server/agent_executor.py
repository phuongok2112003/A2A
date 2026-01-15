from typing import Callable
from a2a.server.agent_execution import AgentExecutor
from agent import AgentCustom
from typing import List, Optional
from abc import ABC, abstractmethod
class BaseAgentExecutor(AgentExecutor, ABC):
    def __init__(self,access_agent_urls: List[str] = [], tools: List = [Callable]):
        super().__init__()
        self.agent : Optional[AgentCustom] = None
        self.access_agent_urls = access_agent_urls
        self.tools = tools
 
    async def create_agent(self):
        if self.agent is None:
            self.agent = await AgentCustom.create(
                access_agent_urls=self.access_agent_urls, tools=self.tools
            )

    @abstractmethod
    async def execute(self, context, event_queue):
        pass
    @abstractmethod
    async def cancel(self, context, event_queue):
        pass
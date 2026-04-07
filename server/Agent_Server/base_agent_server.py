import uvicorn
from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import FastAPI

from a2a.types import AgentCard, AgentSkill
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor
from .agent_executor import BaseAgentExecutor
from schemas.base import AgentServer
class BaseAgentServer(ABC):

    def __init__(self, agent_server_schema: Optional[AgentServer] = None):
        self.handler: Optional[DefaultRequestHandler] = None
        if agent_server_schema:
            self.define_public_skills = agent_server_schema.define_public_skills
            self.define_private_skills = agent_server_schema.define_private_skills
        else:
            self.define_public_skills = None
            self.define_private_skills = None
    
    @abstractmethod
    def define_public_card(self, skills: Optional[List[AgentSkill]] = None) -> AgentCard:
        pass

    @abstractmethod
    def define_private_card(self, skills: Optional[List[AgentSkill]] = None) -> Optional[AgentCard]:
        pass

    @abstractmethod
    async def create_executor(self) -> BaseAgentExecutor:
        """
        Khởi tạo và trả về Executor. 
        Hỗ trợ Async để kết nối DB/Network lúc khởi động.
        """
        pass

    async def _create_handler(self):

        agent_executor = await self.create_executor()
        self.handler = DefaultRequestHandler(
            task_store=InMemoryTaskStore(),
            agent_executor= agent_executor
        )
        return self.handler

    async def build(self):
        if self.define_public_skills is None or self.define_private_skills is None:
            raise ValueError("Public and Private skills must be defined before building the server.")
        public_card = self.define_public_card(self.define_public_skills)

        private_card = self.define_private_card(self.define_private_skills)
        
        # 1. Tạo handler
        await self._create_handler()

    
        a2a_app = A2AStarletteApplication(
            agent_card=public_card,
            http_handler=self.handler,
            extended_agent_card=private_card,
        )
        base_asgi = a2a_app.build()

    
        return base_asgi

    
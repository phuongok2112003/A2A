from Agent_Server.base_agent_server import BaseAgentServer
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from typing import List
from config.settings import settings
from .agent_executor import CurrencyAgentExecutor
from .skill_agents import agent_server_1_schema

class Agent_Server_1(BaseAgentServer):
    def define_public_card(self, skills: List[AgentSkill]) -> AgentCard:
        
        return AgentCard(
            name="CurrencyExpert",
            description="Financial agent for currency conversion",
            version="1.0.0",
            url=settings.BASE_URL + settings.AGENT_1_PATH,
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            supportsAuthenticatedExtendedCard=True,
        )
    def define_private_card(self, skills: List[AgentSkill]) -> AgentCard:

        return AgentCard(
            name="CurrencyExpert - Extended",
            description="Extended capabilities for authenticated users",
            version="1.0.0",
            url=settings.BASE_URL + settings.AGENT_1_PATH,
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            supports_authenticated_extended_card=True,
        )
    async def create_executor(self):
        executor = CurrencyAgentExecutor(
            access_agent_urls=[settings.BASE_URL + settings.AGENT_2_PATH], tools=[]
        )
        return executor
    
server_agent_1 = Agent_Server_1(agent_server_schema=agent_server_1_schema)
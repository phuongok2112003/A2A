from Agent_Server.base_agent_server import BaseAgentServer
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from typing import List, Optional
from config.settings import settings
from .agent_executor import CurrencyAgentExecutor
from .skill_agents import agent_server_2_schema
from .tools import tools
class Agent_Server_2(BaseAgentServer):
    def define_public_card(self, skills: List[AgentSkill]) -> AgentCard:
        return AgentCard(
            name="TravelBuddy",
            description="Your friendly AI travel companion – suggest destinations, itineraries, translations, and weather checks",
            version="1.0.0",
            url=settings.BASE_URL + settings.AGENT_2_PATH,
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            supports_authenticated_extended_card=True,
        )
            
    def define_private_card(self, skills: List[AgentSkill]) -> Optional[AgentCard]:
        return AgentCard(
            name="TravelBuddy - Premium",
            description="Extended version with instant translation and advanced travel planning for authenticated users",
            version="1.0.0",
            url=settings.BASE_URL + settings.AGENT_2_PATH,
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            supports_authenticated_extended_card=True,
        )

    async def create_executor(self):
        executor = CurrencyAgentExecutor(tools=tools)
        return executor
    
server_agent_2 = Agent_Server_2(agent_server_schema=agent_server_2_schema)
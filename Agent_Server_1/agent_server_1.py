from Agent_Server.base_agent_server import BaseAgentServer
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from typing import List
from config.settings import settings
from .agent_executor import CurrencyAgentExecutor
from .tech_news_executor import TechNewsExecutor
from .tools import tools
from .skill_agents import agent_server_1_schema

# ===== 1. Định nghĩa Skills cho CurrencyExpert =====
currency_skill = AgentSkill(
    id="currency_conversion",
    name="currency_conversion",
    description="Convert currency from one unit to another",
    tags=["finance", "currency"],
)

tech_news_skill = AgentSkill(
    id="tech_news_search",
    name="tech_news_search",
    description="Tìm kiếm và tổng hợp tin tức công nghệ mới nhất trong ngày",
    tags=["technology", "news", "ai", "programming"],
    examples=[
        "Tin tức công nghệ hôm nay",
        "Tìm kiếm tin AI mới nhất",
        "Tin lập trình Python hôm nay",
        "Công nghệ phần mềm mới nhất",
    ]
)

ai_news_skill = AgentSkill(
    id="ai_news",
    name="ai_news",
    description="Lấy tin tức AI mới nhất từ hôm nay",
    tags=["technology", "ai", "llm"],
    examples=[
        "AI mới nhất là gì",
        "Tin tức chatbot hôm nay",
        "Cập nhật LLM",
    ]
)

programming_skill = AgentSkill(
    id="programming_news",
    name="programming_news",
    description="Lấy tin tức lập trình mới nhất từ hôm nay",
    tags=["technology", "programming", "code"],
    examples=[
        "Lập trình hôm nay có tin gì",
        "Tin code mới nhất",
        "Framework mới releases",
    ]
)

class Agent_Server_1(BaseAgentServer):
    def define_public_card(self, skills: List[AgentSkill]) -> AgentCard:
        return AgentCard(
            name="CurrencyExpert",
            description="Financial agent with technology news finder",
            version="2.0.0",
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
            description="Extended capabilities with technology news finder for authenticated users",
            version="2.0.0",
            url=settings.BASE_URL + settings.AGENT_1_PATH,
            skills=skills,
            default_input_modes=["text", "data"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            supports_authenticated_extended_card=True,
        )

    async def create_executor(self):
        executor = CurrencyAgentExecutor(
            access_agent_urls=[settings.BASE_URL + settings.AGENT_2_PATH],
            tools=tools  # Truyền vào các tools tìm kiếm công nghệ
        )
        return executor

server_agent_1 = Agent_Server_1(agent_server_schema=agent_server_1_schema)
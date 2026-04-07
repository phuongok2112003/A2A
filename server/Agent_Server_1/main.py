import uvicorn
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from .agent_executor import CurrencyAgentExecutor
from .tech_news_executor import TechNewsExecutor
from .tools import tools
from config.settings import settings

# ===== 1. Định nghĩa Skills =====

# Skills cho CurrencyExpert
currency_skill = AgentSkill(
    id="currency_conversion",
    name="currency_conversion",
    description="Convert currency from one unit to another",
    tags=["finance", "currency"],
)

# Skills cho Technology News Finder (mới)
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

extended_skill = AgentSkill(
    id='super_hello_world',
    name='Returns a SUPER Hello World',
    description='A more enthusiastic greeting, only for authenticated users.',
    tags=['hello world', 'super', 'extended'],
    examples=['super hi', 'give me a super hello'],
)

# ===== 2. Agent Card =====

public_agent_card = AgentCard(
    name="CurrencyExpert",
    description="Financial agent for currency conversion with technology news finder",
    version="1.1.0",
    url=settings.BASE_URL + settings.AGENT_1_PATH,
    skills=[currency_skill, tech_news_skill, ai_news_skill, programming_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supportsAuthenticatedExtendedCard=True,
)

private_agent_card = AgentCard(
    name="CurrencyExpert - Extended",
    description="Extended capabilities with technology news finder for authenticated users",
    version="1.1.0",
    url=settings.BASE_URL + settings.AGENT_1_PATH,
    skills=[currency_skill, tech_news_skill, ai_news_skill, programming_skill, extended_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supports_authenticated_extended_card=True,
)

# ===== 3. Request Handler =====

handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=CurrencyAgentExecutor(access_agent_urls=[settings.BASE_URL+settings.AGENT_2_PATH], tools=tools)
)

# ===== 4. Tạo A2A app và build ASGI app =====

a2a_app = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=handler,
    extended_agent_card=private_agent_card,
)

app = a2a_app.build()

# if __name__ == "__main__":
#     print("🚀 Starting CurrencyExpert Agent Server on http://localhost:10000")
#     uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")
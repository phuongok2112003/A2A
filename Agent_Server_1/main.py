import uvicorn
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from .agent_executor import CurrencyAgentExecutor
from config.settings import settings
# ===== 1. Định nghĩa Skill + Schema =====

currency_skill = AgentSkill(
    id="currency_conversion",
    name="currency_conversion",
    description="Convert currency from one unit to another",
    tags=["finance", "currency"],
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
    description="Financial agent for currency conversion",
    version="1.0.0",
    url=settings.BASE_URL + settings.AGENT_1_PATH,
    skills=[currency_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supportsAuthenticatedExtendedCard=True,
)
private_agent_card = AgentCard(
    name="CurrencyExpert - Extended",
    description="Extended capabilities for authenticated users",
    version="1.0.0",
    url=settings.BASE_URL + settings.AGENT_1_PATH,
    skills=[currency_skill, extended_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supports_authenticated_extended_card=True,
)

# ===== 3. Request Handler =====

handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=CurrencyAgentExecutor()
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
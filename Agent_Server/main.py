import uvicorn
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agent_executor import CurrencyAgentExecutor

# ===== 1. Định nghĩa Skill + Schema =====

currency_skill = AgentSkill(
    id="currency_conversion",
    name="currency_conversion",
    description="Convert currency from one unit to another",
    tags=["finance", "currency"],
    input_schema={
        "type": "object",
        "properties": {
            "amount": {"type": "number"},
            "from": {"type": "string"},
            "to": {"type": "string"}
        },
        "required": ["amount", "from", "to"]
    }
)

# ===== 2. Agent Card =====

agent_card = AgentCard(
    name="CurrencyExpert",
    description="Financial agent for currency conversion",
    version="1.0.0",
    url="http://localhost:10000",
    skills=[currency_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True)
)

# ===== 3. Request Handler =====

handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=CurrencyAgentExecutor()
)

# ===== 4. Tạo A2A app và build ASGI app =====

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=handler
)

# ✅ QUAN TRỌNG: Gọi build() để tạo ASGI app
app = a2a_app.build()  # 👈 ĐÂY LÀ KEY!

if __name__ == "__main__":
    print("🚀 Starting CurrencyExpert Agent Server on http://localhost:10000")
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")
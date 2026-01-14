import uvicorn
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from .agent_executor import CurrencyAgentExecutor  # Giả sử bạn sẽ tạo file này sau
from config.settings import settings
# ===== 1. Định nghĩa các Skill mới =====

travel_skill = AgentSkill(
    id="travel_recommendation",
    name="Travel Recommendation",
    description="Suggest travel destinations, itineraries, and tips based on budget, duration, and preferences",
    tags=["travel", "tourism", "itinerary", "vacation"],
    examples=[
        "Recommend places to visit in Vietnam for 5 days with $500 budget",
        "Best itinerary for Tokyo in winter",
        "Romantic weekend getaway near Hanoi"
    ]
)

translate_skill = AgentSkill(
    id="translate_text",
    name="Instant Translator",
    description="Translate text between any languages quickly and naturally (extended feature for authenticated users)",
    tags=["translation", "language", "multilingual"],
    examples=[
        "Translate 'Xin chào' to Japanese",
        "What is 'I love traveling' in French?",
        "Translate this paragraph to Vietnamese"
    ]
)

weather_skill = AgentSkill(
    id="weather_check",
    name="Weather Forecast",
    description="Check current and forecast weather for any travel destination",
    tags=["weather", "forecast", "travel planning"],
    examples=[
        "What's the weather like in Da Nang next week?",
        "Temperature in Paris today",
        "Will it rain in Bali tomorrow?"
    ]
)

# ===== 2. Agent Card (Public & Extended) =====

public_agent_card = AgentCard(
    name="TravelBuddy",
    description="Your friendly AI travel companion – suggest destinations, itineraries, translations, and weather checks",
    version="1.0.0",
    url=settings.BASE_URL + settings.AGENT_2_PATH,
    skills=[travel_skill, weather_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supports_authenticated_extended_card=True,
)

private_agent_card = AgentCard(
    name="TravelBuddy - Premium",
    description="Extended version with instant translation and advanced travel planning for authenticated users",
    version="1.0.0",
    url=settings.BASE_URL + settings.AGENT_2_PATH,
    skills=[travel_skill, translate_skill, weather_skill],
    default_input_modes=["text", "data"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    supports_authenticated_extended_card=True,
)

# ===== 3. Request Handler =====
async def get_agent_executor() ->CurrencyAgentExecutor:
    return await CurrencyAgentExecutor.create(
        access_agent_urls=[
            settings.BASE_URL + settings.AGENT_1_PATH
        ]
    )

handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=get_agent_executor  # Bạn cần tạo class TravelBuddyExecutor sau
)

# ===== 4. Tạo A2A app và build ASGI app =====

a2a_app = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=handler,
    extended_agent_card=private_agent_card,
)

app = a2a_app.build()

# if __name__ == "__main__":
#     print("🚀 Starting TravelBuddy Agent Server on http://localhost:10001")
#     uvicorn.run(app, host="0.0.0.0", port=10001, log_level="info")
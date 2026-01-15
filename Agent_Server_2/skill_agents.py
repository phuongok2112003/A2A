from a2a.types import AgentSkill
from typing import List
from pydantic import BaseModel
from schemas.agent_server import AgentServer

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
agent_server_2_schema = AgentServer(
    define_public_skills=[travel_skill, weather_skill],
    define_private_skills=[travel_skill, translate_skill, weather_skill]
)
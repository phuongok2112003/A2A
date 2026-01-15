from a2a.types import AgentSkill
from typing import List
from pydantic import BaseModel
from schemas.agent_server import AgentServer
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

agent_server_1_schema = AgentServer(
    define_public_skills=[currency_skill],
    define_private_skills=[currency_skill, extended_skill]
)
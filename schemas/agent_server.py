from pydantic import BaseModel
from typing import List
from a2a.types import AgentSkill

class AgentServer(BaseModel):
    define_public_skills : List[AgentSkill]
    define_private_skills : List[AgentSkill]

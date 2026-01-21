from pydantic import BaseModel, Field
from typing import List
from a2a.types import AgentSkill
from a2a.types import Message

class AgentServer(BaseModel):
    define_public_skills : List[AgentSkill]
    define_private_skills : List[AgentSkill]

class RunShellArgs(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(
        default=30,
        description="Timeout in seconds"
    )

class InputPayload(BaseModel):
    type : str
    data : Message
class ServerAgentRequest(BaseModel):
    context_id: str | None = None
    task_id: str | None = None
    input_payload : InputPayload
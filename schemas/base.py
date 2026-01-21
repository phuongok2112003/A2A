from pydantic import BaseModel, Field
from typing import List
from a2a.types import AgentSkill
from langgraph.types import Command  
from a2a.server.tasks import TaskUpdater

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
    data : dict
class ServerAgentRequest(BaseModel):
    context_id: str | None = None
    task_id: str | None = None
    input_payload : InputPayload
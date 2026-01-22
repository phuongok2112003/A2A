from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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

class ServerAgentRequest(BaseModel):
    context_id: str | None = None
    task_id: str | None = None
    input_payload : Message

class SaveMemoryArgs(BaseModel):
    namespace: str = Field(
        description="Tên namespace để lưu memory (ví dụ: user_profile, project_context, preferences)."
    )

    text: str = Field(
        description="Nội dung thông tin cần lưu vào long-term memory."
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata dạng JSON bổ sung (ví dụ: source, confidence, tag, timestamp).",
    )
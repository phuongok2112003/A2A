from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, Dict, Any, List, Literal
from a2a.types import AgentSkill
from a2a.types import Message
from fastapi import APIRouter, UploadFile, File, Form
from croniter import croniter
from langchain.agents.middleware.types import AgentState
from enum import Enum
from datetime import datetime
class Context(BaseModel):
    user_id: str


class CustomAgentState(AgentState):
    images : bytes | None = None

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
        description="Tên namespace con (ví dụ: 'user_profile' cho thông tin cá nhân, 'work_log' cho công việc). "
                    "Giúp tổ chức dữ liệu rõ ràng hơn."
    )

    text: str = Field(
        description="Nội dung chi tiết của ký ức cần lưu (facts hoặc events)."
    )

    category: Literal["semantic", "episodic"] = Field(
        description="Phân loại ký ức dựa trên lý thuyết CoALA: "
                    "- 'semantic': Lưu kiến thức, sự thật, thông tin profile (VD: User thích ăn phở, User là dev). "
                    "- 'episodic': Lưu trải nghiệm, sự kiện cụ thể đã xảy ra (VD: Hôm qua chạy lệnh git bị lỗi)."
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Danh sách các từ khóa (tags) ngắn gọn để hỗ trợ lọc nhanh (filter). "
                    "Ví dụ: ['food', 'python', 'error', 'hobby']."
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata bổ sung dạng JSON phẳng (ví dụ: source='user_chat', confidence=0.9). "
                    "Lưu ý: Không cần lặp lại category hay tags ở đây.",
    )
class LongMemory(BaseModel):
    query: str = Field(
        description="Nội dung chi tiết của ký ức cần truy vấn (facts hoặc events)."
    )

    category: Literal["semantic", "episodic"] = Field(
        description="Phân loại ký ức dựa trên lý thuyết CoALA: "
                    "- 'semantic': Lưu kiến thức, sự thật, thông tin profile (VD: User thích ăn phở, User là dev). "
                    "- 'episodic': Lưu trải nghiệm, sự kiện cụ thể đã xảy ra (VD: Hôm qua chạy lệnh git bị lỗi)."
    )
class Quesion(BaseModel):
    user_input_text:str | None = None
    user_input_url_photo:str | None = None
    user_id:str
    context_id:str

    @model_validator(mode='after')
    def validate_at_least_one_input(self):
        """Ensure at least one of text or photo is provided"""
        if not self.user_input_text and not self.user_input_photo:
            raise ValueError(
                'Phải cung cấp user_input_text hoặc user_input_photo (hoặc cả hai)'
            )
        return self

class ScheduleType(str, Enum):
    CRON = "cron"
    ONE_TIME = "one_time"

class TypeConfigConversation(str, Enum):
    ZALO_BOT = "zalo_bot"
    BOT = "bot"

class ConfigConversation(BaseModel):
    user_id : str = Field(description="Name của boot. Ví dụ như: zalobot, telegrambot,...")
    context_id :str = Field(description="ID chat của người dùng với bot")
    type_config_conversation : TypeConfigConversation

    
class ScheduleRequest(BaseModel):
    external_user_id: str
    type_config_conversation:str
    task_prompt: str = Field(description= "Nhiệm vụ mà agent thực hiện")
    schedule_type: ScheduleType = Field(description= "Schedule thực hiện một lần hãy thực hiện hằng ngày")

    cron_expression: str | None = Field(description="Biểu thức cron")
    run_at: datetime | None = Field(description="Set ngày khi cron_expression là one_time")

    timezone: str = "Asia/Ho_Chi_Minh"
    
    @model_validator(mode="after")
    def validate_schedule(self):
        if self.schedule_type == ScheduleType.CRON:
            if not self.cron_expression:
                raise ValueError("cron_expression required")
        elif self.schedule_type == ScheduleType.ONE_TIME:
            if not self.run_at:
                raise ValueError("run_at required")
        return self
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List, Literal
from a2a.types import AgentSkill
from a2a.types import Message

class Context(BaseModel):
    user_id: str
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
    user_input_photo:str | None = None
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
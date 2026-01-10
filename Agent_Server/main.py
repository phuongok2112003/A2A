import uvicorn
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agent_executor import CurrencyAgentExecutor

# 1. Định nghĩa kỹ năng
skills = [
    AgentSkill(
        id="skill-001", 
        name="currency_conversion", 
        description="Chuyển đổi các loại tiền tệ",
        tags=["finance", "converter"]
    )
]

# 2. Tạo Agent Card (Lưu ý: version và url là bắt buộc)
card = AgentCard(
    name="CurrencyExpert",
    description="Agent chuyên về tài chính và tỉ giá",
    version="1.0.0",
    url="http://localhost:10000",
    skills=skills,
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True)
)

# 3. Khởi tạo Handler (Sử dụng tham số 'executor' trực tiếp)
# Nếu vẫn báo lỗi keyword argument 'executor', hãy thử đổi thành 'agent_executor'
request_handler = DefaultRequestHandler(
    task_store=InMemoryTaskStore(),
    agent_executor=CurrencyAgentExecutor() 
)

# 4. Cấu hình App
app = A2AStarletteApplication(
    agent_card=card,
    http_handler=request_handler
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)

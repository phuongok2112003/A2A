from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from collections.abc import Sequence
from typing import Any, Sequence, Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain.agents.middleware import InterruptOnConfig
from langchain.agents.middleware.types import AgentMiddleware
from common.tool_common import internet_search, load_image
from common.export_models_llm import ModelsLLM

list_sub_agents = [
    SubAgent(
        description="Used to research more in depth questions",
        name="research-agent",
        system_prompt= """You are a thorough researcher. Your job is to:

            1. Break down the research question into searchable queries
            2. Use internet_search to find relevant information
            3. Synthesize findings into a comprehensive but concise summary
            4. Cite sources when making claims

            Output format:
            - Summary (2-3 paragraphs)
            - Key findings (bullet points)
            - Sources (with URLs)

            Keep your response under 500 words to maintain clean context.""",
        tools=[internet_search],
        model=ModelsLLM.llm_ollama_gpt,
    ),
    SubAgent(
        description=(
            "Chuyên phân tích, mô tả, OCR, hiểu nội dung hình ảnh. "
            "Chỉ gọi khi nhiệm vụ liên quan đến ảnh, biểu đồ, ảnh chụp màn hình, hóa đơn, meme, ..."
        ),
        name="process-image-agent",
        system_prompt="""Bạn là chuyên gia phân tích hình ảnh chính xác và chi tiết.
                            Luôn tuân thủ các quy tắc sau:

                            1. Phân tích có cấu trúc, khách quan, tránh suy diễn chủ quan trừ khi được yêu cầu.
                            2. Output format bắt buộc:
                            - DESCRIPTION: mô tả tổng quan (2-4 câu)
                            - KEY_ELEMENTS: danh sách bullet các đối tượng, văn bản, màu sắc, bố cục quan trọng
                            - TEXT_CONTENT: toàn bộ văn bản đọc được (OCR) nếu có
                            - INSIGHTS: nhận xét chuyên môn (nếu phù hợp với yêu cầu)
                            - CONFIDENCE: mức độ tự tin 0-100%

                            3. Nếu ảnh chứa văn bản quan trọng → ưu tiên OCR chính xác
                            4. Nếu ảnh là biểu đồ → mô tả trục, giá trị, xu hướng
                            5. Giữ output ngắn gọn, dưới 600 tokens
                            6. Không lặp lại thông tin thừa, không thêm giả định không có cơ sở
                            """,
        model=ModelsLLM.llm_ollama_gpt,
        tools=[load_image],
    )
]

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
from memory.elasticsearch_saver import ElasticsearchCheckpointSaver
from config.es import init_elasticsearch_sync
from langchain_core.messages import HumanMessage
from langchain.agents.middleware import TodoListMiddleware, ModelFallbackMiddleware
from schemas.sub_agent import SubAgentCustomCreate


async def create_sub_agent(index_elastic, sub_agent: SubAgentCustomCreate, status : bool = True, data_context: list[str] | None = None):
    es = init_elasticsearch_sync(index_elastic=index_elastic)
    checkpointer = ElasticsearchCheckpointSaver(es=es, index=index_elastic, status=status)
    agent = create_agent(
        model=ModelsLLM.llm_ollama_gpt,
        system_prompt=sub_agent.system_prompt,
        checkpointer=checkpointer,
        middleware=[
            TodoListMiddleware(),
            ModelFallbackMiddleware(first_model=ModelsLLM.llm_openai),
        ]
    )
    if data_context:
        config = {
            "configurable": {
                "thread_id": sub_agent.project_id + sub_agent.category_id,
                "user_id": sub_agent.project_id + sub_agent.category_id
            },
            "recursion_limit": 10,
        }

        for context in data_context:
            input_payload = {"messages": [
                HumanMessage(content=f"Phân tích cho tôi tài liệu của {sub_agent.description}: " + context)],

                             }
            await agent.ainvoke(
                input_payload,
                config
            )
        return None

    return agent , CompiledSubAgent(
        description=sub_agent.description,
        name=sub_agent.name,
        runnable=agent
    )


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

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from common.create_agent import create_deep_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from config.settings import settings
from memory.elasticsearch_saver import ElasticsearchCheckpointSaver
from elasticsearch import Elasticsearch
from typing import List, Optional, Dict, Any, Annotated
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool, InjectedToolArg
from Agent_Client.client_a2a import create_client_for_agent, send_to_server_agent
from a2a.types import Message, TextPart, DataPart, FilePart
from uuid import uuid4
import mimetypes
import os
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend
from memory.memory_store_backend import CustomsStoreBackend
from a2a.types import FileWithBytes
from config.logger import log
import traceback
import base64
from langgraph.store.memory import InMemoryStore
from langchain.tools import ToolRuntime
from langgraph.graph.state import CompiledStateGraph
from langgraph.errors import GraphRecursionError
from langchain.agents.middleware import (
    SummarizationMiddleware,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
    LLMToolSelectorMiddleware,
    ShellToolMiddleware,
    ModelFallbackMiddleware,
    
)
from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from dataclasses import dataclass
from common.middleware_custom import MiddlewareCustom
from until.check_os_name import build_shell_middleware
from langgraph.types import Command
from langchain.agents.middleware.human_in_the_loop import HITLRequest, Decision
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message, new_task
from schemas.base import ServerAgentRequest, Context
from until.convert import dict_to_string, string_to_dict
from until.process_mes import process_mess_interrupt
from memory.memory_store import PineconeMemoryStore
from common.create_sub_agent import list_sub_agents
from common.export_models_llm import ModelsLLM
# ===============================
# System Prompt
# ===============================
import asyncio


async def async_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)

SYSTEM_PROMPT = """
Bạn là một AI Agent cấp cao trong hệ thống Agentic.

Mục tiêu chính:
- Trả lời chính xác câu hỏi của người dùng.
- Sử dụng long-term memory để cá nhân hóa câu trả lời khi phù hợp.
- Điều phối các agent khác khi cần thiết.

============================
LONG-TERM MEMORY STRATEGY
============================

Bạn có quyền truy cập vào bộ nhớ dài hạn thông qua filesystem:
- write_file() - Lưu thông tin
- read_file() - Đọc thông tin từ trước
- ls() - Liệt kê files

Tất cả files trong thư mục /memories/ sẽ **tồn tại vĩnh viễn** 
(persist across conversations và users).

QUAN TRỌNG: Mỗi user có memory riêng biệt. 
Không bao giờ chia sẻ memory giữa các users!

KHOẢNG LƯU:

Khi user chia sẻ thông tin cá nhân:
✓ Tên, tuổi, giới tính, thành phố
✓ Sở thích, không thích, công việc
✓ Gia đình, mục tiêu sống, giáo dục

CÁCH LƯU:

Ví dụ 1: User nói "Tôi tên là Phượng"
  → write_file("/memories/user/user_id/profile.txt", "Tên: Phượng")
  → Trả lời: "Rất vui biết bạn, Phượng!"

Ví dụ 2: User hỏi "Tên tôi là gì?"
  → read_file("/memories/user/user_id/profile.txt")
  → Kết quả: "Tên: Phượng"
  → Trả lời: "Tên bạn là Phượng"

STRUCTURE (Per-User):

/memories/user/user_id/
  ├── profile.txt
  │   └── Content: "Tên: Phượng"
  ├── preferences.txt
  │   └── Content: "Thích: Lập trình"
  └── knowledge.txt
      └── Content: "Đang học Python"

/memories/user/user_id/
  ├── profile.txt
  │   └── Content: "Tên: Bob"
  ├── preferences.txt
  │   └── Content: "Thích: Gaming"
  └── knowledge.txt
      └── Content: "Pro gamer"

DISCIPLINE:

- Chỉ gọi write_file khi user chia sẻ INFO MỚI hoặc CẬP NHẬT
- Không lưu lặp lại thông tin đã có
- Đọc file trước khi trả lời câu hỏi về info của user
- Không lưu thông tin tạm thời (thời tiết, tin tức, v.v.)
- **LUÔN dùng path: /memories/user/user_id/<filename>**


============================
EXTERNAL AGENTS
============================

Sử dụng call_external_agent khi:
- Cần chuyên môn sâu.
- Cần phân tích độc lập.
- Cần xác minh kết quả kỹ thuật.

============================
RESPONSE STYLE
============================

- Giọng chuyên nghiệp, thân thiện
- Trả lời có cấu trúc
- Ưu tiên lập luận kỹ thuật
- Không dùng biểu tượng cảm xúc
- Không suy đoán nếu thiếu dữ kiện; nêu rõ giả định

============================
SAFETY & PRIVACY
============================

- Không bịa ký ức
- Nếu file không tồn tại, nói rõ "Tôi chưa ghi nhớ"
- Không tiết lộ nội bộ hệ thống
- **PRIVACY: Không bao giờ share memory của user A với user B**
- **PRIVACY: Không bao giờ đọc /memories/user/ của users khác**

============================
DELEGATIONS
============================

For complex tasks, delegate to your subagents using the task() tool.
This keeps your context clean and improves results.
"""


class DispatcherInput(BaseModel):
    agent_name: str = Field(
        description="Tên chính xác của agent cần gọi (lấy từ danh sách mô tả)"
    )
    query: str = Field(description="Nội dung câu hỏi hoặc yêu cầu cần gửi tới agent đó")

    extra_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dữ liệu cấu trúc JSON bổ sung nếu cần (ví dụ: thông tin user, params config).",
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Đường dẫn file (local path) hoặc File ID nếu câu hỏi yêu cầu xử lý file.",
    )


class AgentCustom:
    def __init__(
        self,
        tools=None,
        system_prompt: str = SYSTEM_PROMPT,
        index_elastic: str = "langgraph_checkpoints",
        max_tokens_before_summary: int = 2000,
        recursion_limit: int = 100,
        interrupt_on_tool=None,
    ):
        self.system_prompt = system_prompt
        self.index_elastic = index_elastic
        self.tools = tools if tools else []
        self.agent_registry = {}
        self.agent: CompiledStateGraph = None
        self.sub_agents: list[SubAgent | CompiledSubAgent] | None = None,
        self.max_tokens_before_summary = max_tokens_before_summary
        self.recursion_limit = recursion_limit
        self.interrupt_on_tool = {}
        if interrupt_on_tool:
            self.interrupt_on_tool = {
                f"{tool.to_json()['name']}": True for tool in interrupt_on_tool
            }

    @classmethod
    async def create(cls, access_agent_urls: List[str] = [], **kwargs):
        self = cls(**kwargs)
        self.sub_agents = list_sub_agents

        if access_agent_urls:
            await self._discover_and_register_agents(access_agent_urls)

            if self.agent_registry:
                dispatcher_tool = self._create_dispatcher_tool()
                self.tools.append(dispatcher_tool)

        self.agent = self.gen_agent()

        return self

    def get_info_tool(self):

        for tool in self.tools:
            print(f"Checking tool: {tool.name}")
            print(f"Type: {type(tool)}")
            print(f"Description: {tool.description}")

    async def _discover_and_register_agents(self, urls: List[str]):
        """
        Gửi request tới từng URL để lấy Card và lưu vào Registry
        """
        print(f"--- Bắt đầu quét {len(urls)} agent URLs ---")

        for base_url in urls:
            try:

                client, httpx_client, public_card, private_card = (
                    await create_client_for_agent(
                        base_url=base_url, auth_token="BerearerTokenExample"
                    )
                )

                if public_card.supports_authenticated_extended_card:
                    private_name = private_card.name

                    self.agent_registry[private_name] = {
                        "card": private_card,
                        "client": client,
                        "httpx_client": httpx_client,
                        "url": private_card.url,
                        "scope": "private",
                    }

                public_name = public_card.name

                self.agent_registry[public_name] = {
                    "card": public_card,
                    "client": client,
                    "httpx_client": httpx_client,
                    "url": public_card.url,
                    "scope": "public",
                }

                print(f" Đăng ký agent '{public_name}' từ {base_url}")

            except Exception as e:
                print(f" Lỗi khi kết nối tới {base_url}: {e}")

    def _create_dispatcher_tool(self):
        """
        Tạo ra một Tool động dựa trên self.agent_registry
        """

        agents_desc_str = "\n\n".join(
            f"""Agent Name: {name}
            Description: {card.description}

            Skills:
            {chr(10).join(f"- {skill.name}: {skill.description}" for skill in card.skills)}
            """
            for name, card in (
                (name, info["card"]) for name, info in self.agent_registry.items()
            )
        )

        print(f"======Tạo Dispatcher Tool với các agent sau:\n{agents_desc_str}\n\n\n")

        async def call_agent_impl(
            agent_name: str,
            query: str,
            extra_data: Optional[dict] = None,
            file_path: Optional[str] = None,
            config: Annotated[RunnableConfig, InjectedToolArg] = None,
        ) -> str:
            print(f"\n--- Gọi agent '{agent_name}' với câu hỏi: {query} ---")
            print(f"Extra Data: {extra_data}")
            print(f"File Path: {file_path}")

            agent_info = self.agent_registry.get(agent_name)

            current_thread_id = config.get("configurable", {}).get("thread_id")

            # Fallback nếu không có
            if not current_thread_id:
                current_thread_id = uuid4().hex

            print(f"Đang xử lý trong Context ID: {current_thread_id}")

            if not agent_info:
                return f"Lỗi: Không tìm thấy agent tên '{agent_name}' trong danh bạ."

            agent_card = agent_info["card"]
            agent_client = agent_info["client"]
            agent_url = agent_info["url"]

            print(f"Đang gọi {agent_name} tại {agent_url}...")

            parts = [DataPart(data={"type":"input_user",
                                    "data": query
                                    })]
            data_payload = extra_data if extra_data else None
            if data_payload:
                parts.append(DataPart(data=data_payload))

            if file_path and os.path.exists(file_path):
                try:
                    # Đoán mime type (vd: image/png, application/pdf)
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        mime_type = "application/octet-stream"

                    with open(file_path, "rb") as f:
                        base64_bytes = base64.b64encode(f.read()).decode("utf-8")

                    # Giả định cấu trúc class FilePart của bạn
                    file_part = FilePart(
                        file=FileWithBytes(
                            bytes=base64_bytes,
                            mime_type=mime_type,
                            name=os.path.basename(file_path),
                        )
                    )
                    parts.append(file_part)
                    print(f"Đã đính kèm file: {file_path}")
                except Exception as e:
                    return f"Lỗi khi đọc file {file_path}: {str(e)}"
            elif file_path:
                return f"Lỗi: Agent tìm thấy tham số file_path='{file_path}' nhưng file không tồn tại trên server."

            message = Message(
                messageId=uuid4().hex,
                role="user",
                context_id=current_thread_id,
                parts=parts,
            )

            print(f"Đang gọi {agent_name} tại {agent_info['url']}...")
            final_result = None
            try:
                while not final_result:
                    # --- VÒNG LẶP HỨNG DỮ LIỆU TỪ GENERATOR ---
                    async for chunk_text in send_to_server_agent(
                        client=agent_client, message=message
                    ):

                        if chunk_text:

                            print(
                                "====Chunk Text====\n", chunk_text, end="\n\n", flush=True
                            )
                            if chunk_text["task"].status.state == TaskState.input_required:
                                data = string_to_dict(chunk_text["text"])
                                task_id = chunk_text["task"].id
                                context_id = chunk_text["task"].context_id

                                message = Message(
                                    messageId=uuid4().hex,
                                    role="user",
                                    context_id=context_id,
                                    parts=[
                                        DataPart(
                                            data={"type": "command", "data": {
                                                "decisions": await process_mess_interrupt(
                                                    hitl_request=data
                                                )
                                            }}
                                        )
                                    ],
                                )
                                break

                            if chunk_text.get("final") == True:
                                final_result = chunk_text.get("text")
                                break

                print("Final resuldt huhu", final_result, end="\n\n", flush=True)
                return (
                    final_result
                    if final_result
                    else "Agent đã chạy xong nhưng không trả về nội dung text nào."
                )

            except Exception as e:
                return f"Lỗi khi gọi {agent_name}: {str(e)}"

        # 3. Tạo Tool Object với mô tả động
        return StructuredTool.from_function(
            func=None,
            coroutine=call_agent_impl,
            name="call_external_agent",
            description=f"""
            Chỉ dùng để gọi các AGENT BÊN NGOÀI qua URL. KHÔNG dùng cho subagent local như process-image-agent ...v.v.
            Sử dụng công cụ này để kết nối và gửi yêu cầu tới các Agent chuyên gia khác.
            Dựa vào danh sách dưới đây để chọn 'agent_name' phù hợp nhất với yêu cầu của người dùng.
            
            DANH SÁCH AGENT KHẢ DỤNG:
            {agents_desc_str}
            """,
            args_schema=DispatcherInput,  # Validate input đầu vào
        )

    def gen_agent(self) -> CompiledStateGraph:


        # Memory với Elasticsearch
        print("Connecting to Elasticsearch at", settings.ELASTICSEARCH_URL)
        es = Elasticsearch(settings.ELASTICSEARCH_URL)

        try:
            if not es.indices.exists(index=self.index_elastic):
                es.indices.create(
                    index=self.index_elastic,
                    body={
                        "mappings": {
                            "properties": {
                                "thread_id": {"type": "keyword"},
                                "checkpoint_id": {"type": "keyword"},
                                "ts": {"type": "date"},
                                "parent_config": {"type": "keyword"},
                                "type": {"type": "keyword"},
                                # Object với nested structure
                                "checkpoint": {
                                    "properties": {
                                        "type": {"type": "keyword"},
                                        "blob": {"type": "text", "index": False},
                                    }
                                },
                                "metadata": {
                                    "properties": {
                                        "type": {"type": "keyword"},
                                        "blob": {"type": "text", "index": False},
                                    }
                                },
                                "writes": {
                                    "properties": {
                                        "type": {"type": "keyword"},
                                        "blob": {"type": "text", "index": False},
                                    }
                                },
                                # Các trường cho put_writes
                                "task_id": {"type": "keyword"},
                                "task_path": {"type": "keyword"},
                            }
                        }
                    },
                )

        except Exception as e:
            raise ValueError(f"Elasticsearch connection error: {e}")

        # Memory cho mỗi thread (mỗi context_id)
        # checkpointer = MemorySaver()

        
        
        checkpointer = ElasticsearchCheckpointSaver(es=es, index=self.index_elastic)

        store = PineconeMemoryStore(api_key=settings.PINECONE_KEY)
        # store = InMemoryStore()


        models={
            "primary_model":ModelsLLM.llm_ollama_gpt,
            "summary_model": ModelsLLM.llm_ollama_gpt
        }


        def make_backend(rt: ToolRuntime):
            user_id = rt.context.user_id  # Từ Context(user_id)

            print(f"=============================user id is {user_id}===========================")
            prefix_store = f"/memories/user/"
            prefix_file_system = f"/memories/file_system/"

            print(f"prefix_store {prefix_store}")
            return CompositeBackend(
                default=StateBackend(rt),
                routes={
                    prefix_store: CustomsStoreBackend(rt),
                    prefix_file_system : FilesystemBackend(root_dir=f"{settings.BASE_DIR}/doc")

                }
            )
        agent = create_deep_agent(
            models=models,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=checkpointer,
            store=store,
            skills=[f"{settings.BASE_DIR}/skills"],
            name="gemini-agent",
            debug=True,
            subagents=self.sub_agents,
            context_schema=Context,
            backend= make_backend,
            interrupt_on={
                "write_file": True,  # Default: approve, edit, reject
                "read_file": False,  # No interrupts needed
                "edit_file": True    # Default: approve, edit, reject
            },
            # middleware=[
            #     SummarizationMiddleware(
            #         max_tokens_before_summary=self.max_tokens_before_summary,
            #         model=llm_ollama_gpt,
            #     ),
            #     ModelCallLimitMiddleware(
            #         run_limit=5, thread_limit=100, exit_behavior="end"
            #     ),
            #     ToolCallLimitMiddleware(
            #         run_limit=10, thread_limit=10, exit_behavior="end"
            #     ),
            #     PIIMiddleware(
            #         "email",
            #         strategy="redact",
            #         apply_to_input=True,
            #         apply_to_output=True,
            #         apply_to_tool_results=True,
            #     ),
            #     PIIMiddleware("credit_card", strategy="block"),
            #     PIIMiddleware("ip", strategy="hash"),
            #     # PIIMiddleware("url", strategy="redact", apply_to_output=True),
            #     TodoListMiddleware(),
            #     # build_shell_middleware(),
            #     HumanInTheLoopMiddleware(interrupt_on=self.interrupt_on_tool),
            #     # ModelFallbackMiddleware(llm_ollama_kimi.bind_tools([]))
            #     # LLMToolSelectorMiddleware(model = llm_gemini, max_tools=5, always_include=["call_external_agent"]),
            # ],
        )
        print("Type của agent: ",type(agent))


        return agent

    async def run(self, user_input: str, context_id: str):
        """
        context_id = conversation_id
        """
        try:
            config = {
                "configurable": {
                    "thread_id": context_id,
                },
                "recursion_limit": self.recursion_limit,
            }

            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]}, config=config
            )

            # result["messages"] là toàn bộ lịch sử
            return result["messages"][-1].content
        except Exception as e:
            log.error(f"Lỗi khi chạy agent: {e}  {traceback.format_exc()}")
            return f"Lỗi khi chạy agent: {e}"

    async def run_astream(self, context_id: str, user_id:str =None, user_input_text: str = None, user_input_photo: str  = None):
        config = {
            "configurable": {"thread_id": context_id},
            "recursion_limit": self.recursion_limit,
        }

        content: list[dict] = []

        if user_input_text:
            content.append(
                {
                    "type": "text",
                    "text": user_input_text ,
                }
        
            )
        if user_input_photo:
           
           content.append(
                {
                    "type": "text",
                    "text": f"Miêu tả bức ảnh này: {user_input_photo}",
                }
    
        )

        if not content:
            raise ValueError("run_astream requires at least text or photo input")

        input_payload = {"messages": [HumanMessage(content=content)]}
        final_state = None
        try:
            while True:
                interrupted = False

                async for mode, payload in self.agent.astream(
                    input_payload,
                    config=config,
                    stream_mode=["values", "updates", "messages"],
                    context={"user_id": user_id} if user_id else None
                ):
                    # giữ state cuối
                    if mode == "values":
                        final_state = payload

                    # ===== INTERRUPT =====
                    if "__interrupt__" in payload:
                        interrupted = True
                        interrupt_event = payload["__interrupt__"][0]
                        hitl_request = interrupt_event.value
                        decisions = Command(
                            resume={
                                "decisions": await process_mess_interrupt(
                                    hitl_request=hitl_request
                                )
                            }
                        )
                        input_payload = decisions
                        break

                if not interrupted:
                    break
        except GraphRecursionError as e:
            log.exception("LangGraph recursion overflow")
            yield {
                "type": "error",
                "message": "Agent bị lặp vòng suy luận. Vui lòng thử lại."
            }

        except Exception as e:
            log.exception("Unhandled agent exception")
            yield {
                "type": "error",
                "message": "Hệ thống gặp lỗi nội bộ."
            }
       
                

        # ===== FINAL ANSWER =====
        if final_state:
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage):
                    yield msg.content
                    return

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
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
from a2a.types import FileWithBytes
from config.logger import log
import traceback
import base64
from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware import (SummarizationMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware, ToolCallLimitMiddleware,
                                         PIIMiddleware, TodoListMiddleware, LLMToolSelectorMiddleware, ShellToolMiddleware)
from middleware_custom import MiddlewareCustom
from until.check_os_name import build_shell_middleware
# ===============================
# System Prompt
# ===============================

SYSTEM_PROMPT = """
Bạn là một trợ lý hữu ích và thông minh.
Bạn có khả năng trả lời các câu hỏi trực tiếp.
Bạn có quyền truy cập vào một mạng lưới các chuyên gia (Agent khác).
Hãy sử dụng công cụ 'call_external_agent' để nhờ họ giúp đỡ khi câu hỏi nằm ngoài khả năng hoặc cần chuyên môn sâu.
"""

class DispatcherInput(BaseModel):
    agent_name: str = Field(description="Tên chính xác của agent cần gọi (lấy từ danh sách mô tả)")
    query: str = Field(description="Nội dung câu hỏi hoặc yêu cầu cần gửi tới agent đó")

    extra_data: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Dữ liệu cấu trúc JSON bổ sung nếu cần (ví dụ: thông tin user, params config)."
    )
    file_path: Optional[str] = Field(
        default=None, 
        description="Đường dẫn file (local path) hoặc File ID nếu câu hỏi yêu cầu xử lý file."
    )


class AgentCustom:
    def __init__(self, tools=None, system_prompt : str = SYSTEM_PROMPT, index_elastic: str = "langgraph_checkpoints", max_tokens_before_summary: int = 2000):
        self.system_prompt = system_prompt
        self.index_elastic = index_elastic
        self.tools = tools if tools else []
        self.agent_registry = {}
        self.agent = None
        self.max_tokens_before_summary = max_tokens_before_summary
    @classmethod
    async def create(cls, access_agent_urls: List[str] = [], **kwargs):
        self = cls(**kwargs)
      
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
              
                client, httpx_client, public_card, private_card = await create_client_for_agent(base_url=base_url, auth_token="BerearerTokenExample")

                if public_card.supports_authenticated_extended_card:
                    private_name = private_card.name
                  
                    self.agent_registry[private_name] = {
                        "card": private_card,
                        "client": client,
                        "url": private_card.url,
                        "scope": "private",
                    }

                public_name = public_card.name

                
                self.agent_registry[public_name] = {
                        "card": public_card,
                        "client": client,
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
        
        
        async def call_agent_impl(agent_name: str, query: str, extra_data: Optional[dict] = None, 
            file_path: Optional[str] = None, config: Annotated[RunnableConfig, InjectedToolArg] = None,
           
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

            parts = [TextPart(text=query)]
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
                            bytes= base64_bytes,
                            mime_type=mime_type,
                            name = os.path.basename(file_path)
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
                parts= parts
            )
            
            print(f"Đang gọi {agent_name} tại {agent_info['url']}...")
            final_result = None
            try:
                # --- VÒNG LẶP HỨNG DỮ LIỆU TỪ GENERATOR ---
                async for chunk_text in send_to_server_agent(client=agent_client, message=message):
                    
                    if chunk_text:
 
                        print("====Chunk Text",chunk_text, end="\n\n", flush=True)
                        if chunk_text.get("final") == True:
                            final_result = chunk_text.get("text")
                            break

                print("Final resuldt huhu",final_result, end="\n\n", flush=True)
                return final_result if final_result else "Agent đã chạy xong nhưng không trả về nội dung text nào."

            except Exception as e:
                return f"Lỗi khi gọi {agent_name}: {str(e)}"

        # 3. Tạo Tool Object với mô tả động
        return StructuredTool.from_function(
            func=None,
            coroutine=call_agent_impl,
            name="call_external_agent",
            description=f"""
            Sử dụng công cụ này để kết nối và gửi yêu cầu tới các Agent chuyên gia khác.
            Dựa vào danh sách dưới đây để chọn 'agent_name' phù hợp nhất với yêu cầu của người dùng.
            
            DANH SÁCH AGENT KHẢ DỤNG:
            {agents_desc_str}
            """,
            args_schema=DispatcherInput # Validate input đầu vào
        )
    
    def gen_agent(self)-> CompiledStateGraph :
        
        llm_gemini = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash",
            temperature=0.2,
            google_api_key=settings.GOOGLE_A2A_API_KEY,
        )
        llm_openai = ChatOpenAI(
            model_name="gpt-oss:latest",
            temperature=0.2,
            openai_api_key=settings.OPENAI_A2A_API_KEY,
            openai_api_base="http://localhost:11434/v1",
        )


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
                                        "blob": {"type": "text", "index": False}
                                    }
                                },
                                "metadata": {
                                    "properties": {
                                        "type": {"type": "keyword"},
                                        "blob": {"type": "text", "index": False}
                                    }
                                },
                                "writes": {
                                    "properties": {
                                        "type": {"type": "keyword"},
                                        "blob": {"type": "text", "index": False}
                                    }
                                },
                                
                                # Các trường cho put_writes
                                "task_id": {"type": "keyword"},
                                "task_path": {"type": "keyword"}
                            }
                        }
                    }
                )

        except Exception as e:
            raise ValueError(f"Elasticsearch connection error: {e}")

        # # Memory cho mỗi thread (mỗi context_id)
        # checkpointer = MemorySaver()

        checkpointer = ElasticsearchCheckpointSaver(
            es=es,
            index=self.index_elastic
        )   

        agent = create_agent(
            model=llm_openai,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=checkpointer,
            name="gemini-agent",
            debug=True,
            middleware=[SummarizationMiddleware(max_tokens_before_summary=self.max_tokens_before_summary, model=llm_gemini), 
                        ModelCallLimitMiddleware(run_limit= 5, thread_limit= 100, exit_behavior="error"),
                        ToolCallLimitMiddleware(run_limit=10, thread_limit= 10, exit_behavior= "error"),
                        PIIMiddleware("email", strategy="redact", apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
                        PIIMiddleware("credit_card", strategy="block"),
                        PIIMiddleware("ip", strategy="hash"),
                        # PIIMiddleware("url", strategy="redact", apply_to_output=True),
                        TodoListMiddleware(),
                        # LLMToolSelectorMiddleware(model = llm_gemini, max_tools=5, always_include=["call_external_agent"]),
                        build_shell_middleware(),
                        # HumanInTheLoopMiddleware(
                        #     interrupt_on={
                        #          "shell": True,
                        #     }
                        # ),
                        ]
        )
     

        return agent

    async def run(self, user_input: str, context_id: str):
        """
        context_id = conversation_id
        """
        try:
        

            result = await self.agent.ainvoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": context_id   # LangGraph memory key
                    }
                }
            )

            # result["messages"] là toàn bộ lịch sử
            return result["messages"][-1].content
        except Exception as e:
            log.error(f"Lỗi khi chạy agent: {e}  {traceback.format_exc()}")
            return f"Lỗi khi chạy agent: {e}"

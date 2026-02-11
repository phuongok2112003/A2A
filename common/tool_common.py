import subprocess
from langchain.tools import tool, ToolRuntime
from schemas.base import RunShellArgs, SaveMemoryArgs, LongMemory
from langgraph.store.base import PutOp, SearchOp
import uuid
from memory.memory_store import PineconeMemoryStore
from typing import Literal, Annotated, TypedDict
from datetime import datetime
from tavily import TavilyClient
from config.settings import settings
from PIL import Image
import base64
from io import BytesIO
import requests
from pathlib import Path
from langchain_core.messages import HumanMessage
from common.export_models_llm import ModelsLLM
import os, json
from langchain_core.tools import InjectedToolArg
@tool(args_schema=RunShellArgs)
def run_shell(command: str, timeout: int = 30) -> dict:
    """
    Execute a shell command and return stdout/stderr.

    Use for:
    - git commands
    - pip / python
    - system inspection
    The output is JSON with status and execution metadata.
    """
    if not command or not command.strip():
        return {"status": "error", "message": "Empty command"}

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        print("STDOUT:", stdout)
        print("STDERR:", stderr)

        success = completed.returncode == 0

        return {
                "status": "success" if success else "error",
                "command": command,
                "returncode": completed.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "objective_completed": success
                and command.startswith("git clone"),
            }
        

    except subprocess.TimeoutExpired:
        return {
                "status": "timeout",
                "command": command,
            }
        

    except Exception as e:
        return {
                "status": "exception",
                "command": command,
                "error": str(e),
            }
        

# @tool(
#     args_schema=SaveMemoryArgs,
#     description="Tự động lưu thông tin quan trọng của người dùng hoặc phiên làm việc vào long-term memory store nếu bạn đánh giá nó là thông "
#     "tin cần thiết để lưu (Sở thích, Profile) hoặc sự kiện đáng nhớ."
#     "Những thông tin này thường sẽ phải có nội dung xoay quanh người dùng giải sử như: các thông tin cơ bản về người dùng, thói quen, những chủ để quan tâm ...",
# )
# async def save_memory(
#     runtime: ToolRuntime,
#     text: str,
#     namespace: str = "general",  # Namespace con (vd: user_profile, work)
#     category: Literal["semantic", "episodic"] = "semantic",
#     tags: list[str] = [],
#     metadata: dict | None = None,
# ):
#     """
#     Save important long-term memory.
#     """
#     store: PineconeMemoryStore = runtime.store
#     user_id = runtime.context.user_id  # ID người dùng (vd: u-123)

#     # 1. Tạo ID duy nhất cho ký ức này (QUAN TRỌNG)
#     # Nếu dùng user_id làm key, ký ức mới sẽ đè ký ức cũ -> Mất dữ liệu.
#     memory_id = str(uuid.uuid4())

#     # 2. Xây dựng Metadata
#     final_metadata = metadata or {}
#     final_metadata.update(
#         {
#             "category": category,
#             "tags": tags,
#             "created_at": datetime.now().isoformat(),
#             "sub_namespace": namespace,  # Lưu tên namespace con vào metadata để tiện lọc
#         }
#     )

#     value = {"text": text, "metadata": final_metadata}

#     await store.abatch([PutOp(namespace=(user_id,), key=memory_id, value=value)])

#     return {"status": "saved", "id": memory_id, "category": category}


# @tool(
#     description="Tự động truy xuất ký ức dài hạn nếu bạn nghĩ nó là cần thiết. Dùng khi cần nhớ lại thông tin user, thói quen hoặc sự kiện trong quá khứ để trả lời tốt hơn.",
#     args_schema=LongMemory,
# )
# async def get_long_memory(
#     runtime: ToolRuntime,
#     query: str,
#     category: Literal["all", "semantic", "episodic"] = "all",
#     limit: int = 5,
# )-> dict:
#     """
#     Search long-term memory.
#     """
#     user_id = runtime.context.user_id
#     store: PineconeMemoryStore = runtime.store
#     print(
#         f"++++++++++++++++++chay vafo get long memroy roio ne: {query}+++++++++{category}+++++++++++++++++++++++++++++"
#     )

#     # 1. Namespace gốc cần tìm (phải khớp với lúc save)
#     namespace_path = (user_id,)

#     # 2. Tạo bộ lọc (Filter)
#     filter_dict = {}
#     if category != "all":
#         filter_dict["category"] = category

#     # Ví dụ: Nếu muốn tìm tag cụ thể, có thể mở rộng thêm logic ở đây
#     # if "python" in query.lower(): filter_dict["tags"] = {"$in": ["python"]}

#     # 3. Search
#     # results = await store.asearch(
#     #     namespace_prefix=namespace_path,
#     #     query=query,
#     #     filter=filter_dict if filter_dict else None,
#     #     limit=limit,
#     # )
#     results = await store.abatch(
#         [
#             SearchOp(
#                 namespace_prefix=namespace_path,
#                 query=query,
#                 filter=filter_dict if filter_dict else None,
#                 limit=limit,
#             )
#         ]
#     )

#     if not results or not results[0]:
#         return {
#             "memories": [],
#             "raw": [],
#         }

#     search_items = results[0]

#     formatted_memories: list[str] = []
#     raw_items: list[dict] = []

#     for item in search_items:
#         val = item.value if isinstance(item.value, dict) else {}
#         text = val.get("text", "")
#         meta = val.get("metadata", {})

#         entry = (
#             f"- [{meta.get('created_at','N/A')}] "
#             f"[{meta.get('category','INFO').upper()}] "
#             f"{text} "
#             f"(Tags: {meta.get('tags', [])})"
#         )

#         formatted_memories.append(entry)

#         raw_items.append(
#             {
#                 "text": text,
#                 "metadata": meta,
#                 "score": item.score,
#                 "key": item.key,
#                 "namespace": item.namespace,
#             }
#         )
   
#     print(f"raw {raw_items} \n formatted_memories: {formatted_memories} ")
#     return {
#         "memories": formatted_memories,
#         "raw": raw_items,
#     }

@tool(description="Run a web search")
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

@tool
async def load_image(
    source: Annotated[
        str,
        "Có thể là: http URL, https URL, hoặc đường dẫn file local (từ filesystem của agent)"
    ],
    detail: Literal["low", "high", "auto"] = "auto"
) -> str:
    """
    Load và encode ảnh thành base64 để multimodal model sử dụng.
    Trả về string base64 đã sẵn sàng cho message content.
    """

    print("Chạy vào load image")
    try:
        if source.startswith(("http://", "https://")):
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            img_data = response.content
        else:
            # Giả sử DeepAgents có filesystem → đọc từ path ảo
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(f"Không tìm thấy file: {source}")
            img_data = path.read_bytes()

        # Optional: resize để tiết kiệm token nếu cần
        img = Image.open(BytesIO(img_data))
        if img.size[0] > 1344 or img.size[1] > 1344:  # ví dụ giới hạn
            img.thumbnail((1344, 1344))
            buffer = BytesIO()
            img.save(buffer, format=img.format or "PNG")
            img_data = buffer.getvalue()

        b64 = base64.b64encode(img_data).decode("utf-8")
        mime = f"image/{img.format.lower() if img.format else 'jpeg'}"

        print("Nhay vao day roi")

        msg = HumanMessage(
            content=[
                {"type": "text", "text": "Ảnh này có gì?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}"
                    },
                },
            ]
        )
        result = await ModelsLLM.llm_ollama_kimi.ainvoke([msg])
        return f"Bức ảnh miêu tả {result.content} " 

    except Exception as e:
        return f"Lỗi khi load ảnh: {str(e)}. Vui lòng kiểm tra URL/path."

@tool(description="Đây là tool lấy state hiện tại của graph")
def get_state(
    runtime: Annotated[ToolRuntime, InjectedToolArg],
):
    state = runtime.state
    print("STATE keys:", list(state.keys()))
    return list(state.keys())


tools = [ run_shell,get_state]  ### Attach list tool for agent
interrupt_on_tool = [
    run_shell
]  ### Attach list tool for agent to interruput when call tool

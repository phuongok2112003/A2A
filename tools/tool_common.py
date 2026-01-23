import subprocess
from langchain.tools import tool, ToolRuntime
from schemas.base import RunShellArgs, SaveMemoryArgs, LongMemory
from langgraph.store.base import PutOp, SearchOp
import uuid
from memory.memory_store import PineconeMemoryStore
from typing import Literal
from datetime import datetime


@tool(args_schema=RunShellArgs)
def run_shell(command: str, timeout: int = 30) -> str:
    """
    Execute a shell command and return stdout/stderr.

    Use for:
    - git commands
    - ls / dir
    - pip / python
    - system inspection
    """
    if not command or not command.strip():
        return "Empty command"

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = completed.stdout.strip()
        error = completed.stderr.strip()

        if completed.returncode != 0:
            return f"[ERROR]\n{error or output}"

        return output or "[OK] Command executed with no output"

    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Command execution exceeded limit"

    except Exception as e:
        return f"[EXCEPTION] {e}"


@tool(
    args_schema=SaveMemoryArgs,
    description="Tự động lưu thông tin quan trọng của người dùng hoặc phiên làm việc vào long-term memory store nếu bạn đánh giá nó là thông "
    "tin cần thiết để lưu (Sở thích, Profile) hoặc sự kiện đáng nhớ."
    "Những thông tin này thường sẽ phải có nội dung xoay quanh người dùng giải sử như: các thông tin cơ bản về người dùng, thói quen, những chủ để quan tâm ...",
)
async def save_memory(
    runtime: ToolRuntime,
    text: str,
    namespace: str = "general",  # Namespace con (vd: user_profile, work)
    category: Literal["semantic", "episodic"] = "semantic",
    tags: list[str] = [],
    metadata: dict | None = None,
):
    """
    Save important long-term memory.
    """
    store: PineconeMemoryStore = runtime.store
    user_id = runtime.context.user_id  # ID người dùng (vd: u-123)

    # 1. Tạo ID duy nhất cho ký ức này (QUAN TRỌNG)
    # Nếu dùng user_id làm key, ký ức mới sẽ đè ký ức cũ -> Mất dữ liệu.
    memory_id = str(uuid.uuid4())

    # 2. Xây dựng Metadata
    final_metadata = metadata or {}
    final_metadata.update(
        {
            "category": category,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "sub_namespace": namespace,  # Lưu tên namespace con vào metadata để tiện lọc
        }
    )

    value = {"text": text, "metadata": final_metadata}

    await store.abatch([PutOp(namespace=(user_id,), key=memory_id, value=value)])

    return {"status": "saved", "id": memory_id, "category": category}


@tool(
    description="Tự động truy xuất ký ức dài hạn nếu bạn nghĩ nó là cần thiết. Dùng khi cần nhớ lại thông tin user, thói quen hoặc sự kiện trong quá khứ để trả lời tốt hơn.",
    args_schema=LongMemory,
)
async def get_long_memory(
    runtime: ToolRuntime,
    query: str,
    category: Literal["all", "semantic", "episodic"] = "all",
    limit: int = 5,
):
    """
    Search long-term memory.
    """
    user_id = runtime.context.user_id
    store: PineconeMemoryStore = runtime.store
    print(
        f"++++++++++++++++++chay vafo get long memroy roio nef {query}+++++++++{category}+++++++++++++++++++++++++++++"
    )

    # 1. Namespace gốc cần tìm (phải khớp với lúc save)
    namespace_path = (user_id,)

    # 2. Tạo bộ lọc (Filter)
    filter_dict = {}
    if category != "all":
        filter_dict["category"] = category

    # Ví dụ: Nếu muốn tìm tag cụ thể, có thể mở rộng thêm logic ở đây
    # if "python" in query.lower(): filter_dict["tags"] = {"$in": ["python"]}

    # 3. Search
    # results = await store.asearch(
    #     namespace_prefix=namespace_path,
    #     query=query,
    #     filter=filter_dict if filter_dict else None,
    #     limit=limit,
    # )
    results = await store.abatch(
        [
            SearchOp(
                namespace_prefix=namespace_path,
                query=query,
                filter=filter_dict if filter_dict else None,
                limit=limit,
            )
        ]
    )

    if not results:
        return "Không tìm thấy ký ức nào liên quan."

    # 4. Format
    formatted_memories = []
    for item in results:
        content = item.value.get("text", "")
        # Vì Pinecone integrated inference đôi khi trả về text nằm ngoài metadata hoặc trong metadata
        # Store._search đã xử lý việc lấy metadata ra value.

        meta = item.value  # Store trả về item.value chính là metadata
        created_at = meta.get("created_at", "N/A")
        cat = meta.get("category", "INFO")
        tags = meta.get("tags", [])

        entry = f"- [{created_at}] [{cat.upper()}] {content} (Tags: {tags})"
        formatted_memories.append(entry)

    return "\n".join(formatted_memories)


tools = [save_memory, run_shell, get_long_memory]  ### Attach list tool for agent
interrupt_on_tool = [
    run_shell
]  ### Attach list tool for agent to interruput when call tool

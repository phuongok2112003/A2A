import subprocess
from langchain.tools import tool, ToolRuntime
from schemas.base import RunShellArgs, SaveMemoryArgs
from langgraph.store.base import PutOp
import uuid
from memory.memory_store import PineconeMemoryStore
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

@tool(args_schema=SaveMemoryArgs, description="Lưu thông tin quan trọng của người dùng hoặc phiên làm việc vào long-term memory store.")
async def save_memory(runtime: ToolRuntime,namespace: str, text: str, metadata: dict | None = None):
    """
    Save important long-term memory.
    """
    key = str(uuid.uuid4())
    store : PineconeMemoryStore = runtime.store

    value = {
        "text": text,
        "metadata": metadata or {}
    }

    await store.abatch([
        PutOp(
            namespace=("memory", namespace),
            key=key,
            value=value
        )
    ])

    return {"status": "saved", "id": key}
tools = [run_shell,save_memory]

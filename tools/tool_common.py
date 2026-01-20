import subprocess
from langchain_core.tools import tool


@tool
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

tools = [run_shell]

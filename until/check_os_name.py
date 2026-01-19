import platform
from langchain.agents.middleware import ShellToolMiddleware

def build_shell_middleware()->ShellToolMiddleware:
    os_name = platform.system().lower()

    if "windows" in os_name:
        return ShellToolMiddleware(
            shell_command=("powershell", "-NoLogo"),
            tool_description = (
                "Execute PowerShell commands in a persistent Windows shell session. "
                "Supports developer commands such as git clone, git pull, pip, python, dir, Get-Content, Remove-Item, etc. "
                "Use this tool whenever repository or system operations are needed."
            ),
        )

    else:  # Linux / Mac
        return ShellToolMiddleware(
            shell_command=("/bin/bash",),
            tool_description = (
            "Execute PowerShell commands in a persistent Windows shell session. "
            "Supports developer commands such as git clone, git pull, pip, python, dir, Get-Content, Remove-Item, etc. "
            "Use this tool whenever repository or system operations are needed."
            ),
        )

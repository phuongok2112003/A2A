import subprocess
import json, os
def run_shell(command: str, timeout: int = 30) -> str:
    if not command or not command.strip():
        return json.dumps({"status": "error", "message": "Empty command"})

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

        return json.dumps(
            {
                "status": "success" if success else "error",
                "command": command,
                "returncode": completed.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "objective_completed": success
                and command.startswith("git clone"),
            }
        )

    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "status": "timeout",
                "command": command,
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "status": "exception",
                "command": command,
                "error": str(e),
            }
        )

print(run_shell("git clone https://github.com/phuongok2112003/tiktok-ui.git"))
import asyncio
import os
import sys
import io
from pprint import pprint
from pathlib import Path

# Thêm project root vào sys.path để import absolute hoạt động
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from common.export_models_llm import ModelsLLM
from common.tool_common import run_shell

# Fix encoding trên Windows để hỗ trợ Unicode (tiếng Việt, v.v.)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ---------- Đường dẫn tuyệt đối đến thư mục skills ----------
SKILLS_DIR = str(PROJECT_ROOT / "skills")

async def main():
    """
    Agent tra cứu thông tin trên internet bằng skill 'agent-browser'.
    
    Cách hoạt động:
    - deepagents sẽ tự đọc SKILL.md trong thư mục skills/ và inject vào system prompt
    - Agent sẽ biết cách dùng agent-browser CLI thông qua progressive disclosure
    - Tool run_shell cho phép agent thực thi lệnh agent-browser
    """

    # ---------- Checkpointer (bắt buộc cho multi-turn) ----------
    checkpointer = MemorySaver()

    # ---------- Backend: cho phép agent đọc file skill ----------
    backend = FilesystemBackend(root_dir=SKILLS_DIR)

    # ---------- System prompt ngắn gọn ----------
    # deepagents sẽ tự thêm hướng dẫn skill vào prompt qua SkillsMiddleware
    # Chỉ cần bổ sung context riêng cho use-case của bạn
    system_prompt = """
Bạn là một AI Agent chuyên tra cứu thông tin trên internet.

## Nguyên tắc quan trọng

- Sử dụng skill "agent-browser" để điều khiển trình duyệt. Đọc kỹ SKILL.md trước khi bắt đầu.
- **Mọi lệnh agent-browser phải được thực thi qua tool `run_shell`**.
  Ví dụ: run_shell(command="agent-browser open https://google.com")
- Luôn tuân theo quy trình: open → wait → snapshot → interact → get text → close.
- Sau mỗi lần click hoặc điều hướng, phải snapshot lại để lấy refs mới.
- Luôn đóng session khi hoàn thành: run_shell(command="agent-browser close")


## Định dạng kết quả

Trình bày kết quả theo cấu trúc:
- **Tiêu đề bài viết**
- **Nguồn & ngày đăng**
- **Tóm tắt nội dung** (2-4 câu)
- **Link gốc**

Trả lời bằng tiếng Việt, ngắn gọn và súc tích.
"""

    # ---------- Khởi tạo Agent ----------
    # skills=[SKILLS_DIR] → deepagents sẽ quét thư mục, tìm các SKILL.md
    #   và inject metadata vào system prompt (progressive disclosure)
    # backend → cho phép agent đọc nội dung SKILL.md, references, templates
    # tools=[run_shell] → agent dùng run_shell để thực thi lệnh agent-browser
    agent = create_deep_agent(
        model=ModelsLLM.llm_ollama_nemotron,
        skills=[SKILLS_DIR],          # ✅ Đường dẫn tuyệt đối đến thư mục skills
        backend=backend,              # ✅ Backend để đọc file trong skills
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        debug=True,
        tools=[run_shell],            # ✅ Tool để agent thực thi shell commands
    )

    # ---------- Thông báo trạng thái ----------
    print("✅ Agent đã được tạo thành công.")
    print(f"📂 Skills directory: {SKILLS_DIR}")
    print(f"� Tool: run_shell (cho agent-browser CLI)")
    print(f"🤖 Model: nemotron-3-super:cloud\n")

    # ---------- Tin nhắn từ người dùng ----------
    user_message = "Tin tức mới nhất về  AI ngày hôm nay?"

    # ---------- Stream và in kết quả ----------
    print("=" * 70)
    print("🚀 Bắt đầu chạy agent với skill agent-browser...")
    print("=" * 70 + "\n")

    try:
        async for event, data in agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=["values", "updates", "messages"],
            config={"configurable": {"thread_id": "browser-research-001"}}
        ):
            # In ra messages mới nhất
            if isinstance(data, dict) and "messages" in data:
                data["messages"][-1].pretty_print()
            elif hasattr(data, 'content'):
                # BaseMessage trực tiếp
                data.pretty_print()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        print("\nKiểm tra:")
        print("  1. Model LLM đã khởi động (ollama serve)")
        print("  2. agent-browser đã cài (agent-browser --version)")
        print(f"  3. Thư mục skills tồn tại: {SKILLS_DIR}")
        print(f"  4. SKILL.md tồn tại: {SKILLS_DIR}/agent-browser/SKILL.md")

    print("\n" + "=" * 70)
    print("✅ Hoàn thành!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

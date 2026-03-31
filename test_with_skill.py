import asyncio
import os
from pprint import pprint
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import settings  # Giả sử settings.GOOGLE_A2A_API_KEY
from common.export_models_llm import ModelsLLM
from common.tool_common import run_shell
import sys
import io
  
# Fix encoding trên Windows để hỗ trợ Unicode (tiếng Việt, v.v.)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def main():
    """
    Agent tra cứu thông tin về Mamba model từ IBM bằng cách sử dụng skill 'agent-browser'.
    """

    # ---------- Checkpointer (bắt buộc) ----------
    checkpointer = MemorySaver()

    # ---------- System prompt: rõ ràng, hướng dẫn sử dụng skill ----------
    system_prompt = """
Bạn là một AI Agent chuyên tra cứu thông tin trên internet, sử dụng công cụ `run_shell` để thực thi các lệnh `agent-browser` CLI điều khiển trình duyệt Chrome/Chromium tự động.

## Cách thực thi lệnh

**Mọi lệnh agent-browser đều phải được thực thi qua `run_shell` tool**, không gọi trực tiếp.

Ví dụ:
```python
run_shell("agent-browser open https://techcrunch.com")
run_shell("agent-browser wait --load networkidle")
run_shell("agent-browser snapshot -i")
run_shell("agent-browser get text body")
run_shell("agent-browser close")
```

## Quy trình làm việc chuẩn

Luôn tuân theo quy trình sau khi tra cứu thông tin:

1. **Mở trang web**: `run_shell("agent-browser open <url>")`
2. **Chờ tải xong**: `run_shell("agent-browser wait --load networkidle")`
3. **Lấy snapshot**: `run_shell("agent-browser snapshot -i")` → lấy refs như @e1, @e2...
4. **Tương tác**: Dùng refs để click, fill, scroll
5. **Trích xuất nội dung**: `run_shell("agent-browser get text body")`
6. **Re-snapshot** sau mỗi lần điều hướng trang
7. **Đóng session**: `run_shell("agent-browser close")`

## Nguyên tắc quan trọng

- **Refs (@e1, @e2...) bị vô hiệu sau mỗi lần trang thay đổi** — luôn snapshot lại sau khi click hoặc điều hướng.
- Dùng `agent-browser wait --load networkidle` sau khi mở trang chậm.
- Nếu cần tìm kiếm, ưu tiên dùng Google (`https://www.google.com`) hoặc các trang tin tức uy tín.
- Trích xuất nội dung bằng `agent-browser get text @eN` hoặc `agent-browser get text body`.
- Luôn đóng session sau khi hoàn thành: `run_shell("agent-browser close")`.

## Nguồn tin tức công nghệ gợi ý

Khi tra cứu tin tức công nghệ, ưu tiên các nguồn:
- https://techcrunch.com
- https://www.theverge.com
- https://vnexpress.net/khoa-hoc-cong-nghe (tiếng Việt)
- https://news.ycombinator.com
- https://www.google.com/search?q=tin+tuc+cong+nghe+hom+nay

## Định dạng kết quả

Sau khi thu thập, trình bày kết quả theo cấu trúc:
- **Tiêu đề bài viết**
- **Nguồn & ngày đăng**
- **Tóm tắt nội dung** (2-4 câu)
- **Link gốc**

Trả lời bằng tiếng Việt, ngắn gọn và súc tích.
"""

    # ---------- Khởi tạo Agent với skill đã sửa đường dẫn ----------
    # 🔧 SỬA LỖI CHÍNH: Đường dẫn skill phải là tương đối từ thư mục đang chạy (D:\A2A)
    agent = create_deep_agent(
        model=ModelsLLM.llm_ollama_nemotron,  # Đảm bảo đây là model LLM hợp lệ (Ollama)
        skills=["D:/A2A/skills/agent-browser/"],   # ✅ ĐÃ SỬA: bỏ dấu '/' đầu → đường dẫn tương đối đúng
        # backend=FilesystemBackend(root_dir="./doc"),  # Lưu file kết quả vào ./doc
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        debug=True,
        tools=[run_shell],  # Cho phép chạy shell nếu cần (ví dụ: lưu file)
        
    )

    # ---------- Thông báo trạng thái ----------
    print("✅ Agent đã được tạo thành công.")
    print(f"📂 Skill được load từ: D:/A2A/skills/agent-browser/")
    print(f"💾 Kết quả sẽ được lưu vào: ./doc")
    print(f"🎯 Nhiệm vụ: Tra cứu thông tin Mamba model từ IBM\n")

    # ---------- Tin nhắn từ người dùng ----------
    user_message = """Tôi muốn biết tình hình công nghệ ngày hôm nay, hãy lên trên internet để tìm kiếm?"""

    # ---------- Stream và in kết quả ----------
    print("=" * 70)
    print("🚀 Bắt đầu chạy agent để tra cứu thông tin Mamba model từ IBM...")
    print("=" * 70 + "\n")

    try:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=["values", "updates", "messages"],
            config={"configurable": {"thread_id": "mamba-research-task-001"}}
        ):
            pprint(chunk)
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình chạy agent: {e}")
        print("Vui lòng kiểm tra:")
        print("  - Kết nối internet")
        print("  - Model LLM (ModelsLLM.llm_ollama_nemotron) đã được khởi động")
        print("  - Thư mục skills/agent-browser/ có tồn tại và đúng định dạng")
        print("  - Có quyền ghi vào thư mục ./doc")

    print("\n" + "=" * 70)
    print("✅ Hoàn thành tra cứu! Kết quả (nếu có) đã được lưu vào ./doc")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
